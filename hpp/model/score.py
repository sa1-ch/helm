import os
from pathlib import Path

import joblib
import pandas as pd

from ioc.di import Core


class HPPModel:
    """
    Predicts the house price based on the incoming features.
    """

    MODULE_PATH = Path(os.path.dirname(os.path.abspath(__file__))).parent

    def __init__(self):
        self.skl_model = joblib.load(os.environ["MODEL_ARTIFACT"])
        self.skl_pipeline = joblib.load(os.environ["PIPELINE_ARTIFACT"])

    def predict(self, feature_values, features_names):
        """
        predicts the house price
        :param feature_values: input data
        :param features_names: features
        :return:
        """
        logger = Core.logger()
        logger.info("Features:" + str(features_names))
        logger.info("Features Values:" + str(feature_values))
        if features_names is not None and len(features_names) > 0:
            housing = pd.DataFrame(data=feature_values, columns=features_names)
        else:
            housing = pd.DataFrame(data=feature_values)

        full_pipeline = self.skl_pipeline
        # tranforming feature values using loaded serialized object
        housing_prepared = full_pipeline.transform(housing)
        return self.skl_model.predict(housing_prepared)
