import datetime
import logging
import os
import os.path as op
import sys
from copy import deepcopy
from functools import partial
from multiprocessing import Pool

import numpy as np
import pandas as pd
from scipy import stats

import ts_forecast.core.model as gluon_models
from ts_forecast import version
from ts_forecast.core.constants.common import (
    DEEP_AR_ESTIMATOR,
    DEEP_STATE_ESTIMATOR,
    PROPHET_PREDICTOR,
)
from ts_forecast.core.constants.metrics import (
    AGG_METRICS,
    ITEM_LEVEL_METRICS_NAME,
    TRAIN_TS_ERROR_FILE_NAME,
    TS_PERIOD_LEVEL_MERGED_NAME,
)
from ts_forecast.core.dependencies.containers import Gateways
from ts_forecast.core.utils.gluon import (
    get_evaluation_metrics,
    get_forecast_values,
    get_predictor,
    get_sequential_parallel_predictor,
)
from ts_forecast.core.utils.metrics import get_metrics
from ts_forecast.core.utils.mlflow import get_parent_run_details, get_train_details

_LOGGER = logging.getLogger(__name__)


def generate_forecast_res(forecast, job_cfg, freq):
    """Generating the Forecast CSV file to put in outputs.
       Fix this - other relevant params acan be chose to be stores in the forecast file
    """
    yhat = forecast.samples.mean(axis=0)
    std = forecast.samples.std(axis=0)
    yhat_lower = forecast.samples.min(axis=0)
    yhat_upper = forecast.samples.max(axis=0)
    yhat_50_percent = stats.norm.interval(0.50, loc=yhat, scale=std)
    yhat_95_percent = stats.norm.interval(0.95, loc=yhat, scale=std)

    tsd = pd.to_datetime(job_cfg["run_params"]["last_train_date"]) + pd.Timedelta(
        days=1
    )
    ted = pd.to_datetime(job_cfg["run_params"]["test_end_date"])
    dates = list(pd.date_range(tsd, ted, freq=freq))

    atemp = pd.DataFrame(
        {
            "busidaydt": dates,
            "yhat": yhat,
            "yhat_lower": yhat_lower,
            "yhat_upper": yhat_upper,
            "yhat_0.50_left": yhat_50_percent[0],
            "yhat_0.50_right": yhat_50_percent[1],
            "yhat_0.95_left": yhat_95_percent[0],
            "yhat_0.95_right": yhat_95_percent[1],
        }
    )
    atemp["item_id"] = forecast.item_id
    atemp["last_train_date"] = job_cfg["run_params"]["last_train_date"]
    atemp["type"] = job_cfg["dataset_name"]
    return atemp


def generate_forecast_res_prophet(forecast, job_cfg, freq):
    """Generating the Forecast CSV file to put in outputs.
       Fix this - other relevant params acan be chose to be stores in the forecast file
    """
    atemp = pd.DataFrame(forecast.samples, columns=list(forecast.info.keys()))
    
    atemp["item_id"] = forecast.item_id
    atemp["last_train_date"] = '2015-12-12'
    atemp["type"] = 'sales_forecast'
    atemp.rename(columns={'ds': 'busidaydt'}, inplace=True)

    return atemp


def filter_num_time_series(forecast_it, ts_it, num_time_series):
    forecast_list = []
    ts_list = []
    for itr, (test_data, forecast) in enumerate(zip(ts_it, forecast_it)):
        forecast_list.append(forecast)
        ts_list.append(test_data)

        if str(itr) == str(num_time_series):
            break
    return forecast_list, ts_list


def get_forecast_path_parent_score(job_cfg):
    path = op.join(
        job_cfg["run_params"]["evaluation"]["forecastpath"],
        job_cfg["name"],
        job_cfg["dag_id"],
        "FD_"
        + str(
            datetime.datetime.strftime(
                pd.to_datetime(job_cfg["model_date"]), format="%Y%m%d"
            )
        ),
        job_cfg["dataset_name"],
    )
    return path


def get_forecast_path(job_cfg):
    path = get_forecast_path_parent_score(job_cfg)
    path = op.join(
        path,
        str(job_cfg["run_params"]["evaluation"]["start_index_per_scoring_task"])
        + "_"
        + str(job_cfg["run_params"]["evaluation"]["end_index_per_scoring_task"]),
    )
    return path


