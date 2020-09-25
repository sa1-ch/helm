import logging
import os

import boto3
import mlflow
import pandas as pd

from ts_forecast.core.constants.common import (
    DEEP_AR_ESTIMATOR,
    DEEP_STATE_ESTIMATOR,
    PROPHET_PREDICTOR,
)
from ts_forecast.core.constants.metrics import (
    ITEM_LEVEL_METRICS_NAME,
    SCORE_TS_ERROR_FILE_NAME,
    TS_PERIOD_LEVEL_MERGED_NAME,
)
from ts_forecast.core.dependencies.containers import Core, Gateways
from ts_forecast.core.utils.eval import (
    compute_and_log_metrics,
    get_forecast_path_parent_score,
    get_parent_run_id,
    get_train_run_id,
)
from ts_forecast.core.utils.gluon import get_predictor
from ts_forecast.core.utils.io import get_csv_from_s3
from ts_forecast.core.utils.mlflow import (
    init_mlflow,
    log_evaluation_metrics,
    mlflow_experiment_run,
)

_LOGGER = logging.getLogger(__name__)


def get_parallel_process_ids_util(data_per_parallel_process, len_files):
    sliced_gen = [
        (i, i + data_per_parallel_process,)
        for i in range(0, len_files, data_per_parallel_process,)
    ]
    print(sliced_gen)
    return sliced_gen


def get_parallel_process_ids(task):
    sliced_gen = get_parallel_process_ids_util(
        task["run_params"]["evaluation"]["data_per_parallel_process"],
        task["run_params"]["evaluation"]["data_set_length"],
    )
    return sliced_gen


def get_parallel_process_merge_score_ids(task, len_files_list):
    sliced_gen = get_parallel_process_ids_util(
        task["run_params"]["evaluation"]["data_per_merge_score_mp"], len_files_list
    )
    return sliced_gen


def read_score_files_from_s3(bucket_name, file_list, iter_sliced_gen):
    master_df = pd.DataFrame()
    for iter_file in file_list[iter_sliced_gen[0] : iter_sliced_gen[1]]:
        _LOGGER.info(f"Reading TS: {iter_file}")
        temp_df = get_csv_from_s3(iter_file)
        master_df = master_df.append(temp_df)

    return master_df


def get_score_files_recursively(task):
    resource = Core.config.credentials.tld_s3.protocol()
    bucket_name = (
        Core.config.credentials.tld_s3.prefix()
        .replace(f"{Core.config.credentials.tld_s3.protocol()}://", "")
    )
    forecast_out_path = get_forecast_path_parent_score(task)
    bucket_prefix = forecast_out_path.replace(
        Core.config.credentials.tld_s3.prefix() + "/", ""
    )
    _LOGGER.info(f"Reading files in: {forecast_out_path}")

    s3 = boto3.resource(resource)
    mybucket = s3.Bucket(bucket_name)
    objs = mybucket.objects.filter(Prefix=bucket_prefix)

    file_list = []
    for obj in objs:
        path, filename = os.path.split(obj.key)
        if f"{TS_PERIOD_LEVEL_MERGED_NAME}.csv" in filename:
            temp_path = (
                Core.config.credentials.tld_s3.protocol()
                + "://"
                + os.path.join(bucket_name, path, filename)
            )
            file_list.append(temp_path)

    master_df = read_score_files_from_s3(bucket_name, file_list, (0, len(file_list)))
    master_df = master_df.reset_index(drop=True)

    out_path = os.path.join(forecast_out_path, f"{TS_PERIOD_LEVEL_MERGED_NAME}.csv")
    _LOGGER.info(f"Writing final_merged data to: {out_path}")
    with Gateways.tld_s3().open(out_path, "w") as fp:
        master_df.to_csv(fp, index=False)


