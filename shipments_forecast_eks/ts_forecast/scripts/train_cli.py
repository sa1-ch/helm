import logging
from functools import partial

import pandas as pd

from ts_forecast.core.train import run_training
from ts_forecast.core.utils.common import set_seed
from ts_forecast.core.utils.dataset import FilteredDataset, time_filter_func
from ts_forecast.core.utils.gluon import load_gluon_dataset
from ts_forecast.core.utils.job import create_jobs

_LOGGER = logging.getLogger(__name__)


def run_training_job(job, creds, dag_id):
    set_seed(seed_value=job["run_params"]["seed_value"])

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

    _LOGGER.info("Model-Training : STARTED")
    # Train-Data
    # FIXME: #43: Configure train_start_date from config file
    train_start_date = job["run_params"]["data_start_date"]
    tst = pd.to_datetime(job["run_params"]["last_train_date"]) + pd.Timedelta(days=1)
    train_filter = partial(
        time_filter_func,
        start_date=train_start_date,
        end_date=tst,
        unit=ds.metadata.freq,
    )
    _LOGGER.info(f"Train-Data: Start:{train_start_date} & End:{tst}")
    job["run_params"]["hyper_params"].update(mtd)
    train_ds = FilteredDataset(ds.train, transform_func=train_filter)

    # Train-Model
    job["dag_id"] = dag_id
    run_training(job.copy(), train_ds, None)
    _LOGGER.info("Model-Training : COMPLETED")


def run_training_cli(cfg, creds, dag_id):
    _LOGGER.info("Creating-Tasks : STARTED")
    jobs = create_jobs(cfg)
    _LOGGER.info("Creating-Tasks : COMPLETED")

    for job in jobs:
        for task in job:
            run_training_job(creds=creds, job=task, dag_id=dag_id)
