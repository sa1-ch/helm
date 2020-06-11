import numpy as np
from flask import Flask, request, render_template

from ioc.di import Core
from model.score import HPPModel



def create_app():
    flask_app = Flask(__name__)
    return flask_app

app = create_app()

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/predict", methods=["POST"])
def predict():
    """
     predict api called
    """
    logger = Core.logger()
    # creating feature values
    feature_values = [x for x in request.form.values()]
    feature_names = [
        "longitude",
        "latitude",
        "housing_median_age",
        "total_rooms",
        "total_bedrooms",
        "population",
        "households",
        "median_income",
        "ocean_proximity",
    ]
    feature_names = np.array(feature_names)
    feature_values = np.array([feature_values])
    logger.info("Features:{}".format(str(feature_names)))
    logger.info("Features Values:{}".format(str(feature_values)))
    hpp = HPPModel()
    predictions = hpp.predict(feature_values, feature_names)
    logger.info("Predictions:{}".format(str(predictions)))
    return render_template(
        "index.html",
        prediction_text="House price might be $ {}".format(predictions[0])
    )


#if __name__ == "__main__":
#    app.run(debug=True, host='0.0.0.0', port=8080)
