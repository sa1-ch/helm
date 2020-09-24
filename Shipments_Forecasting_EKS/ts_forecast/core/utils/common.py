import datetime
import logging
import random

import mxnet as mx
import numpy as np
import pandas as pd

from ts_forecast.core.constants.common import DEFAULT_SEED_VALUE

_LOGGER = logging.getLogger(__name__)


def set_seed(seed_value=DEFAULT_SEED_VALUE):
    mx.random.seed(seed_value)
    np.random.seed(seed_value)
    random.seed(seed_value)
    _LOGGER.info(f"seed value set to: {seed_value}")


def normalize_dict(dct):
    out = {}
    for k, v in dct.items():
        if isinstance(v, (datetime.date, pd.Timestamp)):
            v = v.isoformat()
        elif isinstance(v, dict):
            v = normalize_dict(v)
        out[k] = v
    return out
