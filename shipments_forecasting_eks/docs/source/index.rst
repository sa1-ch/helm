`ts_forecast` is a Python package for demand forecasting at ts!


Status
------

`ts_forecast` is under active development.


Installation
------------

`ts_forecast` has complex dependencies and it is recommended to 
`install the conda package manager <https://docs.conda.io/en/latest/miniconda.html>`_
to manage the python environment.

To work with `ts_forecast` source code in development, install from `GitHub`::

    $ git clone https://github.com/tigerrepository/ts-demand-forecasting.git
    $ cd ts-demand-forecasting

From a conda shell, create a development python environment with all required dependencies::

    (base)$ conda env create -f env.yml

The above command should create a python environment `ts-dev` with all dependencies of `ts_forecast`.
The `ts_forecast` package itself can now be installed from the new environment as follows::

    (base)$ conda activate ts-dev
    (tbc-dev)$ pip install -e .

Test installation of the package by importing the package::

    (tbc-dev) python -c "import ts_forecast"


Contents
--------

.. toctree::
    :maxdepth: 2

    user_guide
    developer_guide
    api
