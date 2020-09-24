import logging

from ts_forecast.core.utils.gluon import load_gluon_dataset
from ts_forecast.core.utils.mlflow import (
    init_mlflow,
    log_merged_contents,
    log_parent_run_task,
)

_LOGGER = logging.getLogger(__name__)


def parent_run_task_cli(job, creds, dag_id):
    _LOGGER.info("Parent-Task logging : STARTED")

    ds = load_gluon_dataset(
        path=job["run_params"]["datapath"],
        cfg=creds,
        files_filter=None,
        iter_load_all_data=job["run_params"]["iter_load_all_data"],
    )
    mtd = {
        "freq": ds.metadata.freq,
        "cardinality": [x.cardinality for x in ds.metadata.feat_static_cat],
        "prediction_length": ds.metadata.prediction_length,
    }

    job["run_params"]["hyper_params"].update(mtd)
    job["run_params"]["hyper_params"]["no_ts_scored"] = job["run_params"]["evaluation"][
        "data_set_length"
    ]
    job["dag_id"] = dag_id
    client, exp_id = init_mlflow(expt_name=job["name"])
    log_parent_run_task(client=client, exp_id=exp_id, job_cfg=job)

    _LOGGER.info("Parent-Task logged successfully : COMPLETED")


def merge_train_score_cli(job, dag_id):
    exp_dag_list = {f"{job['name']}": dag_id}
    log_merged_contents(exp_dag_list, job)
