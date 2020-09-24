import logging
import time
from contextlib import contextmanager

import mlflow
import pandas as pd
from mlflow.tracking import MlflowClient

from ts_forecast.core.dependencies.containers import Core
from ts_forecast.core.utils.job import _create_job_name

_LOGGER = logging.getLogger(__name__)

FLAVOR_NAME = "GluonTS"
MODEL_SUBPATH = "model"


def init_mlflow(expt_name):
    """Function to inilialise the MLFlow Client for the experiment"""
    store_params = Core.config.credentials.mlflow_store()
    tracking_uri = store_params["uri"].format(**store_params)
    artifact_location = Core.config.credentials.mlflow_artifact_store.prefix()

    client = MlflowClient(tracking_uri=tracking_uri)
    try:
        expt = client.get_experiment_by_name(expt_name)
        expt_id = expt.experiment_id
    except Exception:
        expt_id = client.create_experiment(
            expt_name, artifact_location=artifact_location
        )

    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(expt_name)

    return (client, expt_id)


def get_run_details(
    client, exp_name, reg_model_name=None, model_filter=None, finished_runs=True,
):
    """Obtain the version number of the latest model based on a filter
    """
    exp = client.get_experiment_by_name(exp_name)
    exp_id = exp.experiment_id

    runs = client.search_runs(experiment_ids=[exp_id])
    model_filter = model_filter or (lambda x: True)

    all_runs = []
    for run in runs:
        try:
            if (
                (
                    (run.info.status == "FINISHED")
                    and (run.data.tags["train_status"] == "FINISHED")
                )
                if finished_runs
                else True
            ) and model_filter(run):
                all_runs.append(run)
        except Exception:
            # it is possible that the filter (e.g. on some parmeter)
            # we are applying might throw errors on some old runs.
            # just ignore those for now
            pass

    if len(all_runs) == 0:
        raise Exception(
            "No Trained Models Available for the given experiment {}".format(exp_id)
        )

    return all_runs


def get_run_id_from_runs(runs):
    if len(runs) > 0:
        run_ids = []
        for run in runs:
            run_ids.append(run.info.run_id)
        return run_ids

    return None


def get_latest_modelversion(client, exp_name, reg_model_name, model_filter=None):
    """Obtain the version number of the latest model based on a filter
    """
    finished_runs = get_run_details(client, exp_name, reg_model_name, model_filter)
    run_ids = get_run_id_from_runs(finished_runs)

    vers = client.search_model_versions("name='{}'".format(reg_model_name))
    vers = [x for x in vers if x.run_id in run_ids]

    if len(vers) == 0:
        raise Exception(
            "No Trained Models Available for the giver filter {}".format(str(filter))
        )

    return vers[-1].version


@contextmanager
def mlflow_experiment_run(experiment_id=None, run_name=None, run_id=None, nested=False):
    _LOGGER.info(f"mlflow-uri : {Core.config.credentials.mlflow_store.uri()}")

    with mlflow.start_run(
        experiment_id=experiment_id, run_name=run_name, run_id=run_id, nested=nested,
    ) as run:
        yield run


def log_parent_run_task(client, exp_id, job_cfg):
    with mlflow_experiment_run(
        experiment_id=exp_id, run_name=_create_job_name(job_cfg)
    ):
        parent_run_details = client.get_run(mlflow.active_run().info.run_id)
        mlflow.set_tag("run_id", parent_run_details.info.run_id)
        mlflow.set_tag("dag_id", job_cfg["dag_id"])
        mlflow.set_tag("model_name", job_cfg["run_params"]["model_name"])
        mlflow.log_params(job_cfg["run_params"]["hyper_params"])


def get_parent_run_details(client, exp_id, job_cfg):
    model_filter = (
        lambda x: x.data.tags["dag_id"] == job_cfg["dag_id"]
        and x.data.tags["mlflow.runName"] == job_cfg["run_params"]["name"]
        and x.data.tags.get("mlflow.parentRunId") is None
        and x.info.status == "FINISHED"
    )

    parent_run_details = get_run_details(
        client=client,
        exp_name=job_cfg["name"],
        model_filter=model_filter,
        finished_runs=False,
    )

    if len(parent_run_details) > 1:
        raise Exception("Duplicate Parent-Runs found !")

    return parent_run_details[-1]


