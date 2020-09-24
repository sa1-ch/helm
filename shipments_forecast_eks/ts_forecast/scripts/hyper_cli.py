import hashlib
import itertools
import logging
from copy import deepcopy

import pandas as pd

from ts_forecast.core.constants.common import DEEP_AR_ESTIMATOR, DEEP_STATE_ESTIMATOR
from ts_forecast.scripts.mlflow_cli import merge_train_score_cli, parent_run_task_cli
from ts_forecast.scripts.score_cli import run_scoring_cli
from ts_forecast.scripts.train_cli import run_training_cli

_LOGGER = logging.getLogger(__name__)


def get_config_hashvalue(job_cfg, creds):
    cfg_str = str(creds) + str(job_cfg)
    hash = hashlib.sha1(str.encode(cfg_str)).hexdigest()
    hash = int(hash, 16) % (10 ** 8)
    return f"{str(hash)}"


def run_child_jobs(cfg_list, creds, dag_id):
    for cfg in cfg_list:
        iter_dag_id = dag_id + "_" + "hash" + "_" + get_config_hashvalue(cfg, creds)
        _LOGGER.info(f"Executing sub-dag : {iter_dag_id}")
        parent_run_task_cli(cfg, creds, iter_dag_id)
        if cfg["run_params"]["model_name"] in [DEEP_STATE_ESTIMATOR, DEEP_AR_ESTIMATOR]:
            run_training_cli(cfg, creds, iter_dag_id)

        run_scoring_cli(cfg, creds, iter_dag_id)
        merge_train_score_cli(cfg, iter_dag_id)


def run_hyper_cli(cfg, creds, dag_id):
    _LOGGER.info("Creating-Hyper-Parameter-Tasks : STARTED")

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

    run_child_jobs(cfg, creds, dag_id)

    _LOGGER.info("Creating-Hyper-Parameter-Tasks : COMPLETED")
