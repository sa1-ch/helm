import joblib
import pandas as pd
from transform.hpp_transform import CombinedAttributesAdder
import logging

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s %(name)s %(levelname)s:%(message)s"
)
logger = logging.getLogger(__name__)


class HPPModel:
    """
    Predicts the house price based on the incoming features.
    """

    def __init__(self):
        self.skl_model = joblib.load("../artifacts/model.pkl")
        self.skl_pipeline = joblib.load("../artifacts/pipeline.pkl")

    def predict(self, feature_values, features_names):
        """
        predicts the house price
        :param feature_values: input data
        :param features_names: features
        :return:
        """
        if not features_names is None and len(features_names) > 0:
            housing = pd.DataFrame(data=feature_values, columns=features_names)
        else:
            housing = pd.DataFrame(data=feature_values)

        full_pipeline = self.skl_pipeline
        # tranforming feature values using loaded serialized object
        housing_prepared = full_pipeline.transform(housing)
        return self.skl_model.predict(housing_prepared)