def run_evaluation_deep_state_ar(job_cfg, creds, data, is_prediction=True):
    init_mlflow(job_cfg["name"])
    predictor = get_predictor(job_cfg, None)
    compute_and_log_metrics(
        job_cfg=job_cfg,
        creds=creds,
        predictor=predictor,
        score_item_to_s3=True,
        calc_eval_metrics=job_cfg["run_params"]["evaluation"]["run_eval_in_score"],
        ts_error_file_name=SCORE_TS_ERROR_FILE_NAME,
        data=data,
    )


def run_evaluation_prophet(job_cfg, creds, data, is_prediction=True):
    init_mlflow(job_cfg["name"])
    compute_and_log_metrics(
        job_cfg=job_cfg,
        creds=creds,
        predictor=None,
        score_item_to_s3=True,
        calc_eval_metrics=True,
        ts_error_file_name=SCORE_TS_ERROR_FILE_NAME,
        data=data,
    )


def run_evaluation(job_cfg, creds, data, is_prediction=True):
    model_name = job_cfg["run_params"]["model_name"]
    _LOGGER.info(f"Scoring {model_name} model")
    if model_name in [DEEP_STATE_ESTIMATOR, DEEP_AR_ESTIMATOR]:
        run_evaluation_deep_state_ar(job_cfg, creds, data, is_prediction)
    elif model_name == PROPHET_PREDICTOR:
        run_evaluation_prophet(job_cfg, creds, data, is_prediction)


def merge_scoring_jobs(task, dag_id):
    path = get_forecast_path_parent_score(task)

    master_list = None
    sliced_gen = get_parallel_process_ids(task)
    for iter_sliced_gen in sliced_gen:
        sub_folder = str(iter_sliced_gen[0]) + "_" + str(iter_sliced_gen[1])
        file_path = os.path.join(path, sub_folder, ITEM_LEVEL_METRICS_NAME + ".csv")
        if master_list is None:
            master_list = get_csv_from_s3(file_path)
        else:
            master_list = master_list.append(get_csv_from_s3(file_path))

    col_names_without_item_id = list(master_list.drop(columns=["item_id"]).columns)
    avg_master_list = dict(master_list[col_names_without_item_id].mean())

    exp_name = task["name"]
    run_name = task["run_params"]["name"]
    model_name = task["run_params"]["model_name"]
    client, exp_id = init_mlflow(exp_name)
    parent_run_id = get_parent_run_id(client, exp_id, task)

    if model_name in [DEEP_STATE_ESTIMATOR, DEEP_AR_ESTIMATOR]:
        train_run_id = get_train_run_id(client, exp_id, parent_run_id, task)
    elif model_name == PROPHET_PREDICTOR:
        train_run_id = None

    with mlflow.start_run(
        experiment_id=exp_id, run_name=run_name, run_id=parent_run_id
    ):
        exception = None
        with mlflow_experiment_run(run_name=run_name, run_id=train_run_id, nested=True):
            try:
                if model_name == PROPHET_PREDICTOR:
                    run_id = client.get_run(mlflow.active_run().info.run_id).info.run_id
                    mlflow.set_tag("p_run_id", parent_run_id)
                    mlflow.set_tag(
                        "run_id", run_id,
                    )
                    mlflow.set_tag("dag_id", task["dag_id"])
                    mlflow.set_tag("model_name", model_name)
                    mlflow.log_params(task["run_params"]["hyper_params"])
                    mlflow.log_param("model_date", task["model_date"])
                    mlflow.log_param(
                        "last_train_date", task["run_params"]["last_train_date"]
                    )

                mlflow.set_tag("scoring", task["run_params"]["training"])
                mlflow.set_tag("score_out_path", path)

                _LOGGER.info("Logging Performance-Metrics: STARTED")
                log_evaluation_metrics(metrics_dict=avg_master_list)
                _LOGGER.info("Logging Performance-Metrics: COMPLETED")

                mlflow.set_tag("score_status", "FINISHED")
            except Exception as e:
                mlflow.set_tag("score_status", "FAILED")
                exception = e

    if exception is not None:
        raise exception

    get_score_files_recursively(task)
