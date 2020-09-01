#  Copyright 2018 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  
#  Licensed under the Apache License, Version 2.0 (the "License").
#  You may not use this file except in compliance with the License.
#  A copy of the License is located at
#  
#      http://www.apache.org/licenses/LICENSE-2.0
#  
#  or in the "license" file accompanying this file. This file is distributed 
#  on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either 
#  express or implied. See the License for the specific language governing 
#  permissions and limitations under the License.

from __future__ import print_function

import argparse
import joblib
import os
import pandas as pd
from io import StringIO

import numpy as np
from xgboost import XGBRegressor
from sklearn.model_selection import cross_validate
from sklearn.metrics import mean_squared_error
import math
from sklearn.metrics import mean_absolute_error
from sagemaker_containers.beta.framework import (
    content_types, encoders, env, modules, transformer, worker)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    # Hyperparameters are described here. In this simple example we are just including one hyperparameter.
    parser.add_argument('--max_depth', type=int, default=None)
    parser.add_argument('--eta', type=float, default=None)
    parser.add_argument('--gamma', type=int, default=None)
    parser.add_argument('--min_child_weight', type=int, default=None)
    parser.add_argument('--subsample', type=float, default=None)
    parser.add_argument('--eval_metric', type=str, default=None)
    parser.add_argument('--objective', type=str, default=None)
    parser.add_argument('--n_estimators', type=int, default=None)
    

    # Sagemaker specific arguments. Defaults are set in the environment variables.
    parser.add_argument('--output-data-dir', type=str, default=os.environ['SM_OUTPUT_DATA_DIR'])
    parser.add_argument('--model-dir', type=str, default=os.environ['SM_MODEL_DIR'])
    parser.add_argument('--train', type=str, default=os.environ['SM_CHANNEL_TRAIN'])
    parser.add_argument('--validation', type=str, default=os.environ['SM_CHANNEL_VALIDATION'])

    args = parser.parse_args()

    # Take the set of files and read them all into a single pandas dataframe
    input_files = [ os.path.join(args.train, file) for file in os.listdir(args.train) ]
    if len(input_files) == 0:
        raise ValueError(('There are no files in {}.\n' +
                          'This usually indicates that the channel ({}) was incorrectly specified,\n' +
                          'the data specification in S3 was incorrectly specified or the role specified\n' +
                          'does not have permission to access the data.').format(args.train, "train"))
    raw_data = [ pd.read_csv(file, header=None, engine="python") for file in input_files ]
    train_data = pd.concat(raw_data)

    # labels are in the first column
    train_y = train_data.iloc[:, 0]
    train_x = train_data.iloc[:, 1:]
    
    clf = XGBRegressor(
        max_depth=args.max_depth, 
        eta=args.eta,
        gamma=args.gamma,
        min_child_weight=args.min_child_weight,
        subsample=args.subsample,
        eval_metric=args.eval_metric,
        objective=args.objective,
        n_estimators=args.n_estimators
    )
    clf_fit = clf.fit(train_x, train_y)
    
    # Input Validation Files
    input_valid_files = [ os.path.join(args.validation, file) for file in os.listdir(args.validation) ]
    if len(input_valid_files) == 0:
        raise ValueError(('There are no test files in {}.\n' +
                          'This usually indicates that the channel ({}) was incorrectly specified,\n' +
                          'the data specification in S3 was incorrectly specified or the role specified\n' +
                          'does not have permission to access the data.').format(args.validation, "validation"))
    raw_valid_data = [ pd.read_csv(file, header=None, engine="python") for file in input_valid_files ]
    validation_data = pd.concat(raw_valid_data)
    
    validation_y = validation_data.iloc[:, 0]
    validation_x = validation_data.iloc[:, 1:]

    # Fit the model
    cv_scores = cross_validate(
        clf, 
        train_x, 
        train_y,
        scoring=["neg_mean_squared_error",'neg_mean_absolute_error'], 
        cv=3
    )
    cv_mse = cv_scores["test_neg_mean_squared_error"]
    cv_mae = cv_scores["test_neg_mean_absolute_error"]
     
    # Calculate Train Metrics
    train_res = clf_fit.predict(train_x)
    train_mae = mean_absolute_error(train_y, train_res)
    train_mse = mean_squared_error(train_y, train_res)
    
    # Calculate Validation Metrics
    validation_res = clf_fit.predict(validation_x)
    validation_mae = mean_absolute_error(validation_y, validation_res)
    validation_mse = mean_squared_error(validation_y, validation_res)
    
    # Log Metric
    for i in cv_mse:
        print(f"CV MSE={i*-1};")
        
    for i in cv_mae:   
        print(f"CV MAE={i*-1};")
        
    print(f"Train MAE={train_mae};")
    print(f"Train MSE={train_mse};")
    print(f"Validation MAE={validation_mae};")
    print(f"Validation MSE={validation_mse};")
        
    # Print the coefficients of the trained classifier, and save the coefficients
    joblib.dump(clf, os.path.join(args.model_dir, "model.joblib"))


def input_fn(input_data, content_type):
    """Parse input data payload
    
    We currently only take csv input. Since we need to process both labelled
    and unlabelled data we first determine whether the label column is present
    by looking at how many columns were provided.
    """
    print(" ********* input_fn *********")
    print(content_type)
   
    if 'text/csv' in content_type:
        s=str(input_data,'utf-8')
        data = StringIO(s) 
        df=pd.read_csv(data, header=None)
        df.columns = [str(int(i)+1) for i in list(df.columns)]
        return df
    else:
        raise ValueError("{} not supported by script!".format(content_type))
        
        
def output_fn(prediction, accept):
    """Format prediction output
    
    The default accept/content-type between containers for serial inference is JSON.
    We also want to set the ContentType or mimetype as the same value as accept so the next
    container can read the response payload correctly.
    """
    print(" ********* output_fn *********")
    if accept == "application/json":
        instances = []
        for row in prediction.tolist():
            instances.append({"features": row})

        json_output = {"instances": instances}

        return worker.Response(json.dumps(json_output), mimetype=accept)
    elif 'text/csv' in accept:
        print(accept)
        return worker.Response(encoders.encode(prediction, accept), mimetype=accept)
    else:
        raise RuntimeException("{} accept type is not supported by this script.".format(accept))

    
def predict_fn(input_data, model):
    """Preprocess input data
    
    We implement this because the default predict_fn uses .predict(), but our model is a preprocessor
    so we want to use .transform().

    The output is returned in the following order:
    
        rest of features either one hot encoded or standardized
    """
    print(" ********* predict_fn *********")
    output = model.predict(input_data)

    return output

        
def model_fn(model_dir):
    """Deserialized and return fitted model
    
    Note that this should have the same name as the serialized model in the main method
    """
    clf = joblib.load(os.path.join(model_dir, "model.joblib"))
    return clf