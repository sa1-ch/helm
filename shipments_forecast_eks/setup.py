from distutils.core import setup

from setuptools import PEP420PackageFinder

setup(
    name="ts_forecast",
    use_scm_version={
        "root": ".",
        "relative_to": __file__,
        "local_scheme": "node-and-timestamp",
        "write_to": "ts_forecast/_version.py",
    },
    version="0.2",
    description="Timeseries Forecasting !",
    author="Tiger Analytics",
    packages=PEP420PackageFinder.find(),
    entry_points={"console_scripts": ["ts-fcast=ts_forecast.scripts.cli:main"]},
)
