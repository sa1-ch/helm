import copy
import getpass
import hashlib
import logging
import time
import s3fs
from pathlib import Path

import requests
import yaml
from jinja2 import Environment, FileSystemLoader

from ts_forecast.core.constants.eks import NODE_SELECTORS
from ts_forecast.core.dependencies.containers import Core, Gateways

# from argparse import Namespace
# import pandas as pd
# from tabulate import tabulate


_LOGGER = logging.getLogger(__name__)


def unpause_dag_via_rest(dag_id):
    airflow_uri = Core.config.credentials.airflow.remote_rest_eks_trigger_url()
    api_endpoint = f"{airflow_uri}api/experimental/dags/{dag_id}/paused/false"
    request = requests.get(url=api_endpoint)
    return request


def trigger_dag_via_rest(dag_id):
    airflow_uri = Core.config.credentials.airflow.remote_rest_eks_trigger_url()
    api_endpoint = f"{airflow_uri}api/experimental/dags/{dag_id}/dag_runs"
    request = requests.post(url=api_endpoint, data="{}")
    return request


def pause_dag_via_rest(dag_id):
    airflow_uri = Core.config.credentials.airflow.remote_rest_eks_trigger_url()
    api_endpoint = f"{airflow_uri}api/experimental/dags/{dag_id}/paused/true"
    request = requests.get(url=api_endpoint)
    return request


def get_user_id():
    user_id = getpass.getuser().replace(".", "_")
    return f"{user_id}"


def get_config_hashvalue(creds, job_cfg):
    user_id = get_user_id()
    cfg_str = creds + job_cfg
    hash = hashlib.sha1(str.encode(cfg_str)).hexdigest()
    hash = int(hash, 16) % (10 ** 8)
    return f"{user_id}_hash_{str(hash)}"


def get_uid_for_template(dag_id, creds, job_cfg):
    dag_id = f"{dag_id}_{get_config_hashvalue(creds, job_cfg)}"
    _LOGGER.info("***********************************")
    _LOGGER.info(f"Please notedown dag_id : {dag_id}")
    _LOGGER.info("***********************************")
    return dag_id


'''class AirflowClient:
    def __init__(self):
        self.connection = None
        # using local-airflow-client
        from airflow.api.client.local_client import Client
        from airflow.settings import engine as _engine

        self.client = Client(api_base_url=None, auth=None)

    def __enter__(self):
        self.connection = _engine.connect()

    def __exit__(self, type, value, traceback):
        self.connection.close()

    def trigger_dag_run(self, dag_id, run_id=None, conf=None, execution_date=None):
        return self.client.trigger_dag(
            dag_id=dag_id, run_id=run_id, conf=conf, execution_date=execution_date,
        )

    def get_dag_status(self, dag_id, run_id=None):
        dag_run_table_query = f"""
                select * from dag_run
                where
                    dag_id='{dag_id}'
                and
                    run_id='{run_id}'
            """
        return pd.read_sql(dag_run_table_query, self.connection)

    def get_dag_run_task_status(self, dag_id, run_id):
        task_instance_table_query = f"""
                select
                    a.*
                from
                    task_instance a
                join
                    dag_run b
                on
                    a.dag_id = b.dag_id
                and
                    a.execution_date = b.execution_date
                and
                    b.run_id='{run_id}'
                and
                    b.dag_id='{dag_id}'
                order by
                    a.priority_weight desc,
                    a.end_date asc
            """
        return pd.read_sql(task_instance_table_query, self.connection)

    def get_dag_run_failed_task_status(self, dag_id, run_id):
        task_fail_table_query = f"""
                select
                    a.*
                from
                    task_fail a
                join
                    dag_run b
                on
                    a.dag_id = b.dag_id
                and
                    a.execution_date = b.execution_date
                and
                    b.run_id='{run_id}'
                and
                    b.dag_id='{dag_id}'
                order by
                    a.end_date asc
            """
        return pd.read_sql(task_fail_table_query, self.connection)

    def get_all_runs_for_dag(self, dag_id):
        dag_run_table_query = f"""
                select * from dag_run
                where
                    dag_id='{dag_id}'
                order by
                    execution_date desc
            """
        return pd.read_sql(dag_run_table_query, self.connection)


def unpause_dag(dag_id):
    from airflow.bin.cli import unpause

    args = Namespace(dag_id=dag_id)
    unpause(args)


def pause_dag(dag_id):
    from airflow.bin.cli import pause

    args = Namespace(dag_id=dag_id)
    pause(args)'''


def get_resources_mapping(const_dict):
    upd = copy.deepcopy(const_dict)
    for k, v in const_dict.items():
        upd[k] = list(const_dict[k].keys())[0]
        upd[k + "_resources"] = list(const_dict[k].values())[0]
    return upd


