import joblib
import pandas as pd
from transform.hpp_transform import CombinedAttributesAdder

class HPPModel():
    def __init__(self):
        self.skl_model = joblib.load('../artifacts/model.pkl')
        self.skl_pipeline = joblib.load('../artifacts/pipeline.pkl')

    def predict(self,X,features_names):
        if not features_names is None and len(features_names)>0:
            housing = pd.DataFrame(data=X,columns=features_names)
        else:
            housing = pd.DataFrame(data=X)

        housing_num = housing.drop("ocean_proximity",axis=1)
        full_pipeline = self.skl_pipeline
        housing_prepared = full_pipeline.transform(housing)
        #print(housing_prepared)
        return self.skl_model.predict(housing_prepared)