def save_outputs(data, path):
    """Saving the forecast file in teh path specified in S3"""
    _LOGGER.info(f"Saving outputs to: {path}")
    with Gateways.tld_s3().open(path, "w") as fp:
        data.to_csv(fp, index=False)


def save_ts_error_list(
    ts_error_list, path, error_file_name, start_date, end_date, score_item_to_s3=False,
):
    if len(ts_error_list) > 0:
        _LOGGER.error(
            f"""
        Time-Series doesn't have data for the period, start:{start_date}, end:{end_date}
        """
        )
        _LOGGER.error(ts_error_list)

        ts_error_list = pd.DataFrame(ts_error_list, columns=["Item_id"])

        file_path = op.join(path, f"{error_file_name}.csv")
        save_outputs(data=ts_error_list, path=file_path)
        _LOGGER.info(f"Error-Metrics saved in: {file_path}")


def save_item_level_metrics(
    agg_metrics_across_ts, path, file_name=ITEM_LEVEL_METRICS_NAME
):
    file_path = op.join(path, f"{file_name}.csv")
    save_outputs(data=agg_metrics_across_ts, path=file_path)
    _LOGGER.info(f"Item-Level-Metrics saved in: {file_path}")


def iter_compute_and_log_metrics(
    score_item_to_s3,
    calc_eval_metrics,
    job_cfg,
    creds,
    predictor,
    path,
    tsd,
    ted,
    data,
    slice_value,
):
    # with suppress_stdout_stderr():
    _LOGGER.info(f"Sliced_Value: {slice_value}")
    print(slice_value[0], slice_value[1])
    iter_data = data[slice_value[0] : slice_value[1]]
    model_name = job_cfg["run_params"]["model_name"]

    if predictor is None:
        if model_name in [DEEP_STATE_ESTIMATOR, DEEP_AR_ESTIMATOR]:
            predictor = get_predictor(job_cfg, None)
        elif model_name == PROPHET_PREDICTOR:
            hyper_params = deepcopy(job_cfg["run_params"]["hyper_params"])
            freq = hyper_params.pop("freq", None)
            prediction_length = hyper_params.pop("prediction_length", None)
            del hyper_params["cardinality"]
            params = dict(
                freq=freq,
                prediction_length=prediction_length,
                prophet_params=hyper_params,
            )

            if params["prophet_params"].get("no_ts_scored", ""):
                del params["prophet_params"]["no_ts_scored"]

            cls = getattr(gluon_models, model_name)
            predictor = cls.from_hyperparameters(**params)
            predictor = get_sequential_parallel_predictor(
                eval_method=job_cfg["run_params"]["evaluation"]["eval"],
                predictor=predictor,
                job_cfg=job_cfg,
            )

    _LOGGER.info("Forecasting Test-Data: STARTED")
    (forecast_it, ts_it) = get_forecast_values(
        job_cfg=job_cfg, data=iter_data, predictor=predictor
    )
    _LOGGER.info("Forecasting Test-Data: COMPLETED")

    _LOGGER.info("Metrics-Calculation: STARTED")
    ts_error_list = []
    agg_metrics_across_ts = []
    agg_period_ts_list = pd.DataFrame()

    for itr, (test_data, forecast) in enumerate(zip(ts_it, forecast_it), start=1):
        test_forecast_length = test_data.loc[
            (test_data.index >= tsd) & (test_data.index <= ted)
        ]

        if (
            len(test_forecast_length)
            != job_cfg["run_params"]["hyper_params"]["prediction_length"]
        ):
            _LOGGER.error(f"Skipped-Item: {forecast.item_id}")
            ts_error_list.append(forecast.item_id)
            continue

        # Check for nan values and total forecast=0 in test_data
        check_test_values = test_data[
            -job_cfg["run_params"]["hyper_params"]["prediction_length"] :
        ].values
        if np.isnan(check_test_values).any() or np.sum(check_test_values) == 0:
            _LOGGER.error(f"Skipped-Item [nan, sum-zero]: {forecast.item_id}")
            ts_error_list.append(forecast.item_id)
            continue

        _LOGGER.info(f"item-Started: {forecast.item_id}")

        # Get Forecast & Actual values
        if model_name == PROPHET_PREDICTOR:
            atemp = generate_forecast_res_prophet(forecast, job_cfg, predictor.freq)
        else:
            atemp = generate_forecast_res(forecast, job_cfg, predictor.freq)
        atemp["actual_values"] = check_test_values
        if score_item_to_s3:
            atemp["registered_model_name"] = job_cfg["run_params"][
                "registered_model_name"
            ]
            atemp["version"] = version

            if not atemp.empty:
                save_outputs(
                    data=atemp,
                    path=os.path.join(
                        path, "ts_period_level", forecast.item_id + ".csv"
                    ),
                )
                agg_period_ts_list = agg_period_ts_list.append(atemp)

        if calc_eval_metrics:
            # Gluon-TS metrics calculation
            #(agg_metrics, item_metrics) = get_evaluation_metrics(
            #    forecast_list=[forecast], ts_list=[test_data]
            #)
            agg_metrics = {}
            # Custom metrics calculation
            atemp['yhat'] = atemp['yhat'].astype(float)
            metrics = get_metrics(y_actual=atemp["actual_values"], y_pred=atemp["yhat"])
            for metric, value in metrics.items():
                for op_name, op_func in AGG_METRICS:
                    # mlflow accepts only float-values as metric
                    agg_metrics[f"{op_name}_{metric}"] = float(op_func(value))

            agg_metrics["item_id"] = str(forecast.item_id)
            agg_metrics_across_ts.append(agg_metrics)

    _LOGGER.info("Metrics-Calculation: COMPLETED")

    return agg_metrics_across_ts, ts_error_list, agg_period_ts_list


