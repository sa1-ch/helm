# Flask-Model-Deployment

### Installation

To start, clone the repo
```
  $ git clone -b feat/flask-model-deployment https://github.com/tigerrepository/MLE-Playground.git
  $ cd MLE-Playground/hpp
```
Create conda env

```
(base)$ conda env create -f env/dep-linux.yml --name hpp-dev
```

Activate created env

```
(base)$ conda activate hpp-dev
(hpp-dev)$ pip install -r requirements.txt
(hpp-dev)$ pip install -e .
```

Train the model - Training should be done atleast once to create pickle file

```
(hpp-dev)$ python ./model/train.py
```

To test the trained model

```
(hpp-dev)$ python ./model/test.py
```

To deploy the model

```
(hpp-dev)$ python app.py
```

Serving URL: http://ec2-public-ip:8080/
