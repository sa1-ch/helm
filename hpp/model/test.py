from model.score import HPPModel
import numpy as np
import json
import logging

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s %(name)s %(levelname)s:%(message)s"
)
logger = logging.getLogger(__name__)


def test():
    """
    Test the trained model
    """
    input_json_str = """{"longitude":-121.89,"latitude":37.29,
    "housing_median_age":38.0,"total_rooms":1568.0,"total_bedrooms":351.0,
    "population":710.0,"households":339.0,"median_income":2.7042,
    "ocean_proximity":"<1H OCEAN"} """

    input_json = json.loads(input_json_str)
    features = list(input_json.keys())
    x = list(input_json.values())
    feature_names = np.array(list(input_json.keys()))
    x = np.array([list(input_json.values())])
    hpp = HPPModel()
    pred = hpp.predict(x, feature_names)
    logging.info("Predictions:{}".format(str(pred)))


if __name__ == "__main__":
    test()
