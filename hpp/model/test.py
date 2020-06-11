import json
import numpy as np

from ioc.di import Core
from model.score import HPPModel


def test():
    """
    Test the trained model
    """
    logger = Core.logger()
    input_json_str = """
    {"longitude":-121.89,"latitude":37.29,
    "housing_median_age":38.0,"total_rooms":1568.0,"total_bedrooms":351.0,
    "population":710.0,"households":339.0,"median_income":2.7042,
    "ocean_proximity":"<1H OCEAN"}
    """

    input_json = json.loads(input_json_str)
    feature_names = np.array(list(input_json.keys()))
    feature_values = np.array([list(input_json.values())])
    hpp = HPPModel()
    pred = hpp.predict(feature_values, feature_names)
    assert pred[0] > 0, "Wrong Predictions"
    logger.info("Predictions:{}".format(str(pred[0])))


if __name__ == "__main__":
    test()
