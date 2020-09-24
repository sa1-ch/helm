import datetime
import hashlib
import itertools
import json
import os
import os.path as op
from copy import deepcopy
from datetime import timedelta

import pandas as pd
import yaml
from airflow import DAG
from airflow.contrib.operators.kubernetes_pod_operator import KubernetesPodOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.utils.dates import days_ago
from airflow.utils.helpers import chain

# These args will get passed on to each operator
# You can override them on a per-task basis during operator initialization
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": days_ago(0),
    "email": ["airflow@example.com"],
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 6,
    "retry_delay": timedelta(minutes=5),
}

dag = DAG(
    "{{ dag_id }}",
    default_args=default_args,
    description="Timeseries Forecasting : Backtest DAG",
)


def _create_job_name(job_cfg):
    """Create run_name, registered_model_name for a job"""
    registered_model_name = job_cfg["name"] + "--" + job_cfg["dataset_name"]
    return registered_model_name


def _get_last_train_date(date, offset):
    """For a given date obtain the last train date that comes prior to
       test start date with the offset(in days) provided
    """
    d = pd.to_datetime(date)
    prevd = d - pd.Timedelta(days=offset + 1)
    return prevd


def _split_exp_in_jobs(cfg):
    """split the experiment into multiple jobs of full training based on
       number of weeks in the forecast period and offset.
    """
    fcst_start = pd.to_datetime(cfg["forecast_start_date"])
    fcst_end = pd.to_datetime(cfg["forecast_end_date"])
    offset = cfg["run_params"]["offset"]

    daysdiff = (fcst_end - fcst_start).days

    if daysdiff <= 0:
        raise ValueError("forecast_end_date should be greater than forecast_start_date")

    num_jobs = (daysdiff // cfg["training_frequency"]["full"]) + 1
    if cfg["training_frequency"]["incremental"] > 0:
        num_sub_jobs = (
            (cfg["training_frequency"]["full"] - 1)
            // cfg["training_frequency"]["incremental"]
        ) + 1
    else:
        num_sub_jobs = 1

    jobs = []
    for _ in range(num_jobs):
        temp = []
        for j in range(num_sub_jobs):
            if j == 0:
                tst = fcst_start + pd.Timedelta(
                    days=_ * cfg["training_frequency"]["full"]
                )
                ted = tst + pd.Timedelta(days=cfg["training_frequency"]["full"] - 1)
                ltd = _get_last_train_date(tst, offset)
                model_date = ltd + pd.Timedelta(days=1)
                temp.append(
                    {
                        "test_end_date": ted,
                        "last_train_date": ltd,
                        "model_date": model_date,
                        "training": "full",
                    }
                )
            else:
                tst = tst + pd.Timedelta(days=cfg["training_frequency"]["incremental"])
                ted = ted + pd.Timedelta(days=cfg["training_frequency"]["incremental"])
                ltd = _get_last_train_date(tst, offset)
                model_date = ltd + pd.Timedelta(days=1)
                temp.append(
                    {
                        "test_end_date": ted,
                        "last_train_date": ltd,
                        "model_date": model_date,
                        "training": "incremental",
                    }
                )
        jobs.append(temp)
    return jobs


def create_jobs(cfg):
    """Create relevant jobs to be run in parallel using the exp_config.
       Job represents a part of an experiment that can be run in parallel.
       Ex -  1 week's run in a backtest etc.,
    """
    jobsplits = _split_exp_in_jobs(cfg)

    jobs = []
    for i in jobsplits:
        subjobs = []
        for j in i:
            cp = deepcopy(cfg)
            cp["run_params"].update(j)
            registered_model_name = _create_job_name(cp)
            cp["run_params"]["registered_model_name"] = registered_model_name
            cp["run_params"]["name"] = registered_model_name
            if (cp["run_params"]["training"] == "incremental") and (
                "inc_epochs" in cp["run_params"]["hyper_params"].keys()
            ):
                cp["run_params"]["hyper_params"].update(
                    {"epochs": cp["run_params"]["hyper_params"]["inc_epochs"]}
                )

            if "inc_epochs" in cp["run_params"]["hyper_params"].keys():
                cp["run_params"]["hyper_params"].pop("inc_epochs")

            cp["model_date"] = cp["run_params"]["model_date"]

            subjobs.append(cp)
        jobs.append(subjobs)
    return jobs


def normalize_dict(dct):
    out = {}
    for k, v in dct.items():
        if isinstance(v, (datetime.date, pd.Timestamp)):
            v = v.isoformat()
        elif isinstance(v, dict):
            v = normalize_dict(v)
        out[k] = v
    return out


def get_parallel_process_ids(task):
    sliced_gen = [
        (i, i + task["run_params"]["evaluation"]["data_per_parallel_process"],)
        for i in range(
            0,
            task["run_params"]["evaluation"]["data_set_length"],
            task["run_params"]["evaluation"]["data_per_parallel_process"],
        )
    ]
    print(sliced_gen)
    return sliced_gen


def add_airflow_tasks_train_score(dag, iter_dag_id, job, cfg, run_spec_folder):
    train_tasks = []
    score_tasks = []

    run_spec_folder = op.abspath(run_spec_folder)
    cfg_file = op.join(run_spec_folder, "cfg.yml")
    with open(cfg_file, "w") as fp:
        yaml.dump(normalize_dict(cfg), fp)

    conf_input = json.dumps(normalize_dict(cfg))
    for task in job:
        if task["run_params"]["model_name"] == "ProphetPredictor":
            task_id = "{}-Dummy_MD_{}_FD_{}".format(
                task["run_params"]["training"],
                task["run_params"]["model_date"].strftime("%Y-%m-%d"),
                task["run_params"]["test_end_date"].strftime("%Y-%m-%d"),
            )
            train_task = DummyOperator(
                task_id=task_id + "_" + iter_dag_id.split("_")[-1], dag=dag
            )
        else:
            task_id = "{}-train_MD_{}_FD_{}".format(
                task["run_params"]["training"],
                task["run_params"]["model_date"].strftime("%Y-%m-%d"),
                task["run_params"]["test_end_date"].strftime("%Y-%m-%d"),
            )
            task_spec_file = op.join(run_spec_folder, task_id + ".yml")
            with open(task_spec_file, "w") as fp:
                yaml.dump(normalize_dict(task), fp)

            # create an airflow task for training the model
            train_task_input = json.dumps(normalize_dict(task))
            train_task = KubernetesPodOperator(
                in_cluster=True,
                task_id=task_id + "_" + iter_dag_id.split("_")[-1],
                name="train"
                + "_"
                + "{{ dag_id }}"[0:30]
                + "_"
                + iter_dag_id.split("_")[-1],
                namespace="ts-eks-ns",
                image="{{ ecr_image_uri }}",
                image_pull_policy="IfNotPresent",
                cmds=["/opt/conda/envs/ts-dev/bin/ts-fcast"],
                arguments=[
                    "-c",
                    conf_input,
                    "train-job",
                    "-i",
                    train_task_input,
                    "-dg",
                    iter_dag_id,
                ],
                resources={{train_task_resources}},
                service_account_name="s3-service-account",
                node_selectors={"nodegroup-name": "{{ train_task }}"},
                startup_timeout_seconds=7200,
                dag=dag,
            )

        sliced_gen = get_parallel_process_ids(task)
        child_score_task = []
        for iter_sliced_gen in sliced_gen:
            print(f"Starting task for data: {iter_sliced_gen}")
            iter_score_dag_id = (
                iter_dag_id
                + "_"
                + str(iter_sliced_gen[0])
                + "_"
                + str(iter_sliced_gen[1])
            )
            task["run_params"]["evaluation"][
                "start_index_per_scoring_task"
            ] = iter_sliced_gen[0]
            task["run_params"]["evaluation"][
                "end_index_per_scoring_task"
            ] = iter_sliced_gen[1]
            task["iter_score_dag_id"] = iter_score_dag_id

            task_id = "{}-score_MD_{}_FD_{}_{}_{}".format(
                task["run_params"]["training"],
                task["run_params"]["model_date"].strftime("%Y-%m-%d"),
                task["run_params"]["test_end_date"].strftime("%Y-%m-%d"),
                str(iter_sliced_gen[0]),
                str(iter_sliced_gen[1]),
            )
            task_spec_file = op.join(run_spec_folder, task_id + ".yml")
            with open(task_spec_file, "w") as fp:
                yaml.dump(normalize_dict(task), fp)

            # create an airflow task for scoring the model
            score_task_input = json.dumps(normalize_dict(task))
            iter_score_task = KubernetesPodOperator(
                in_cluster=True,
                task_id=task_id + "_" + iter_dag_id.split("_")[-1],
                name="score"
                + "_"
                + "{{ dag_id }}"[0:30]
                + "_"
                + iter_dag_id.split("_")[-1],
                namespace="ts-eks-ns",
                image="{{ ecr_image_uri }}",
                image_pull_policy="IfNotPresent",
                cmds=["/opt/conda/envs/ts-dev/bin/ts-fcast"],
                arguments=[
                    "-c",
                    conf_input,
                    "score-job",
                    "-i",
                    score_task_input,
                    "-dg",
                    iter_dag_id,
                ],
                resources={{score_task_resources}},
                service_account_name="s3-service-account",
                node_selectors={"nodegroup-name": "{{ score_task }}"},
                startup_timeout_seconds=7200,
                dag=dag,
            )
            child_score_task.append(iter_score_task)
            # chain(*child_score_task)

        task_id = "{}-merge_score_MD_{}_FD_{}".format(
            task["run_params"]["training"],
            task["run_params"]["model_date"].strftime("%Y-%m-%d"),
            task["run_params"]["test_end_date"].strftime("%Y-%m-%d"),
        )
        task_spec_file = op.join(run_spec_folder, task_id + ".yml")
        with open(task_spec_file, "w") as fp:
            yaml.dump(normalize_dict(task), fp)

        # create an airflow task for training the model
        merge_score_task_input = json.dumps(normalize_dict(task))
        conf_input = json.dumps(normalize_dict(cfg))
        merge_score_task = KubernetesPodOperator(
            in_cluster=True,
            task_id=task_id + "_" + iter_dag_id.split("_")[-1],
            name="merge_score"
            + "_"
            + "{{ dag_id }}"[0:30]
            + "_"
            + iter_dag_id.split("_")[-1],
            namespace="ts-eks-ns",
            image="{{ ecr_image_uri }}",
            image_pull_policy="IfNotPresent",
            cmds=["/opt/conda/envs/ts-dev/bin/ts-fcast"],
            arguments=[
                "-c",
                conf_input,
                "merge-score-run",
                "-i",
                merge_score_task_input,
                "-dg",
                iter_dag_id,
            ],
            resources={{score_merge_task_resources}},
            service_account_name="s3-service-account",
            node_selectors={"nodegroup-name": "{{ score_merge_task }}"},
            startup_timeout_seconds=7200,
            dag=dag,
        )

        train_task >> child_score_task
        child_score_task >> merge_score_task
        train_tasks.append(train_task)
        score_tasks.append(merge_score_task)

    chain(*train_tasks)
    return train_tasks[0], score_tasks[-1]


def get_config_hashvalue(job_cfg, creds):
    cfg_str = str(creds) + str(job_cfg)
    hash = hashlib.sha1(str.encode(cfg_str)).hexdigest()
    hash = int(hash, 16) % (10 ** 8)
    return f"{str(hash)}"


def run_hyper_cli(cfg, creds, dag_id):
    param = cfg["run_params"]["hyper_params"]
    vals = {i: j for i, j in param.items() if type(j) == list}
    combinations = pd.DataFrame(
        list(itertools.product(*list(vals.values()))), columns=list(vals.keys())
    ).to_dict("records")

    job_com = []
    for i in range(len(combinations)):
        params = dict(cfg["run_params"]["hyper_params"])
        params.update(combinations[i])
        task = deepcopy(cfg)
        task["run_params"]["hyper_params"].update(params)
        job_com.append(task)

    if job_com:
        cfg = list(job_com)
    else:
        cfg = [cfg]
    return cfg


def create_sub_dags(dag, iter_dag_id, cfg, job_spec):
    jobs = create_jobs(job_spec)

    run_spec_folder = "/tmp/backtest_job_specs_{{ dag_id }}"
    os.makedirs(run_spec_folder, exist_ok=True)

    parent_task = KubernetesPodOperator(
        in_cluster=True,
        task_id="parent_task" + "_" + iter_dag_id.split("_")[-1],
        name="parent_task"
        + "_"
        + "{{ dag_id }}"[0:30]
        + "_"
        + iter_dag_id.split("_")[-1],
        namespace="ts-eks-ns",
        image="{{ ecr_image_uri }}",
        image_pull_policy="IfNotPresent",
        cmds=["/opt/conda/envs/ts-dev/bin/ts-fcast"],
        arguments=[
            "-c",
            json.dumps(normalize_dict(cfg)),
            "parent-run",
            "-i",
            json.dumps(normalize_dict(job_spec)),
            "-dg",
            iter_dag_id,
        ],
        resources={{parent_run_resources}},
        service_account_name="s3-service-account",
        node_selectors={"nodegroup-name": "{{ parent_run }}"},
        startup_timeout_seconds=7200,
        dag=dag,
    )

    merge_tasks = KubernetesPodOperator(
        in_cluster=True,
        task_id="merge_tasks" + "_" + iter_dag_id.split("_")[-1],
        name="merge_tasks"
        + "_"
        + "{{ dag_id }}"[0:30]
        + "_"
        + iter_dag_id.split("_")[-1],
        namespace="ts-eks-ns",
        image="{{ ecr_image_uri }}",
        image_pull_policy="IfNotPresent",
        cmds=["/opt/conda/envs/ts-dev/bin/ts-fcast"],
        arguments=[
            "-c",
            json.dumps(normalize_dict(cfg)),
            "merge-run",
            "-i",
            json.dumps(normalize_dict(job_spec)),
            "-dg",
            iter_dag_id,
        ],
        resources={{merge_run_resources}},
        service_account_name="s3-service-account",
        node_selectors={"nodegroup-name": "{{ merge_run }}"},
        startup_timeout_seconds=7200,
        dag=dag,
    )

    first_tasks_list = []
    last_tasks_list = []
    job_spec["run_params"]["fit_and_predict"]
    for job in jobs:
        first_task, last_task = add_airflow_tasks_train_score(
            dag, iter_dag_id, job, cfg, run_spec_folder,
        )
        first_tasks_list.append(first_task)
        last_tasks_list.append(last_task)

    parent_task >> first_tasks_list
    last_tasks_list >> merge_tasks


def main():
    cfg = yaml.safe_load("""{{ creds_config }}""")
    job_spec = yaml.safe_load("""{{ job_config }}""")

    job_spec_list = run_hyper_cli(job_spec, cfg, "{{ dag_id }}")

    for iter_job_cfg in job_spec_list:
        iter_dag_id = "{{ dag_id }}" + "_" + get_config_hashvalue(iter_job_cfg, None)
        print(f"Experiment-Dag-Id: {iter_dag_id}")

        create_sub_dags(dag, iter_dag_id, cfg, iter_job_cfg),


main()
