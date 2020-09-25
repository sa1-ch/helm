import logging
from functools import partial
from itertools import islice

import pandas as pd

from ts_forecast.core.eval import (
    get_parallel_process_ids,
    merge_scoring_jobs,
    run_evaluation,
)
from ts_forecast.core.utils.common import set_seed
from ts_forecast.core.utils.dataset import (
    FilteredDataset,
    minimum_samples_filter,
    time_filter_func,
)
from ts_forecast.core.utils.gluon import load_gluon_dataset
from ts_forecast.core.utils.job import create_jobs

_LOGGER = logging.getLogger(__name__)
logging.getLogger("fbprophet").setLevel(logging.WARNING)


def get_filter_score_data(job, creds, start_index, end_index):
    datapath = job["run_params"]["datapath"]
    ds = load_gluon_dataset(
        path=datapath,
        cfg=creds,
        files_filter=None,
        iter_load_all_data=job["run_params"]["iter_load_all_data"],
    )

    lookup = {"D": 1, "W": 7, "M": 30}
    ds.metadata.prediction_length = (
        job["training_frequency"]["full"] // lookup[ds.metadata.freq[0]]
    )
    mtd = {
        "freq": ds.metadata.freq,
        "cardinality": [x.cardinality for x in ds.metadata.feat_static_cat],
        "prediction_length": ds.metadata.prediction_length,
    }

    # Test-Data
    train_start_date = job["run_params"]["data_start_date"]
    test_end_date = pd.to_datetime(job["run_params"]["test_end_date"]) + pd.Timedelta(
        days=1
    )
    test_filter = partial(
        time_filter_func,
        start_date=train_start_date,
        end_date=test_end_date,
        unit=ds.metadata.freq,
    )
    _LOGGER.info(f"Test-Data: Start:{train_start_date} & End:{test_end_date}")

    min_size_filter_func_test = partial(
        minimum_samples_filter, min_size=ds.metadata.prediction_length
    )
    job["run_params"]["hyper_params"].update(mtd)
    test_ds = FilteredDataset(
        ds.train,
        transform_func=test_filter,
        post_filter_func=min_size_filter_func_test,
    )

    return list(islice(test_ds, int(start_index), int(end_index)))


def run_scoring_job(job, creds, dag_id):
    set_seed(seed_value=job["run_params"]["seed_value"])
    _LOGGER.info("Scoring : STARTED")

    job["dag_id"] = dag_id
    data = get_filter_score_data(
        job,
        creds,
        job["run_params"]["evaluation"]["start_index_per_scoring_task"],
        job["run_params"]["evaluation"]["end_index_per_scoring_task"],
    )
    run_evaluation(job_cfg=job.copy(), creds=creds, data=data)
    _LOGGER.info("Scoring : COMPLETED")


def merge_scoring_jobs_cli(cfg, dag_id):
    jobs = create_jobs(cfg)

    for job in jobs:
        for task in job:
            _LOGGER.info("Merge-Scoring : STARTED")
            task["dag_id"] = dag_id
            merge_scoring_jobs(task, dag_id)
            _LOGGER.info("Merge-Scoring : COMPLETED")


def run_scoring_cli(cfg, creds, dag_id):
    _LOGGER.info("Creating-Tasks : STARTED")
    jobs = create_jobs(cfg)
    _LOGGER.info("Creating-Tasks : COMPLETED")

    for job in jobs:
        for task in job:
            sliced_gen = get_parallel_process_ids(task)

            for iter_sliced_gen in sliced_gen:
                _LOGGER.info(f"Starting task for data: {iter_sliced_gen}")
                iter_score_dag_id = (
                    dag_id
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
                run_scoring_job(creds=creds, job=task, dag_id=dag_id)

            _LOGGER.info("Merge-Scoring : STARTED")
            task["dag_id"] = dag_id
            merge_scoring_jobs(task, dag_id)
            _LOGGER.info("Merge-Scoring : COMPLETED")
