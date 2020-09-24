from ts_forecast.core.constants.common import (
    DEEP_AR_ESTIMATOR,
    DEEP_STATE_ESTIMATOR,
    PROPHET_PREDICTOR,
)

PARENT_RUN = "parent_run"
TRAIN_TASK = "train_task"
SCORE_TASK = "score_task"
SCORE_MERGE_TASK = "score_merge_task"
MERGE_RUN = "merge_run"

LIMIT_MEMORY = "limit_memory"
LIMIT_CPU = "limit_cpu"
REQUEST_MEMORY = "request_memory"
REQUEST_CPU = "request_cpu"


C5_4X_LARGE_DEMAND = "c5-4x-large-demand"
C5_4X_LARGE_SPOT = "c5-4x-large-spot"
T2_2X_LARGE_SPOT = "t2-2x-large-spot"

EXECUTION_MODE_DEV = "dev"
EXECUTION_MODE_PROD = "prod"

DEEP_STATE_NODES = {
    PARENT_RUN: {
        C5_4X_LARGE_SPOT: {
            LIMIT_MEMORY: "2Gi",
            LIMIT_CPU: "1000m",
            REQUEST_MEMORY: "2Gi",
            REQUEST_CPU: "1000m",
        }
    },
    TRAIN_TASK: {
        C5_4X_LARGE_DEMAND: {
            LIMIT_MEMORY: "10Gi",
            LIMIT_CPU: "8000m",
            REQUEST_MEMORY: "10Gi",
            REQUEST_CPU: "8000m",
        }
    },
    SCORE_TASK: {
        C5_4X_LARGE_SPOT: {
            LIMIT_MEMORY: "22Gi",
            LIMIT_CPU: "12000m",
            REQUEST_MEMORY: "22Gi",
            REQUEST_CPU: "12000m",
        }
    },
    SCORE_MERGE_TASK: {
        C5_4X_LARGE_SPOT: {
            LIMIT_MEMORY: "2Gi",
            LIMIT_CPU: "1500m",
            REQUEST_MEMORY: "2Gi",
            REQUEST_CPU: "1500m",
        }
    },
    MERGE_RUN: {
        C5_4X_LARGE_SPOT: {
            LIMIT_MEMORY: "2Gi",
            LIMIT_CPU: "1000m",
            REQUEST_MEMORY: "2Gi",
            REQUEST_CPU: "1000m",
        }
    },
}

DEEP_AR_NODES = {
    PARENT_RUN: {
        C5_4X_LARGE_SPOT: {
            LIMIT_MEMORY: "2Gi",
            LIMIT_CPU: "1000m",
            REQUEST_MEMORY: "2Gi",
            REQUEST_CPU: "1000m",
        }
    },
    TRAIN_TASK: {
        C5_4X_LARGE_SPOT: {
            LIMIT_MEMORY: "2Gi",
            LIMIT_CPU: "2000m",
            REQUEST_MEMORY: "2Gi",
            REQUEST_CPU: "2000m",
        }
    },
    SCORE_TASK: {
        C5_4X_LARGE_SPOT: {
            LIMIT_MEMORY: "2Gi",
            LIMIT_CPU: "1500m",
            REQUEST_MEMORY: "2Gi",
            REQUEST_CPU: "1500m",
        }
    },
    SCORE_MERGE_TASK: {
        C5_4X_LARGE_SPOT: {
            LIMIT_MEMORY: "2Gi",
            LIMIT_CPU: "1500m",
            REQUEST_MEMORY: "2Gi",
            REQUEST_CPU: "1500m",
        }
    },
    MERGE_RUN: {
        C5_4X_LARGE_SPOT: {
            LIMIT_MEMORY: "2Gi",
            LIMIT_CPU: "1000m",
            REQUEST_MEMORY: "2Gi",
            REQUEST_CPU: "1000m",
        }
    },
}

PROPHET_NODES = {
    PARENT_RUN: {
        C5_4X_LARGE_SPOT: {
            LIMIT_MEMORY: "2Gi",
            LIMIT_CPU: "1000m",
            REQUEST_MEMORY: "2Gi",
            REQUEST_CPU: "1000m",
        }
    },
    TRAIN_TASK: {"None": None},
    SCORE_TASK: {
        C5_4X_LARGE_SPOT: {
            LIMIT_MEMORY: "5Gi",
            LIMIT_CPU: "5000m",
            REQUEST_MEMORY: "5Gi",
            REQUEST_CPU: "5000m",
        }
    },
    SCORE_MERGE_TASK: {
        C5_4X_LARGE_SPOT: {
            LIMIT_MEMORY: "2Gi",
            LIMIT_CPU: "1500m",
            REQUEST_MEMORY: "2Gi",
            REQUEST_CPU: "1500m",
        }
    },
    MERGE_RUN: {
        C5_4X_LARGE_SPOT: {
            LIMIT_MEMORY: "2Gi",
            LIMIT_CPU: "1000m",
            REQUEST_MEMORY: "2Gi",
            REQUEST_CPU: "1000m",
        }
    },
}

DEV_NODES = {
    PARENT_RUN: {
        T2_2X_LARGE_SPOT: {
            LIMIT_MEMORY: "2Gi",
            LIMIT_CPU: "2000m",
            REQUEST_MEMORY: "2Gi",
            REQUEST_CPU: "2000m",
        }
    },
    TRAIN_TASK: {
        T2_2X_LARGE_SPOT: {
            LIMIT_MEMORY: "5Gi",
            LIMIT_CPU: "5000m",
            REQUEST_MEMORY: "5Gi",
            REQUEST_CPU: "5000m",
        }
    },
    SCORE_TASK: {
        T2_2X_LARGE_SPOT: {
            LIMIT_MEMORY: "2.5Gi",
            LIMIT_CPU: "3500m",
            REQUEST_MEMORY: "2.5Gi",
            REQUEST_CPU: "3500m",
        }
    },
    SCORE_MERGE_TASK: {
        T2_2X_LARGE_SPOT: {
            LIMIT_MEMORY: "5Gi",
            LIMIT_CPU: "5000m",
            REQUEST_MEMORY: "5Gi",
            REQUEST_CPU: "5000m",
        }
    },
    MERGE_RUN: {
        T2_2X_LARGE_SPOT: {
            LIMIT_MEMORY: "2Gi",
            LIMIT_CPU: "2000m",
            REQUEST_MEMORY: "2Gi",
            REQUEST_CPU: "2000m",
        }
    },
}

NODE_SELECTORS = {
    EXECUTION_MODE_PROD: {
        DEEP_STATE_ESTIMATOR: DEEP_STATE_NODES,
        DEEP_AR_ESTIMATOR: DEEP_AR_NODES,
        PROPHET_PREDICTOR: PROPHET_NODES,
    },
    EXECUTION_MODE_DEV: {
        DEEP_STATE_ESTIMATOR: DEV_NODES,
        DEEP_AR_ESTIMATOR: DEV_NODES,
        PROPHET_PREDICTOR: DEV_NODES,
    },
}
