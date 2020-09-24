# Copyright 2018 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License").
# You may not use this file except in compliance with the License.
# A copy of the License is located at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# or in the "license" file accompanying this file. This file is distributed
# on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# express or implied. See the License for the specific language governing
# permissions and limitations under the License.

import os
from typing import Callable, Dict, Iterator, List, NamedTuple, Optional

import numpy as np
import pandas as pd
from gluonts.core.component import validated
from gluonts.dataset.common import DataEntry, Dataset
from gluonts.model.forecast import SampleForecast
from gluonts.model.predictor import RepresentablePredictor

try:
    from fbprophet import Prophet
except ImportError:
    Prophet = None

PROPHET_IS_INSTALLED = Prophet is not None

USAGE_MESSAGE = """
Cannot import `fbprophet`.

The `ProphetPredictor` is a thin wrapper for calling the `fbprophet` package.
In order to use it you need to install it using one of the following two
methods:

    # 1) install fbprophet directly
    pip install fbprophet

    # 2) install gluonts with the Prophet extras
    pip install gluonts[Prophet]
"""


def feat_name(i: int) -> str:
    """The canonical name of a feature with index `i`."""
    return f"feat_dynamic_real_{i:03d}"


class ProphetDataEntry(NamedTuple):
    """
    A named tuple containing relevant base and derived data that is
    required in order to call Prophet.
    """

    train_length: int
    prediction_length: int
    start: pd.Timestamp
    target: np.ndarray
    feat_dynamic_real: List[np.ndarray]

    @property
    def prophet_training_data(self) -> pd.DataFrame:
        return pd.DataFrame(
            data={
                **{
                    "ds": pd.date_range(
                        start=self.start,
                        periods=self.train_length,
                        freq=self.start.freq,
                    ),
                    "y": self.target,
                },
                **{
                    feat_name(i): feature[: self.train_length]
                    for i, feature in enumerate(self.feat_dynamic_real)
                },
            }
        )

    @property
    def forecast_start(self) -> pd.Timestamp:
        return self.start + self.train_length * self.start.freq


class suppress_stdout_stderr(object):
    """
    A context manager for doing a "deep suppression" of stdout and stderr in
    Python, i.e. will suppress all print, even if the print originates in a
    compiled C/Fortran sub-function.
       This will not suppress raised exceptions, since exceptions are printed
    to stderr just before a script exits, and after the context manager has
    exited (at least, I think that is why it lets exceptions through).

    """

    def __init__(self):
        # Open a pair of null files
        self.null_fds = [os.open(os.devnull, os.O_RDWR) for x in range(2)]
        # Save the actual stdout (1) and stderr (2) file descriptors.
        self.save_fds = [os.dup(1), os.dup(2)]

    def __enter__(self):
        # Assign the null pointers to stdout and stderr.
        os.dup2(self.null_fds[0], 1)
        os.dup2(self.null_fds[1], 2)

    def __exit__(self, *_):
        # Re-assign the real stdout/stderr back to (1) and (2)
        os.dup2(self.save_fds[0], 1)
        os.dup2(self.save_fds[1], 2)
        # Close the null files
        for fd in self.null_fds + self.save_fds:
            os.close(fd)


class ProphetPredictor(RepresentablePredictor):
    """
    Wrapper around `Prophet <https://github.com/facebook/prophet>`_.

    The `ProphetPredictor` is a thin wrapper for calling the `fbprophet`
    package. In order to use it you need to install the package::

        # you can either install Prophet directly
        pip install fbprophet

        # or install gluonts with the Prophet extras
        pip install gluonts[Prophet]

    Parameters
    ----------
    freq
        Time frequency of the data, e.g. '1H'
    prediction_length
        Number of time points to predict
    prophet_params
        Parameters to pass when instantiating the prophet model.
    init_model
        An optional function that will be called with the configured model.
        This can be used to configure more complex setups, e.g.

        >>> def configure_model(model):
        ...     model.add_seasonality(
        ...         name='weekly', period=7, fourier_order=3, prior_scale=0.1
        ...     )
        ...     return model
    """

    @validated()
    def __init__(
        self,
        freq: str,
        prediction_length: int,
        prophet_params: Optional[Dict] = None,
        init_model: Callable = lambda m: m,
    ) -> None:
        super().__init__(freq=freq, prediction_length=prediction_length)

        if not PROPHET_IS_INSTALLED:
            raise ImportError(USAGE_MESSAGE)

        if prophet_params is None:
            prophet_params = {}

        assert "uncertainty_samples" not in prophet_params, (
            "Parameter 'uncertainty_samples' should not be set directly. "
            "Please use 'num_samples' in the 'predict' method instead."
        )

        self.prophet_params = prophet_params
        self.init_model = init_model

    def predict(
        self, dataset: Dataset, num_samples: int = 100, **kwargs
    ) -> Iterator[SampleForecast]:

        params = self.prophet_params.copy()
        params.update(uncertainty_samples=num_samples)
        params.update(interval_width=0.95)

        for entry in dataset:
            data = self._make_prophet_data_entry(entry)

            forecast_samples = self._run_prophet(data, params)

#             yield SampleForecast(
#                 samples=forecast_samples,
#                 start_date=data.forecast_start,
#                 freq=self.freq,
#                 item_id=str(entry["item_id"]),
#             )
            yield SampleForecast(
                samples=forecast_samples.values,
                start_date=data.forecast_start,
                freq=self.freq,
                item_id=str(entry["item_id"]),
                info= {k:i for i,k in enumerate(forecast_samples.columns)}
            )

    def _run_prophet(self, data: ProphetDataEntry, params: dict) -> np.array:
        """
        Construct and run a :class:`Prophet` model on the given
        :class:`ProphetDataEntry` and return the resulting array of samples.
        """

        prophet = self.init_model(Prophet(**params))

        # Register dynamic features as regressors to the model
        for i in range(len(data.feat_dynamic_real)):
            prophet.add_regressor(feat_name(i))

        with suppress_stdout_stderr():
            prophet.fit(data.prophet_training_data, algorithm="Newton")

        future_df = prophet.make_future_dataframe(
            periods=self.prediction_length, freq=self.freq, include_history=False,
        )

        # Add dynamic features in the prediction range
        for i, feature in enumerate(data.feat_dynamic_real):
            future_df[feat_name(i)] = feature[data.train_length :]

        #prophet_result = prophet.predictive_samples(future_df)

        #return prophet_result["yhat"].T
        return prophet.predict(future_df)

    def _make_prophet_data_entry(self, entry: DataEntry) -> ProphetDataEntry:
        """
        Construct a :class:`ProphetDataEntry` from a regular
        :class:`DataEntry`.
        """

        train_length = len(entry["target"])
        prediction_length = self.prediction_length
        start = entry["start"]
        target = entry["target"]
        feat_dynamic_real = entry.get("feat_dynamic_real", [])

        # make sure each dynamic feature has the desired length
        for i, feature in enumerate(feat_dynamic_real):
            assert len(feature) == train_length + prediction_length, (
                f"Length mismatch for dynamic real-valued feature #{i}: "
                f"expected {train_length + prediction_length}, "
                f"got {len(feature)}"
            )

        return ProphetDataEntry(
            train_length=train_length,
            prediction_length=prediction_length,
            start=start,
            target=target,
            feat_dynamic_real=feat_dynamic_real,
        )
