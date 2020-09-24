import gzip
from pathlib import Path

import pandas as pd
import ujson as json
import yaml
from gluonts.dataset.common import (
    BasicFeatureInfo,
    CategoricalFeatureInfo,
    MetaData,
    TrainDatasets,
    serialize_data_entry,
)

from ts_forecast.core.dependencies.containers import Gateways
from ts_forecast.core.utils.common import normalize_dict
from ts_forecast.core.utils.dataset import FSFileDataset


def get_csv_from_s3(path):
    with Gateways.tld_s3().open(path, "rb") as f:
        return pd.read_csv(f).drop(columns=["Unnamed: 0"], errors="ignore")


def categ_feature_info(ds, var_name):
    # dynamic cat vars are not supported.
    assert var_name == "static_feat_cat_vars"
    return [
        CategoricalFeatureInfo(name=name, cardinality=card)
        for (name, card) in zip(getattr(ds, var_name), ds.cardinality)
    ]


def basic_feature_info(real_vars):
    return [BasicFeatureInfo(name=name) for name in real_vars]


def dump_line(f, line):
    f.write(json.dumps(line).encode("utf-8"))
    f.write("\n".encode("utf-8"))


def _save_dataset_part(dataset: TrainDatasets, path_str: str, suffix="") -> None:
    """
    Saves an TrainDatasets object to a JSON Lines file.

    Parameters
    ----------
    dataset
        The training datasets.
    path_str
        Where to save the dataset.
    """
    path = Path(path_str)

    (path / "train").mkdir(parents=True, exist_ok=True)
    with gzip.open(path / f"train/data{suffix}.json.gz", "wb") as f:
        for entry in dataset.train:
            dump_line(f, serialize_data_entry(entry))

    if dataset.test is not None:
        (path / "test").mkdir(parents=True, exist_ok=True)
        with gzip.open(path / f"test/data{suffix}.json.gz", "wb") as f:
            for entry in dataset.test:
                dump_line(f, serialize_data_entry(entry))


def save_metadata(path, dds):
    path = Path(path)
    # FIXME: store all relevant parameters
    metadata = MetaData(
        freq="1D",
        target=None,
        feat_static_cat=categ_feature_info(dds, "static_feat_cat_vars"),
        feat_static_real=basic_feature_info(dds.static_feat_real_vars),
        feat_dynamic_cat=[],
        feat_dynamic_real=basic_feature_info(dds.dynamic_feat_real_vars),
        prediction_length=dds.prediction_length,
    )

    (path / "metadata").mkdir(parents=True, exist_ok=True)
    with gzip.open(path / "metadata/metadata.json.gz", "wb") as f:
        dump_line(f, metadata.dict())


# This is meant to called in parallel. so does not write metadata
def save_dataset_part(path, dds, train_ds, test_ds=None, file_suffix=""):
    gluon_dataset = TrainDatasets(train=train_ds, test=test_ds, metadata=None)
    _save_dataset_part(gluon_dataset, path_str=path, suffix=file_suffix)


def load_dataset(path, files_filter=None):
    path = Path(path)

    with gzip.open(path / "metadata/metadata.json.gz", "rb") as f:
        metadata = MetaData(**json.loads(f.read().decode("utf-8")))

    train_ds = FSFileDataset(
        path / "train",
        freq=metadata.freq,
        compression="gzip",
        files_filter=files_filter,
    )
    test_ds = None
    if (path / "test").exists():
        test_ds = FSFileDataset(
            path / "test",
            freq=metadata.freq,
            compression="gzip",
            files_filter=files_filter,
        )

    return TrainDatasets(train=train_ds, test=test_ds, metadata=metadata)


def load_config_from_path(path):
    """Loading a config file from path
    """
    with open(path, "r") as fp:
        cfg = yaml.load(fp)
    return cfg


def dumpy_dict_as_yaml(file_name, dict_obj):
    with open(file_name, "w") as fp:
        yaml.dump(normalize_dict(dict_obj), fp)
