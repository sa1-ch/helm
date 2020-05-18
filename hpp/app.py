import numpy as np
from flask import Flask, request, jsonify, render_template
import joblib
from model.score import HPPModel

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict',methods=['POST'])
def predict():
    feature_values = [x for x in request.form.values()]
    feature_names = ['longitude','latitude','housing_median_age','total_rooms','total_bedrooms','population','households','median_income','ocean_proximity']
    feature_names = np.array(feature_names)
    feature_values = np.array([feature_values])
    print(feature_names)
    print(feature_values)
    hpp = HPPModel()
    pred = hpp.predict(feature_values,feature_names)
    print(pred)
    return render_template('index.html', prediction_text='House price might be $ {}'.format(pred[0]))

if __name__ == "__main__":
    app.run(debug=True)
