## Project Location

ts_forecast has complex dependencies and it is recommended to install the conda package manager to manage the python environment.

To work with `Shipments_Forecasting` source code in development, install from GitHub:
```bash
  $ git clone https://github.com/tigerrepository/Shipments_Forecasting
  $ cd Shipments_Forecasting
```

### Directory Structure
```html
. --------------------> (README.md) - Contains details about ******* Project-Structure *******, Developer-Instructions
├── configs
├── deploy
│   ├── airflow
│   ├── container ----> (README.md) - Contains details about Docker-Images Remove/Build/Push to ECR
|   ├── eks ----------> (README.md) - Contains details about eks resource YMLs
│   ├── terraform  ---> (README.md) - Contains details about terraform, terragrunt scripts
|   └── --------------> (README.md) - ******* Contains Deployment Architecture & Instructions ******* 
                                      (Please make sure this is run before running any commands from other READMEs)
├── env
│   └── cpu
├── notebooks
├── ts_forecast
│   ├── core
│   │   ├── constants
│   │   ├── dependencies
│   │   ├── model
│   │   └── utils
│   ├── dashboards
│   └── scripts
```
### ---------------------------------------------------------------------------------------------


## Installation

### Developer Installation

From a `conda` shell, create a development python environment with all required dependencies:
```bash
(base)$ conda env create -f env/cpu/py3-master.yml -n ts-dev
```

*NOTE* If installing on `windows` OS, use
```bash
(base)$ conda env create -f env/cpu/py3-master-windows.yml -n ts-dev
```

The above command should create a python environment `ts-dev` with all dependencies of `Shipments_Forecasting`. The `Shipments_Forecasting` package itself can now be installed from the new environment as follows:
```bash
(base)$ conda activate ts-dev

(ts-dev)$ pip install -e .

(ts-dev)$ pre-commit install
(ts-dev)$ pre-commit run --all-files # One-Time run and make sure ALL ARE PASSED.
```

Test installation of the package by importing the package:
```bash
(ts-dev) python -c "import Shipments_Forecasting"
```

## Starting the Jupyter notebooks

All the example notebooks are available under the `notebooks` folder at the root folder of the cloned repository. You can launch a jupyter notebook/lab instance to work with the notebooks in the folder. 

To run a jupyter server that can be accessed outside of the server (e.g your browser on AWS workspace), do the following:
```bash
(ts-dev) jupyter lab --ip 0.0.0.0 --port 8082 --NotebookApp.token='' --NotebookApp.password='' --no-browser
```

The jupyter server can accessed by opening `http://<server-ip>:8082/lab`


## Getting Started

Once you have access to a working jupyter server with the development environment, you can find example notebooks in the root folder of the repository and should be accessible from jupyter lab from the file-browser pane.

----------------------------------------------------
## cli runs

#### 1. **deepstate* - `Parent task run`, `Train task run`, `Score task run`, `Merge child runs`

**Non-Hyper-Parameter runs**
```bash
    ts-fcast -c configs/dev.yml -cd file parent-run -i configs/fulltrain_deepstate.yml -id file -dg dag_deepstate_03

    ts-fcast -c configs/dev.yml -cd file train -i configs/fulltrain_deepstate.yml -id file -dg dag_deepstate_03
    ts-fcast -c configs/dev.yml -cd file score -i configs/fulltrain_deepstate.yml -id file -dg dag_deepstate_03
    ts-fcast -c configs/dev.yml -cd file merge-score-run -i configs/fulltrain_deepstate.yml -id file -dg dag_deepstate_03

    ts-fcast -c configs/dev.yml -cd file merge-run -i configs/fulltrain_deepstate.yml -id file -dg dag_deepstate_03
```

**Hyper-Parameter runs**
```bash
    ts-fcast -c configs/dev.yml -cd file hyper-run -i configs/fulltrain_deepstate.yml -id file -dg dag_deepstate_04
```


#### 2. **deepar* - `Parent task run`, `Train task run`, `Score task run`, `Merge child runs`