def log_evaluation_metrics(metrics_dict):
    """Logs the evaluation metrics

    Arguments:
        metrics_dict {dict} -- Evaluation-Metrics to be logged
    """
    metrics_dict = {
        k.replace("[", "_").replace("]", ""): v for k, v in metrics_dict.items()
    }
    mlflow.log_metrics(metrics_dict)


def get_artifacts_uri(job_cfg, data):
    """Obtain Forecasts with the latest version of model and Save them"""

    # FIXME: We assume the mlflow context is set before calling this
    # function
    client = mlflow.tracking.MlflowClient()
    model_filter = (
        lambda x: pd.to_datetime(x.data.params["last_train_date"])
        == pd.to_datetime(job_cfg["run_params"]["last_train_date"])
        and x.data.tags["dag_id"] == job_cfg["dag_id"]
        and x.data.tags["mlflow.runName"] == job_cfg["run_params"]["name"]
        and x.data.tags["mlflow.parentRunId"] is not None
    )

    train_run_details = get_run_details(
        client=client, exp_name=job_cfg["name"], model_filter=model_filter
    )[-1]
    uri = train_run_details.info.artifact_uri
    time.sleep(5)

    _LOGGER.info(f"Model uri: {uri}")

    return uri


def register_model(run_id, registered_model_name):
    store_params = Core.config.credentials.mlflow_store()
    tracking_uri = store_params["uri"].format(**store_params)
    artifact_location = Core.config.credentials.mlflow_artifact_store.prefix()
    client = MlflowClient(tracking_uri=tracking_uri)

    try:
        client.create_registered_model(registered_model_name)
    except Exception as e:
        if "RESOURCE_ALREADY_EXISTS" not in str(e):
            raise e
        else:
            _LOGGER.info(
                f"""Model-Name: {registered_model_name}, already registered.
                Creating a new version for the Model-Name."""
            )

    result = client.create_model_version(
        name=registered_model_name,
        source=f"{artifact_location}/{run_id}/artifacts/model",
        run_id=run_id,
    )

    _LOGGER.debug(result)
    _LOGGER.info(f"Registered_Model: {result.name}, with Version: {result.version}")
    return result


def get_train_details(client, exp_id, parent_run_id, job_cfg):
    model_filter = (
        lambda x: x.data.tags["dag_id"] == job_cfg["dag_id"]
        and x.data.tags["mlflow.runName"] == job_cfg["run_params"]["name"]
        and x.data.tags.get("mlflow.parentRunId") == parent_run_id
        and pd.to_datetime(x.data.params["model_date"])
        == pd.to_datetime(job_cfg["model_date"])
    )

    train_run_details = get_run_details(
        client=client,
        exp_name=job_cfg["name"],
        model_filter=model_filter,
        finished_runs=True,
    )

    if len(train_run_details) > 1:
        raise Exception("Duplicate Train-Runs found !")

    return train_run_details[-1]


def get_all_run_details(exp_name, dag_id, client, exp_id):
    model_filter = (
        lambda x: x.data.tags["dag_id"] == dag_id
        and x.data.tags.get("mlflow.parentRunId") is not None
    )

    run_details = get_run_details(
        client=client,
        exp_name=exp_name,
        model_filter=model_filter,
        reg_model_name=None,
        finished_runs=False,
    )

    return run_details


def log_merged_contents(exp_dag_list, job):
    for iter_exp_name, iter_dag_id in exp_dag_list.items():
        final_avg_dict = []
        client, exp_id = init_mlflow(iter_exp_name)
        run_details = get_all_run_details(iter_exp_name, iter_dag_id, client, exp_id)

        for iter_run_details in run_details:
            final_avg_dict.append(iter_run_details.data.metrics)
        avg_agg_metric = dict(pd.DataFrame(final_avg_dict).mean())
        job["run_params"]["name"] = job["name"] + "--" + job["dataset_name"]
        job["dag_id"] = iter_dag_id
        parent_run_details = get_parent_run_details(client, exp_id, job)
        with mlflow.start_run(
            experiment_id=exp_id,
            run_name=job["run_params"]["name"],
            run_id=parent_run_details.info.run_id,
        ):
            log_evaluation_metrics(metrics_dict=avg_agg_metric)
