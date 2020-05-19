import pandas as pd
import numpy as np
from sklearn.model_selection import StratifiedShuffleSplit
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GridSearchCV
import joblib
import os
from transform.hpp_transform import CombinedAttributesAdder
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.metrics import mean_squared_error
import logging

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s %(name)s %(levelname)s:%(message)s"
)
logger = logging.getLogger(__name__)


def split_data(input_df):
    """
    strata data split into train test

    :param input_df: input data to split
    :return: train and test dataframe
    """
    split = StratifiedShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    for train_index, test_index in split.split(input_df, input_df["income_cat"]):
        train_set = input_df.loc[train_index]
        test_set = input_df.loc[test_index]
    return train_set, test_set


def load_housing_data(housing_path):
    """
    Loads data in csv file

    :param housing_path: data path
    :return: housing data dataframe
    """
    csv_path = os.path.join(housing_path, "housing.csv")
    return pd.read_csv(csv_path)


def train():
    """
    Trains the RandomForestRegressor with housing data
    It serializes pipeline and model
    """
    housing_path = "datasets/housing/"
    housing = load_housing_data(housing_path)
    # income category column for strat sampling
    housing["income_cat"] = pd.cut(
        housing["median_income"],
        bins=[0.0, 1.5, 3.0, 4.5, 6.0, np.inf],
        labels=[1, 2, 3, 4, 5],
    )
    strata_train_set, strata_test_set = split_data(housing)
    for set_ in (strata_train_set, strata_test_set):
        set_.drop("income_cat", axis=1, inplace=True)
    housing = strata_train_set.drop("median_house_value", axis=1)
    housing_labels = strata_train_set["median_house_value"].copy()
    housing_num = housing.drop("ocean_proximity", axis=1)

    # data cleaning, feature scaling
    num_pipeline = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("attribs_adder", CombinedAttributesAdder()),
            ("std_scaler", StandardScaler()),
        ]
    )

    num_attribs = list(housing_num)
    cat_attribs = ["ocean_proximity"]

    full_pipeline = ColumnTransformer(
        [("num", num_pipeline, num_attribs), ("cat", OneHotEncoder(), cat_attribs),]
    )
    housing_prepared = full_pipeline.fit_transform(housing)
    forest_reg = RandomForestRegressor()
    param_grid = [
        {"n_estimators": [3, 10, 30], "max_features": [2, 4, 6, 8]},
        {"bootstrap": [False], "n_estimators": [3, 10], "max_features": [2, 3, 4]},
    ]
    # hyper parameter tuning using grid search
    grid_search = GridSearchCV(
        forest_reg,
        param_grid,
        cv=5,
        scoring="neg_mean_squared_error",
        return_train_score=True,
    )
    grid_search.fit(housing_prepared, housing_labels)
    final_model = grid_search.best_estimator_
    x_test = strata_test_set.drop("median_house_value", axis=1)
    y_test = strata_test_set["median_house_value"].copy()
    x_test_prepared = full_pipeline.transform(x_test)
    final_predictions = final_model.predict(x_test_prepared)
    final_mse = mean_squared_error(y_test, final_predictions)
    final_rmse = np.sqrt(final_mse)
    logger.info("RMSE:{}".format(str(final_rmse)))
    artifact_path = "../artifacts"
    if not os.path.isdir(artifact_path):
        os.mkdir(artifact_path)
    # saving model and pipeline
    joblib.dump(final_model, "{}/model.pkl".format(artifact_path))
    joblib.dump(full_pipeline, "{}/pipeline.pkl".format(artifact_path))


if __name__ == "__main__":
    train()