**Non-Hyper-Parameter runs**
```bash
    ts-fcast -c configs/dev.yml -cd file parent-run -i configs/fulltrain_deepar.yml -id file -dg dag_deepar_01

    ts-fcast -c configs/dev.yml -cd file train -i configs/fulltrain_deepar.yml -id file -dg dag_deepar_01
    ts-fcast -c configs/dev.yml -cd file score -i configs/fulltrain_deepar.yml -id file -dg dag_deepar_01
    ts-fcast -c configs/dev.yml -cd file merge-score-run -i configs/fulltrain_deepar.yml -id file -dg dag_deepar_01

    ts-fcast -c configs/dev.yml -cd file merge-run -i configs/fulltrain_deepar.yml -id file -dg dag_deepar_01
```

**Hyper-Parameter runs**
```bash
    ts-fcast -c configs/dev.yml -cd file hyper-run -i configs/fulltrain_deepar.yml -id file -dg dag_deepar_02
```


#### 3. **prophet* - `Parent task run`, `Score task run`, `Merge child runs`

**Non-Hyper-Parameter runs**
```bash
    ts-fcast -c configs/dev.yml -cd file parent-run -i configs/fulltrain_prophet.yml -id file -dg dag_prophet_02

    ts-fcast -c configs/dev.yml -cd file score -i configs/fulltrain_prophet.yml -id file -dg dag_prophet_02
    ts-fcast -c configs/dev.yml -cd file merge-score-run -i configs/fulltrain_prophet.yml -id file -dg dag_prophet_02
    
    ts-fcast -c configs/dev.yml -cd file merge-run -i configs/fulltrain_prophet.yml -id file -dg dag_prophet_02
```

**Hyper-Parameter runs**
```bash
    ts-fcast -c configs/dev.yml -cd file hyper-run -i configs/fulltrain_prophet.yml -id file -dg dag_prophet_03
```


### Docker runs

#### Build docker image

From the root folder of the repository, run:
```bash
    sudo docker build -f deploy/container/Dockerfile -t ts-app .
```

----------------------------------------------------
## Docker runs

### Start docker deamon, `sudo service docker start`, if not started
### Make sure aws credentials are set

#### 1. Run parent script
```bash
    sudo docker run \
         --net=host \
         --env-file=$HOME/.aws/credentials \
         --name=ts_app_parent_run \
         --cpus=2  --memory=2G \
         -v $PWD/configs/dev.yml:/root/config/cfg.yml \
         -v $PWD/configs/fulltrain.yml:/root/config/train.yml \
         ts-app \
         parent-run -i /root/config/train.yml -id file -dg dag_id_1
```


#### 2. Run Train script

From the root folder of the repository, run:
```bash
    sudo docker run \
         --net=host \
         --env-file=$HOME/.aws/credentials \
         --name=ts_app_train \
         --cpus=5  --memory=5G \
         -v $PWD/configs/dev.yml:/root/config/cfg.yml \
         -v $PWD/configs/fulltrain.yml:/root/config/train.yml \
         ts-app \
         train -i /root/config/train.yml -id file -dg dag_id_1
```

#### 3. Run Score script

From the root folder of the repository, run:
```bash
    sudo docker run \
         --net=host \
         --env-file=$HOME/.aws/credentials \
         --name=ts_app_score \
         -v $PWD/configs/dev.yml:/root/config/cfg.yml \
         -v $PWD/configs/fulltrain.yml:/root/config/train.yml \
         ts-app \
         score -i /root/config/train.yml -id file -dg dag_id_1
```

#### 4. Run Merge childs runs script
```bash
    sudo docker run \
         --net=host \
         --env-file=$HOME/.aws/credentials \
         --name=ts_app_merge_run \
         --cpus=2  --memory=2G \
         -v $PWD/configs/dev.yml:/root/config/cfg.yml \
         -v $PWD/configs/fulltrain.yml:/root/config/train.yml \
         ts-app \
         merge-score-run -i /root/config/train.yml -id file -dg dag_id_1
```

#### 5. Run Merge childs runs script
```bash
    sudo docker run \
         --net=host \
         --env-file=$HOME/.aws/credentials \
         --name=ts_app_merge_run \
         --cpus=2  --memory=2G \
         -v $PWD/configs/dev.yml:/root/config/cfg.yml \
         -v $PWD/configs/fulltrain.yml:/root/config/train.yml \
         ts-app \
         merge-run -i /root/config/train.yml -id file -dg dag_id_1
```

----------------------------------------------------