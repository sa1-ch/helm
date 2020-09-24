import logging
import os
import os.path as op
import tempfile
import warnings

import mlflow
import mxnet as mx
import pandas as pd
from mlflow.tracking.artifact_utils import _download_artifact_from_uri

import ts_forecast.core.model as gluon_models
from ts_forecast.core.constants.metrics import TRAIN_TS_ERROR_FILE_NAME
from ts_forecast.core.eval import compute_and_log_metrics
from ts_forecast.core.model.incremental_deep_state import IncrementalDeepStateEstimator
from ts_forecast.core.model.mlflow_trainer import MlflowTrainer
from ts_forecast.core.utils.gluon import log_model
from ts_forecast.core.utils.mlflow import (
    get_parent_run_details,
    get_run_details,
    init_mlflow,
    mlflow_experiment_run,
)

_LOGGER = logging.getLogger(__name__)


def run_training(
    job_cfg, train_data, test_data=None,
):

    if job_cfg["run_params"]["hyper_params"]["init"] == "xavier":
        job_cfg["run_params"]["hyper_params"].update({"init": mx.init.Xavier()})
    else:
        wr_msg = """Init param currently customises only for Xavier Initialisation.
        Default initialising used as the input is not valid
        """
        warnings.warn(wr_msg)
        job_cfg["run_params"]["hyper_params"].pop("init")

    exp_name = job_cfg["name"]
    run_name = job_cfg["run_params"]["name"]
    model_name = job_cfg["run_params"]["model_name"]
    hyper_params = dict(job_cfg["run_params"]["hyper_params"])

    client, exp_id = init_mlflow(exp_name)
    parent_run_details = get_parent_run_details(client, exp_id, job_cfg)

    exception = None
    with mlflow.start_run(
        experiment_id=exp_id, run_name=run_name, run_id=parent_run_details.info.run_id
    ):
        with mlflow_experiment_run(run_name=run_name, nested=True):
            try:
                mlflow.set_tag(
                    "p_run_id", parent_run_details.info.run_id
                )  # To be removed
                mlflow.set_tag(
                    "run_id",
                    client.get_run(mlflow.active_run().info.run_id).info.run_id,
                )
                mlflow.set_tag("dag_id", job_cfg["dag_id"])
                mlflow.set_tag("model_name", model_name)
                mlflow.set_tag("training", job_cfg["run_params"]["training"])
                mlflow.log_params(hyper_params)
                mlflow.log_param("training", job_cfg["run_params"]["training"])
                mlflow.log_param("model_date", job_cfg["model_date"])
                mlflow.log_param(
                    "last_train_date", job_cfg["run_params"]["last_train_date"]
                )
                cls = getattr(gluon_models, model_name)
                hyper_params["freq"] = hyper_params["freq"][0]
                estimator = cls.from_hyperparameters(**hyper_params)

                if job_cfg["run_params"]["training"] == "incremental":
                    if model_name == "DeepStateEstimator":
                        previous_model_train_date = pd.to_datetime(
                            job_cfg["run_params"]["last_train_date"]
                        ) + pd.Timedelta(
                            days=-int(job_cfg["training_frequency"]["incremental"])
                        )
                        model_filter = (
                            lambda x: pd.to_datetime(x.data.params["last_train_date"])
                            == previous_model_train_date
                            and x.data.tags["dag_id"] == job_cfg["dag_id"]
                            and x.data.tags["mlflow.runName"]
                            == job_cfg["run_params"]["name"]
                            and x.data.tags.get("mlflow.parentRunId") is not None
                        )
                        train_run_details = get_run_details(
                            client=client,
                            exp_name=job_cfg["name"],
                            model_filter=model_filter,
                        )[-1]
                        params_path = train_run_details.info.artifact_uri
                        net = estimator.create_training_network()
                        with tempfile.TemporaryDirectory() as out_dir:
                            _download_artifact_from_uri(
                                params_path, output_path=out_dir
                            )
                            fl = os.listdir(
                                out_dir + "/artifacts/model/trained_net_params/"
                            )
                            net.load_parameters(
                                out_dir + "/artifacts/model/trained_net_params/" + fl[0]
                            )

                        estimator = IncrementalDeepStateEstimator.from_hyperparameters(
                            network=net, **hyper_params
                        )
                    else:
                        err_msg = "Inc Learning not implemented for prophet"
                        raise NotImplementedError(err_msg)

                estimator.trainer = MlflowTrainer(
                    **dict(estimator.trainer.__dict__["__init_args__"])
                )
                transformation, trained_net, predictor = estimator.train_model(
                    train_data
                )
                predictor.freq = job_cfg["run_params"]["hyper_params"]["freq"]
                with tempfile.TemporaryDirectory() as out_dir:
                    paramspath = op.join(out_dir, "temp.params")
                    trained_net.save_parameters(paramspath)
                    mlflow.log_artifact(paramspath, "model/trained_net_params")
                    uri = mlflow.get_artifact_uri()
                    _LOGGER.info(f"Artifact saved in: {uri}/model/trained_net_params")

                registered_model_name = (
                    job_cfg["run_params"]["registered_model_name"]
                    if (job_cfg["run_params"]["register_model"])
                    else None
                )
                log_model(
                    predictor, "model", registered_model_name=registered_model_name
                )

                if test_data is not None:
                    compute_and_log_metrics(
                        job_cfg=job_cfg,
                        data=test_data,
                        predictor=predictor,
                        calc_eval_metrics=True,
                        ts_error_file_name=TRAIN_TS_ERROR_FILE_NAME,
                    )

                mlflow.set_tag("train_status", "FINISHED")
                return predictor
            except Exception as e:
                mlflow.set_tag("train_status", "FAILED")
                exception = e

    if exception is not None:
        raise exception
