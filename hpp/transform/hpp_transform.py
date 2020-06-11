
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin

ROOMS_IX, BEDROOMS_IX, POPULATION_IX, HOUSEHOLDS_IX = 3, 4, 5, 6


class CombinedAttributesAdder(BaseEstimator, TransformerMixin):
    """
    CombinedAttributesAdder is the transformer that adds some new features to
    existing data
   
   """

    def __init__(self, add_bedrooms_per_room=True):  # no *args or **kargs
        self.add_bedrooms_per_room = add_bedrooms_per_room

    def fit(self, input_df, input_y=None):
        return self  # nothing else to do

    def transform(self, input_df):
        """
        Transforms the data by adding some new features
        
        """
        rooms_per_household = input_df[:, ROOMS_IX] / input_df[:, HOUSEHOLDS_IX]
        population_per_household = input_df[:, POPULATION_IX] / input_df[:,
                                                                HOUSEHOLDS_IX]
        if self.add_bedrooms_per_room:
            bedrooms_per_room = input_df[:, BEDROOMS_IX] / input_df[:, ROOMS_IX]
            return np.c_[
                input_df, rooms_per_household, population_per_household, bedrooms_per_room
            ]

        else:
            return np.c_[
                input_df, rooms_per_household, population_per_household]

