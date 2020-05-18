from model.score import HPPModel
import numpy as np


def test():
    input_json_str = """{"longitude":-121.89,"latitude":37.29,"housing_median_age":38.0,"total_rooms":1568.0,"total_bedrooms":351.0,"population":710.0,"households":339.0,"median_income":2.7042,"ocean_proximity":"<1H OCEAN"}"""
    import json
    input_json = json.loads(input_json_str)
    features = list(input_json.keys())
    X = list(input_json.values())
    feature_names = np.array(list(input_json.keys()))
    X = np.array([list(input_json.values())])
    print(feature_names)
    print(X)
    hpp = HPPModel()
    pred = hpp.predict(X,feature_names)
    print("Predictions:"+str(pred))


test()