import itertools
import logging
import os.path as op
import time
from copy import deepcopy

import pandas as pd
import requests

from ts_forecast.core.utils.airflow import execute_jobs_airflow, get_uid_for_template
from ts_forecast.core.utils.io import dumpy_dict_as_yaml

_LOGGER = logging.getLogger(__name__)


def run_backtest_job_local(cred, job, dags_id, train_score):
    from ts_forecast.scripts.train_cli import run_training_job
    from ts_forecast.scripts.score_cli import run_scoring_job
    from ts_forecast.scripts.mlflow_cli import (
        parent_run_task_cli,
        merge_train_score_cli,
    )

    creds_config = str(cred)
    job_config = str(job)
    jobs = create_jobs(job)

    param = jobs[0][0]["run_params"]["hyper_params"]
    vals = {i: j for i, j in param.items() if type(j) == list}
    combinations = pd.DataFrame(
        list(itertools.product(*list(vals.values()))), columns=list(vals.keys())
    ).to_dict("records")

    hyperparameters = []
    if combinations:
        for comb in combinations:
            params = deepcopy(param)
            params.update(comb)
            hyperparameters.append(params)
    else:
        hyperparameters.append(param)

    for i, parameter in enumerate(hyperparameters):

        dag_id = f"{dags_id}_Hyper_{i}"
        dag_id = get_uid_for_template(dag_id, creds_config, job_config)
        parent_run_task_cli(job=job, creds=creds_config, dag_id=dag_id)

        for iter_job in jobs:
            for task in iter_job:
                task["run_params"]["hyper_params"].update(parameter)
                if train_score:
                    run_training_job(creds=cred, job=task, dag_id=dag_id)
                run_scoring_job(creds=cred, job=task, dag_id=dag_id)
        merge_train_score_cli(job=job, dag_id=dag_id)


def run_backtest_job_airflow(airflow_params):
    execute_jobs_airflow(**airflow_params)


def trigger_rest_job_request(url, json_data):
    _LOGGER.info(f"url : {url}, json_data: {json_data}")

    r = requests.post(url=url, json=json_data)
    _LOGGER.info("status_code: {}".format(r.status_code))
    if r.status_code == 200:
        res = r.json()
        _LOGGER.info(res)
        _LOGGER.info("Please notedown the request_uuid !")
        return res
    else:
        _LOGGER.error(r.text)


def get_rest_job_request_status(url, request_uuid):
    _LOGGER.info(f"url : {url}, request_uuid: {request_uuid}")

    url = url.format(request_uuid)
    r = requests.get(url=url)
    _LOGGER.info("status_code: {}".format(r.status_code))
    if r.status_code == 200:
        res = r.json()
        _LOGGER.info(res)
        return res
    else:
        _LOGGER.error(r.text)


def watch_rest_job_request_status(url, request_uuid, watch=False, poll_time=20):
    get_rest_job_request_status(url, request_uuid)

    if watch:
        while True:
            time.sleep(poll_time)
            get_rest_job_request_status(url=url, request_uuid=request_uuid)


def save_train_score_creds_tasks(creds_cfg, job_spec_cfg):
    jobs = create_jobs(job_spec_cfg)

    # Save job-spec-file
    for job in jobs:
        for task in job:
            for iter_task_name in ["train", "score"]:
                task_id = "{}-{}_MD_{}_FD_{}".format(
                    task["run_params"]["training"],
                    iter_task_name,
                    task["run_params"]["model_date"].strftime("%Y-%m-%d"),
                    task["run_params"]["test_end_date"].strftime("%Y-%m-%d"),
                )
                task_spec_file = op.join(task_id + ".yml")

                _LOGGER.info(f"Saving: {task_spec_file}")
                dumpy_dict_as_yaml(file_name=task_spec_file, dict_obj=task)

    # save creds file
    task_spec_file = op.join("cfg.yml")
    _LOGGER.info(f"Saving: {task_spec_file}")
    dumpy_dict_as_yaml(file_name=task_spec_file, dict_obj=creds_cfg)


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


def _create_job_name(job_cfg):
    """Create run_name, registered_model_name for a job"""
    registered_model_name = job_cfg["name"] + "--" + job_cfg["dataset_name"]
    return registered_model_name


def create_jobs(cfg):
    """Create relevant jobs to be run in parallel using the exp_config.
       Job represents a part of an experiment that can be run in parallel.
       Ex -  1 week's run in a backtest etc.,
    """
    jobsplits = _split_exp_in_jobs(cfg)
    # Fix This
    # if (cfg['run_params']['training'] == 'incremental') and (len(jobsplits)>1):
    #    raise warnings.warn("")

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
