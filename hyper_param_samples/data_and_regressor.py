import numpy as np
from sklearn.datasets import load_boston
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import cross_val_score
from skopt.space import Integer, Real


def get_data():
    """
        Get Data
    """
    boston = load_boston()
    X, y = boston.data, boston.target
    n_features = X.shape[1]

    return X, y, n_features


def objective(**params):
    """
        Function to minimize
    """
    reg = GradientBoostingRegressor(n_estimators=50, random_state=0)
    reg.set_params(**params)

    return -np.mean(
        cross_val_score(reg, X, y, cv=5, n_jobs=-1, scoring="neg_mean_absolute_error")
    )