def frame_dag_with_jinja(
    dag_id, creds_config_path, job_config_path, template_path, ecr_image_uri
):
    if creds_config_path.startswith('s3'):
        creds_config = s3fs.S3FileSystem().open(creds_config_path).read()
    else:
        creds_config = Path(creds_config_path).read_text()
    if job_config_path.startswith('s3'):
        job_config = s3fs.S3FileSystem().open(job_config_path).read()
    else:
        job_config = Path(job_config_path).read_text()
    job_spec = yaml.safe_load(job_config)
    creds_spec = yaml.safe_load(creds_config)

    _LOGGER.info(f"Reading template: template, from {template_path}")
    template_file_name = template_path.split("/")[-1]
    template_dir_path = template_path.replace(template_file_name, "")[:-1]
    env = Environment(loader=FileSystemLoader(template_dir_path))
    template = env.get_template(template_file_name)

    dag_id = get_uid_for_template(dag_id, creds_config, job_config)
    node_selector = NODE_SELECTORS[creds_spec["credentials"]["execution_mode"]][
        job_spec["run_params"]["model_name"]
    ]
    template_args = {
        "dag_id": dag_id,
        "creds_config": creds_config,
        "job_config": job_config,
        "ecr_image_uri": ecr_image_uri,
    }
    upd_node_selector = get_resources_mapping(node_selector)
    template_args.update(upd_node_selector)
    output_from_parsed_template = template.render(**template_args)

    dest_dag_file_path = f"{Core.config.credentials.airflow.dag_folder_path()}/{dag_id}"
    with Gateways.tld_s3().open(f"{dest_dag_file_path}.py", "w") as text_file:
        text_file.write(output_from_parsed_template)

    _LOGGER.info(f"Dag file placed in : {dest_dag_file_path}")
    _LOGGER.info(
        f"Successfully created dag:{dag_id}, with template:{template_file_name}"
    )

    return dag_id


def overwrite_and_trigger_dag(
    dag_id,
    ecr_image_uri,
    run_id=None,
    conf=None,
    execution_date=None,
    watch=False,
    poll_seconds=20,
    airflow_client=None,
    overwrite_if_exists=False,
    creds_config_path=None,
    job_config_path=None,
    template_path=None,
):
    if overwrite_if_exists:
        dag_id = frame_dag_with_jinja(
            dag_id=dag_id,
            creds_config_path=creds_config_path,
            job_config_path=job_config_path,
            template_path=template_path,
            ecr_image_uri=ecr_image_uri,
        )

        wait_str = (
            f"Waiting for dag, {dag_id} to be read by the scheduler. Please wait !"
        )
        _LOGGER.info(wait_str)
        time.sleep(40)
        while True:
            request = unpause_dag_via_rest(dag_id=dag_id)
            if '"response":"ok"' not in request.text:
                _LOGGER.info(wait_str)
                time.sleep(poll_seconds)
            else:
                trigger_dag_via_rest(dag_id=dag_id)
                break

        _LOGGER.info(f"Enabled dag: {dag_id}")


"""def watch_dag(
    dag_id, run_id=None, poll_seconds=20, airflow_client=None,
):
    if airflow_client is None:
        airflow_client = AirflowClient()

    with airflow_client:
        while True:
            dag_df = airflow_client.get_dag_status(dag_id, run_id)
            task_details_df = airflow_client.get_dag_run_task_status(dag_id, run_id)
            task_details_df["state"] = task_details_df["state"].fillna("Not Scheduled")
            temp_df = pd.DataFrame(
                task_details_df[["state", "task_id"]]
                .groupby(by=["state"])["task_id"]
                .apply(list)
            ).reset_index()

            _LOGGER.info("________________Start________________")
            _LOGGER.info(
                "\n"
                + tabulate(
                    dag_df[["dag_id", "run_id", "execution_date", "state"]],
                    headers="keys",
                    tablefmt="pretty",
                )
                + "\n"
            )
            for index, row in temp_df.iterrows():
                _LOGGER.info(f"*****{row['state']}*****, {len(row['task_id'])}")
                _LOGGER.info("\n" + str(row["task_id"]) + "\n")
            _LOGGER.info("________________End________________\n\n")

            if dag_df["state"][0] != "running":
                break
            time.sleep(poll_seconds)"""


def execute_jobs_airflow(
    dag_id, run_id, creds_config_path, job_config_path, template_path, ecr_image_uri,
):
    overwrite_and_trigger_dag(
        dag_id=dag_id,
        run_id=run_id,
        conf=None,
        execution_date=None,
        watch=False,
        poll_seconds=20,
        overwrite_if_exists=True,
        creds_config_path=creds_config_path,
        job_config_path=job_config_path,
        template_path=template_path,
        ecr_image_uri=ecr_image_uri,
    )

    """watch_dag(
        dag_id=dag_id, run_id=run_id, poll_seconds=10, airflow_client=airflow_client
    )

    pause_dag(dag_id=dag_id)"""
