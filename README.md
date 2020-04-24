***Hyper-Parameter tuning samples ipynb***

**Dataset used**: `from sklearn.datasets import load_boston`

**For more details on Dataset**: https://scikit-learn.org/stable/modules/generated/sklearn.datasets.load_boston.html#sklearn.datasets.load_boston

**Regressor used**: `from sklearn.ensemble import GradientBoostingRegressor`

**`data_and_regressor.py`**: Common util for getting the dataset details.

1. <u>**`scikit-learn skopt`**</u>
    - Install: `pip install scikit-optimize==0.7.4`
    - Sequential Bayesian Optimization
    - Top performer of all
    - Faster convergence
    - Uni-Directional Convergence
    - Refer: `scikit_skopt.ipynb`, includes plot
    - Ranks 1st

2. <u>**`Hyperopt (Sequential)`**</u>
    - Install: `pip install hyperopt==0.2.3`
    - Sequential Bayesian Optimization
    - For paralleliation, MangoDB is needed
    - Second to scikit-learn skopt
    - Refer: `just_hyperopt.ipynb`, includes plot
    - Ranks 2nd

3. <u>**`Ray-Tune Hyperopt`**</u>
    - Install: `pip install hyperopt==0.2.3`
    - Install: `pip install ray==0.8.4`
    - `Ray` enables multiprocessing capability in python
        -- Makes use of the available cores to enable CPU/GPU optimization
        -- Can deploy on `AWS`, `GCP`, `Clusters`, `Local Machine`
        -- Contains a **hyper-parameter-tuning** library `tune`
    - `tune` is a `hyper-parameter-tuning` library
        -- Has many hyper-parameter-tuning modules, including `hyperopt`, `bayesian`, `Population Based Training (PBT)`
        -- Used `ray`s' parallelization to achieve parallelization even with `Bayesian` & `PBT` frameworks
        -- For some reason, not performing well in AWS EC2. But performs well in <u>Local Machine</u> and <u> Google Collab</u>
    - Refer: `ray_hyperopt.ipynb`, includes plot
    - Ranks 2nd


4. <u>**`Ray-Tune Gridsearch`**
    - Brute-Force method of randomly searching through possible parameters
    - `tune` uses `ray`'s parallelization to run all combinations on multi-cores
    - Refer: `ray_grid.ipynb`, includes plot


