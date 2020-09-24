""" Helper functions to load/save GluonTS models
"""
import gzip
import json
import logging
import os
import os.path as op
import tempfile
from pathlib import Path

import gluonts
import mlflow
import mlflow.tracking
from gluonts.dataset.common import MetaData, TrainDatasets
from gluonts.evaluation import Evaluator
from gluonts.evaluation.backtest import make_evaluation_predictions
from gluonts.model.predictor import ParallelizedPredictor
from mlflow import pyfunc
from mlflow.models import Model
from mlflow.tracking.artifact_utils import _download_artifact_from_uri
from mlflow.utils.model_utils import _get_flavor_configuration

import ts_forecast
from ts_forecast.core.dependencies.containers import Gateways
from ts_forecast.core.utils.dataset import FSFileDataset
from ts_forecast.core.utils.mlflow import get_artifacts_uri

_LOGGER = logging.getLogger(__name__)

FLAVOR_NAME = "GluonTS"
MODEL_SUBPATH = "model"


def save_model(gluon_model, path, conda_env=None, mlflow_model=Model()):
    path = os.path.abspath(path)
    if os.path.exists(path):
        raise Exception("Path '{}' already exists".format(path))

    model_data_subpath = MODEL_SUBPATH
    model_path = os.path.join(path, model_data_subpath)
    os.makedirs(model_path)
    gluon_model.serialize(Path(model_path))

    #   conda_env_subpath = "conda.yaml"
    #   if conda_env is None:
    #       conda_env = DEFAULT_CONDA_ENV
    #   elif not isinstance(conda_env, dict):
    #       with open(conda_env, "r") as f:
    #           conda_env = yaml.safe_load(f)
    #   with open(os.path.join(path, conda_env_subpath), "w") as f:
    #       yaml.safe_dump(conda_env, stream=f, default_flow_style=False)

    pyfunc.add_to_model(
        mlflow_model,
        loader_module="ts_forecast.core.utils.gluon",
        data=model_data_subpath,
    )
    mlflow_model.add_flavor(
        FLAVOR_NAME, gluonts_version=gluonts.__version__, data=model_data_subpath,
    )
    mlflow_model.save(os.path.join(path, "MLmodel"))


def log_model(gluon_model, artifact_path, conda_env=None, **kwargs):
    Model.log(
        artifact_path=artifact_path,
        flavor=ts_forecast.core.utils.gluon,
        gluon_model=gluon_model,
        conda_env=conda_env,
        **kwargs,
    )


def _load_model(model_file):
    from gluonts.model.estimator import Predictor
    import mxnet as mx

    return Predictor.deserialize(Path(model_file), mx.cpu())


def load_model(path, run_id=None):
    if run_id is not None:
        path = mlflow.tracking.utils._get_model_log_dir(model_name=path, run_id=run_id)
    path = os.path.abspath(path)
    flavor_conf = _get_flavor_configuration(model_path=path, flavor_name=FLAVOR_NAME)
    _LOGGER.info(f"Loading model with flavor_conf: {flavor_conf}")
    # Flavor configurations for models saved in MLflow version <= 0.8.0 may not contain
    # `data` key; in this case, we assume the model artifact path to be `model.h5`
    gluon_model_artifacts_path = os.path.join(
        path, flavor_conf.get("data", MODEL_SUBPATH)
    )
    return _load_model(model_file=gluon_model_artifacts_path)


class _GluonTsModelWrapper:
    def __init__(self, gluon_model):
        self.gluon_model = gluon_model

    def predict(self, data):
        return self.gluon_model.predict(data)


def _load_pyfunc(model_file):
    """
    Load PyFunc implementation. Called by ``pyfunc.load_pyfunc``.
    """
    m = _load_model(model_file)
    return _GluonTsModelWrapper(m)


def get_sequential_parallel_predictor(eval_method, predictor, job_cfg):
    if eval_method == "sequential":
        pred = predictor
    elif eval_method == "parallel":
        pred = ParallelizedPredictor(
            predictor,
            num_workers=job_cfg["run_params"]["evaluation"]["num_workers"],
            chunk_size=job_cfg["run_params"]["evaluation"]["chunk_size"],
        )
    else:
        raise ValueError(f"Unsupported evaluation method : {eval_method}")
    return pred


def get_predictor(job_cfg, data):
    uri = os.path.join(get_artifacts_uri(job_cfg, data), "model")
    with tempfile.TemporaryDirectory() as out_dir:
        _download_artifact_from_uri(uri, output_path=out_dir)
        predictor = load_model(op.join(out_dir) + "/model")

    pred = get_sequential_parallel_predictor(
        eval_method=job_cfg["run_params"]["evaluation"]["eval"],
        predictor=predictor,
        job_cfg=job_cfg,
    )
    return pred


def get_forecast_values(job_cfg, data, predictor=None):
    """Gets forecast values for a given
       job_config, data and predictor

    Arguments:
        job_cfg - Dictionary containing job config
        data - Data for which the forecast to be done
        predictor - predictor with which the forecast to be done

    Returns:
        generator -- Forecast values
        generator -- Actual values
    """
    if predictor is None:
        predictor = get_predictor(job_cfg=job_cfg, data=data)

    forecast_it, ts_it = make_evaluation_predictions(
        dataset=data,  # dataset
        predictor=predictor,  # predictor
        num_samples=job_cfg["run_params"]["evaluation"][
            "num_samples"
        ],  # number of sample paths we want for evaluation
    )

    return forecast_it, ts_it


def get_evaluation_metrics(forecast_list, ts_list):
    """Returns evaluation metrics for a given set of
       forecast and actual values

    Arguments:
        forecast_list {list} -- Forecast values
        ts_list {list} -- Actual Values

    Returns:
        dict -- Aggregated evaluation metrics
        pd.Dataframe -- Evlauation metrics at the item level
    """
    evaluator = Evaluator(quantiles=[0.5])
    agg_metrics, item_metrics = evaluator(
        iter(ts_list), iter(forecast_list), num_series=len(forecast_list)
    )

    return agg_metrics, item_metrics


def load_gluon_dataset(path, cfg, files_filter=None, iter_load_all_data=False):
    """Loading a GluonDataset from S3. cfg here represents the credentials config
    """
    with Gateways.tld_s3().open(path + "/metadata/metadata.json.gz", "rb") as f:
        metadata = MetaData(
            **json.loads(gzip.GzipFile(fileobj=f).read().decode("utf-8"))
        )

    train_ds = FSFileDataset(
        path + "/data/*",
        fs=Gateways.tld_s3(),
        freq=metadata.freq,
        compression="gzip",
        files_filter=files_filter,
        iter_load_all_data=iter_load_all_data,
    )
    test_ds = None
    return TrainDatasets(train=train_ds, test=test_ds, metadata=metadata)


def load_gluon_dataset_v2(datapath, metadata, cfg, files_filter=None):
    """Loading a GluonDataset from S3. cfg here represents the credentials config
    """
    train_ds = FSFileDataset(
        datapath,
        fs=Gateways.tld_s3(),
        freq=metadata.freq,
        compression="gzip",
        files_filter=files_filter,
    )
    test_ds = None
    return TrainDatasets(train=train_ds, test=test_ds, metadata=metadata)
