import numpy as np

# metrics' names
MAD = "mad"
MEAN_DEV = "mean_dev"
WMAPE = "wmape"

# metrics calculation type
AGG_METRICS = [("avg", np.nanmean)]

TRAIN_TS_ERROR_FILE_NAME = "train_ts_error_list"
SCORE_TS_ERROR_FILE_NAME = "score_ts_error_list"

ITEM_LEVEL_METRICS_NAME = "item_level_metrics"

TS_PERIOD_LEVEL_MERGED_NAME = "ts_period_level_merged"