def mute():
    sys.stdout = open(os.devnull, "w")


def compute_and_log_metrics(
    job_cfg,
    creds,
    predictor=None,
    score_item_to_s3=False,
    calc_eval_metrics=False,
    ts_error_file_name=TRAIN_TS_ERROR_FILE_NAME,
    data=None,
):
    """Calculates and logs evaluation metrics
       for a given job_config, data, predictor

    Arguments:
        job_cfg - Dictionary containing job config
        data - Data for which the forecast to be done
        predictor - predictor with which the forecast to be done
    """
    # Logging No-of-Time-Series used for evaluation
    path = get_forecast_path(job_cfg=job_cfg)
    tsd = pd.to_datetime(job_cfg["run_params"]["last_train_date"]) + pd.Timedelta(
        days=1
    )
    ted = pd.to_datetime(job_cfg["run_params"]["test_end_date"])

    data_split_length = int(
        len(data) / job_cfg["run_params"]["evaluation"]["num_workers_per_scoring_task"]
    )
    sliced_gen = [
        (i, i + data_split_length) for i in range(0, len(data), data_split_length,)
    ]
    _LOGGER.info(f"Sliced score intervals: {sliced_gen}")

    with Pool(len(sliced_gen)) as pool:
        results = pool.map(
            partial(
                iter_compute_and_log_metrics,
                score_item_to_s3,
                calc_eval_metrics,
                job_cfg,
                creds,
                predictor,
                path,
                tsd,
                ted,
                data,
            ),
            sliced_gen,
        )

    agg_metrics_across_ts = []
    ts_error_list = []
    agg_period_ts_df = pd.DataFrame()
    for iter_result in results:
        agg_metrics_across_ts = agg_metrics_across_ts + iter_result[0]
        ts_error_list = ts_error_list + iter_result[1]
        agg_period_ts_df = agg_period_ts_df.append(iter_result[2])

    if calc_eval_metrics:
        # FIXME: #61: Log this as an artifact along with the item_id to S3
        agg_metrics_across_ts = pd.DataFrame(agg_metrics_across_ts)
        col_names_without_item_id = list(
            agg_metrics_across_ts.drop(columns=["item_id"]).columns
        )
        save_item_level_metrics(
            agg_metrics_across_ts=agg_metrics_across_ts[
                ["item_id"] + col_names_without_item_id
            ],
            path=path,
            file_name=ITEM_LEVEL_METRICS_NAME,
        )
        save_outputs(
            data=agg_period_ts_df,
            path=os.path.join(path, f"{TS_PERIOD_LEVEL_MERGED_NAME}.csv"),
        )

    save_ts_error_list(
        ts_error_list=ts_error_list,
        path=path,
        error_file_name=ts_error_file_name,
        start_date=tsd,
        end_date=ted,
        score_item_to_s3=score_item_to_s3,
    )


def get_parent_run_id(client, exp_id, job_cfg):
    parent_run_details = get_parent_run_details(client, exp_id, job_cfg)
    return parent_run_details.info.run_id


def get_train_run_id(client, exp_id, parent_run_id, job_cfg):
    train_run_details = get_train_details(client, exp_id, parent_run_id, job_cfg)
    return train_run_details.info.run_id
