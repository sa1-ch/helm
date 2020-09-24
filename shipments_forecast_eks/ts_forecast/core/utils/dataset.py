# Standard library imports
import functools
import gzip
import posixpath as pp
from pathlib import Path
from typing import NamedTuple

import numpy as np
import pandas as pd
import ujson as json
from fsspec.implementations.local import LocalFileSystem
from gluonts.core.exception import GluonTSDataError
from gluonts.dataset.common import (
    DataEntry,
    Dataset,
    Iterator,
    List,
    ProcessDataEntry,
    SourceContext,
)


def load(file_obj):
    for line in file_obj:
        yield json.loads(line)


def dump(objects, file_obj):
    for object_ in objects:
        file_obj.writeline(json.dumps(object_))


class Span(NamedTuple):
    path: Path
    line: int


class Line(NamedTuple):
    content: object
    span: Span


# Slightly adapted version of the code from GluonTS
class JsonLinesFile:
    def __init__(self, path, fs, compression=None, iter_load_all_data=False) -> None:
        self.path = path
        self.fs = fs
        self.compression = compression
        self.iter_load_all_data = iter_load_all_data

    def __iter__(self):
        with self.fs.open(str(self.path)) as jsonl_file:
            # check whether [Gzip or Json] file
            with (
                gzip.open(jsonl_file, mode="rb")
                if (self.compression == "gzip")
                else jsonl_file
            ) as hndle:
                for line_number, raw in enumerate(
                    hndle.readlines() if self.iter_load_all_data else hndle, start=1,
                ):
                    span = Span(path=self.path, line=line_number)
                    try:
                        yield Line(json.loads(raw), span=span)
                    except ValueError:
                        raise GluonTSDataError(
                            f"Could not read json line {line_number}, {raw}"
                        )

    def __len__(self):
        # 1MB
        BUF_SIZE = 1024 ** 2

        if self.compression == "gzip":
            raise NotImplementedError()

        with self.fs.open(str(self.path)) as file_obj:
            read_chunk = functools.partial(file_obj.read, BUF_SIZE)
            return sum(
                chunk.decode("utf-8").count("\n") for chunk in iter(read_chunk, "")
            )


class FSFileDataset(Dataset):
    def __init__(
        self,
        path: Path,
        freq: str,
        one_dim_target: bool = True,
        fs=None,
        compression=None,
        files_filter=None,
        iter_load_all_data=False,
    ) -> None:
        self.path = path
        self.process = ProcessDataEntry(freq, one_dim_target=one_dim_target)
        self.fs = fs or LocalFileSystem()
        self.compression = compression
        self.files_filter = files_filter or (lambda x: x)
        if not self.files():
            raise ValueError(f"no valid file found in {path}")
        self.iter_load_all_data = iter_load_all_data

    def __iter__(self) -> Iterator[DataEntry]:
        for path in self.files():
            for line in JsonLinesFile(
                path,
                fs=self.fs,
                compression=self.compression,
                iter_load_all_data=self.iter_load_all_data,
            ):
                data = self.process(line.content)
                data["source"] = SourceContext(
                    source=line.span.path, row=line.span.line
                )
                yield data

    def __len__(self):
        # ** FIX THIS **
        # Figure out a way to get the total number of timeseries.
        # Ideally we should try not to loop through as it increases latency
        # return sum(
        #    [
        #        len(JsonLinesFile(path, self.fs, compression=self.compression))
        #        for path in self.files()
        #    ]
        # )
        return len(self.files())

    def files(self) -> List[Path]:
        filter_func = self.files_filter
        fpaths = self.fs.glob(pp.join(self.path))
        fpaths = [Path(fpath) for fpath in fpaths if filter_func(fpath)]
        return [fpath for fpath in fpaths if self.is_valid(fpath, self.compression)]

    @classmethod
    def is_valid(cls, path: Path, compression=None) -> bool:
        # TODO: given that we only support json, should we also filter json
        # TODO: in the extension?
        basename = pp.basename(str(path))
        if compression == "gzip":
            return basename.endswith(".json.gz")
        else:
            return basename.endswith(".json")


# FIXME: use cache if performance is an issue
def _mask_func(orig_start_date, num_periods, filter_start_date, filter_end_date, unit):
    ts = pd.date_range(start=orig_start_date, periods=num_periods, freq=unit)
    mask = (ts >= filter_start_date) & (ts < filter_end_date)
    return mask


def time_filter_func(data, start_date=None, end_date=None, unit="D"):
    """ Given a DataEntry dict, filter the timeseries data to the specified data range.
    """
    days = unit[0]
    start = data["start"]
    n_days = len(data["target"])
    end = start + pd.to_timedelta(n_days, unit=days)

    start_date = pd.Timestamp(start_date, freq=unit) or start
    end_date = pd.Timestamp(end_date, freq=unit) or end
    mask = _mask_func(start, n_days, start_date, end_date, unit)

    new_data = {}
    for k, v in data.items():
        if k == "target":
            v = v[mask]
        elif ("dynamic" in k) and (v.shape[1] > 0):
            v = v[:, mask]

        new_data[k] = v

    if mask[0]:
        new_data["start"] = start
    else:
        diff = (np.where(mask[:-1] != mask[1:])[0] + 1)[0] if sum(mask) else 0
        new_data["start"] = start + pd.Timedelta(diff, unit=days)
    new_data["target"] = np.where(new_data["target"] <= 0, 0, new_data["target"])
    return new_data


def minimum_samples_filter(data, min_size):
    return len(data["target"]) > min_size


def item_id_filter(data, valid_set, key_transform=lambda x: x):
    return key_transform(data["item_id"]) in valid_set


class FilteredDataset(Dataset):
    def __init__(
        self, ds, transform_func=None, pre_filter_func=None, post_filter_func=None,
    ):
        self.ds = ds
        self.pre_filter_func = pre_filter_func or (lambda x: True)
        self.post_filter_func = post_filter_func or (lambda x: True)
        self.transform_func = transform_func or (lambda x: x)

    def __iter__(self) -> Iterator[DataEntry]:
        pre_filter_func = self.pre_filter_func
        post_filter_func = self.post_filter_func
        transform_func = self.transform_func
        for data in self.ds:
            if not pre_filter_func(data):
                continue

            trans_data = transform_func(data)

            if not post_filter_func(trans_data):
                continue

            yield trans_data

    def __len__(self):
        return len(self.ds)
