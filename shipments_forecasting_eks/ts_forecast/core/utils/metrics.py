import numpy as np

from ts_forecast.core.constants.metrics import MAD, MEAN_DEV, WMAPE


def get_actual_pred_diff(y_actual, y_pred, actual_pred_diff=None):
    return actual_pred_diff if actual_pred_diff is not None else y_actual - y_pred


def mad(y_actual, y_pred, actual_pred_diff=None):
    return np.nanmedian(
        np.abs(get_actual_pred_diff(y_actual, y_pred, actual_pred_diff))
    )


def mean_dev(y_actual, y_pred, actual_pred_diff=None):
    return np.nanmean(np.abs(get_actual_pred_diff(y_actual, y_pred, actual_pred_diff)))


def wmape(y_actual, y_pred, actual_pred_diff=None):
    return np.nansum(
        np.abs(get_actual_pred_diff(y_actual, y_pred, actual_pred_diff))
    ) / np.nansum(y_actual)


def get_metrics(y_actual, y_pred):
    actual_pred_diff = y_actual - y_pred

    return {
        MAD: mad(y_actual, y_pred, actual_pred_diff),
        MEAN_DEV: mean_dev(y_actual, y_pred, actual_pred_diff),
        WMAPE: wmape(y_actual, y_pred, actual_pred_diff),
    }
