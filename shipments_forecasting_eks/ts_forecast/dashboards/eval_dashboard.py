import os
import re
import json
import warnings

import holoviews as hv
import numpy as np
import pandas as pd
import panel as pn
import s3fs
import yaml
from bokeh.core.properties import value
from bokeh.models import (
    Band,
    ColumnDataSource,
    DatetimeTickFormatter,
    HoverTool,
    Legend,
    LinearAxis,
    Range1d,
)
from bokeh.palettes import Spectral5, Spectral6
from bokeh.models.formatters import NumeralTickFormatter
from bokeh.plotting import figure
from bokeh.transform import dodge


def metric_MAPE(y_true, y_pred):
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    y_pred = y_pred[y_true != 0]
    y_true = y_true[y_true != 0]
    return np.mean(np.abs((y_true - y_pred) / y_true))


def metric_MAD(y_true, y_pred):
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    return np.mean(np.abs(y_true - y_pred))


def metric_WMAPE(y_true, y_pred):
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    return np.sum(np.abs(y_true - y_pred)) / sum(y_true)


def metric_Bias(y_true, y_pred):
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    return np.mean(y_true - y_pred)


def metric_NFM(y_true, y_pred):
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    return np.mean((y_pred - y_true) / (y_true + y_pred))


def metric_Tracking_Signal(y_true, y_pred):
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    return np.sum(y_true - y_pred) / np.mean(np.abs((y_true - y_pred)))


warnings.filterwarnings("ignore")
pn.extension()
hv.extension("bokeh")
css = """
.gray_bg {
    background: #F7FFE0 !important;
}
.custom_class .bk-input {
   background-color: #F7FFE0; !important
}
.primary.button button {
  background: #FFA500 !important;
  color: #F7FFE0 !important;
  border-color: #ffffff !important;
}
.story_title_input {
    border: 0 !important;
    background: #3D5366 !important;
    color: #fff !important;
    padding: 0px 5px 0px 5px !important;
    font-weight: bold;
    font-size: 14px !important;
    height: 45px !important;
}
"""
pn.extension(raw_css=[css])


def load_yaml(file):
    with open(file, "r") as fp:
        config = yaml.load(fp, Loader=yaml.SafeLoader)

    return config


package_dir = os.path.dirname(os.path.abspath(__file__))
creds_file = load_yaml(os.path.join(package_dir, "..", "..", "configs/dev.yml"))


class ModelEvaluation:
    def __init__(self):

        # Initialize all components

        # self.metrics_list = ["MAPE", "WMAPE", "MAD", "Bias"]
        self.metrics_list = ["MAPE", "WMAPE", "MAD", "Tracking_Signal"]
        self.percentage_metric = ["MAPE", "WMAPE"]

        # Bins
        self.prediction_dict = {}
        self.metric_bins_dropdown = [
            "None",
            "[0, 20)",
            "[20, 40)",
            "[40, 60)",
            "[60, 80)",
            "[80, ∞)",
        ]
        self.bin_range_mapping = dict(
            zip(
                self.metric_bins_dropdown,
                [None, (0, 20), (20, 40), (40, 60), (60, 80), (80, np.inf)],
            )
        )
        self.bins = pd.IntervalIndex.from_breaks(
            list(np.arange(0, 81, 20)) + [np.inf], closed="left"
        )

        # Headers
        self.dash_heading = pn.pane.Markdown(
            """<h1> Model Evaluation Dashboard""", align="center"
        )
        self.forecast_heading = pn.pane.Markdown(
            """<h2> Forecast Plot & Feature Importance""",
            align="center",
            css_classes=["story_title_input"],
        )
        self.crosstable_heading = pn.pane.Markdown(
            """<h2> Cross Table""", align="center", css_classes=["story_title_input"]
        )
        self.metrics_heading = pn.pane.Markdown(
            """<h2> Metrics Distribution""",
            align="center",
            css_classes=["story_title_input"],
        )
        self.models_summary_heading = pn.pane.Markdown(
            """<h2> Models Summary""",
            align="center",
            css_classes=["story_title_input"],
        )

        # Progress bar
        self.progress = pn.widgets.Progress(
            name="Calculating metrics",
            value=0,
            width=250,
            height=40,
            disabled=True,
            margin=(23, 10, 30, 0),
        )
        self.progress_text = pn.widgets.StaticText(margin=(30, 10, 0, 0))

        # Experiment Name input
        # self.experiment_name = pn.widgets.TextInput(
        #    width=300, height=40, margin=(5, 10, 30, 0)
        # )
        self.experiment_name = pn.widgets.MultiChoice(
            width=300, name="Experiments", max_items=1,
        )
        self.experiment_name.options = [
            i.split("/")[-1]
            for i in s3fs.S3FileSystem().ls(
                "s3://tiger-mle-tg/inputs/auto-gluonts-data"
            )
            if not i.split("/")[-1].endswith(".json")
        ]
        self.experiment_name_btn = pn.widgets.Button(
            name="Get Data",
            height=42,
            width=80,
            margin=(23, 10, 30, 0),
            button_type="primary",
            css_classes=["primary", "button"],
        )
        self.experiment_name_btn.on_click(self.load_data)

        # TAB
        self.ts_level_tab = pn.Tabs()

        # - Start Dates Dropdown
        self.start_date = pn.widgets.Select(
            width=200,
            height=60,
            name="Forecast Start Date",
            margin=20,
            css_classes=["custom_class"],
        )
        self.start_date.param.watch(self.handle_start_date_selection, "value")

        self.start_date_agg = pn.widgets.Select(
            width=200,
            height=60,
            name="Forecast Start Date",
            margin=20,
            css_classes=["custom_class"],
        )
        self.start_date_agg.param.watch(self.handle_start_date_selection_agg, "value")

        self.cross_start_date = pn.widgets.Select(
            width=200,
            height=60,
            name="Forecast Start Date",
            margin=20,
            css_classes=["custom_class"],
        )
        self.cross_start_date.param.watch(
            self.handle_cross_start_date_selection, "value"
        )

        self.cross_start_date_agg = pn.widgets.Select(
            width=200,
            height=60,
            name="Forecast Start Date",
            margin=20,
            css_classes=["custom_class"],
        )
        self.cross_start_date_agg.param.watch(
            self.handle_cross_start_date_selection_agg, "value"
        )

        # - End Dates Dropdown
        self.end_date = pn.widgets.Select(
            width=200,
            height=60,
            name="Forecast End Date",
            margin=20,
            css_classes=["custom_class"],
        )
        self.end_date_agg = pn.widgets.Select(
            width=200,
            height=60,
            name="Forecast End Date",
            margin=20,
            css_classes=["custom_class"],
        )
        self.cross_end_date = pn.widgets.Select(
            width=200,
            height=60,
            name="Forecast End Date",
            margin=20,
            css_classes=["custom_class"],
        )
        self.cross_end_date_agg = pn.widgets.Select(
            width=200,
            height=60,
            name="Forecast End Date",
            margin=20,
            css_classes=["custom_class"],
        )

        # Metrics Distribution button
        self.metrics_dist_btn = pn.widgets.Button(
            name="Plot",
            height=40,
            width=80,
            margin=38,
            button_type="primary",
            css_classes=["primary", "button"],
        )
        self.metrics_dist_btn.on_click(self.get_metrics_dist_plot)

        self.metrics_dist_plot_list = []
        for metric in self.metrics_list:
            exec(
                f"self.{metric.lower()}_dist_plot = \
                pn.pane.Bokeh(name='{metric} Dist Plot')"
            )
            self.metrics_dist_plot_list.append(eval(f"self.{metric.lower()}_dist_plot"))

        # Aggregate Metrics Distribution button
        self.metrics_dist_btn_agg = pn.widgets.Button(
            name="Plot",
            height=40,
            width=80,
            margin=38,
            button_type="primary",
            css_classes=["primary", "button"],
        )
        self.metrics_dist_btn_agg.on_click(self.get_metrics_dist_plot_agg)

        self.metrics_dist_plot_list_agg = []
        for metric in self.metrics_list:
            exec(
                f"self.{metric.lower()}_dist_plot_agg = \
                pn.pane.Bokeh(name='{metric} Dist Plot')"
            )
            self.metrics_dist_plot_list_agg.append(
                eval(f"self.{metric.lower()}_dist_plot_agg")
            )

        # Forecast Plot
        self.forecast_plot = pn.pane.Bokeh(name="forecast plot")
        self.waterfall_plot = pn.pane.Bokeh(name="Waterfall Chart")
        self.metrics_df = pn.widgets.DataFrame(
            name="Metrics Dataframe",
            height=0,
            width=800,
            fit_columns=True,
            align="start",
        )

        # Aggregate Forecast Plot
        self.forecast_plot_agg = pn.pane.Bokeh(name="forecast plot")
        self.waterfall_plot_agg = pn.pane.Bokeh(name="Waterfall Chart")
        self.metrics_df_agg = pn.widgets.DataFrame(
            name="Metrics Dataframe",
            height=0,
            width=800,
            fit_columns=True,
            align="start",
        )

        # ----------------------------- Cross Tables among Metrics ------------

        self.x_axis_metrics = pn.widgets.Select(
            options=self.metrics_list,
            width=200,
            name="Y-Axis",
            value="",
            margin=20,
            height=60,
            css_classes=["custom_class"],
        )
        self.y_axis_metrics = pn.widgets.Select(
            options=self.metrics_list,
            width=200,
            name="X-Axis",
            value="",
            margin=20,
            height=60,
            css_classes=["custom_class"],
        )

        self.crosstab_btn = pn.widgets.Button(
            name="Get",
            height=40,
            width=80,
            margin=38,
            button_type="primary",
            css_classes=["primary", "button"],
        )
        self.crosstab_btn.on_click(self.get_cross_table)
        self.crosstab_df = pn.widgets.DataFrame(
            name="Metrics Dataframe", height=0, width=800, fit_columns=True
        )

        self.model_metrics_df = pn.widgets.DataFrame(align="center", height=0)
        self.model_metrics_df_agg = pn.widgets.DataFrame(align="center", height=0)

        # Aggregate TAB
        self.x_axis_metrics_agg = pn.widgets.Select(
            options=self.metrics_list,
            width=200,
            name="Y-Axis",
            value="",
            margin=20,
            height=60,
            css_classes=["custom_class"],
        )
        self.y_axis_metrics_agg = pn.widgets.Select(
            options=self.metrics_list,
            width=200,
            name="X-Axis",
            value="",
            margin=20,
            height=60,
            css_classes=["custom_class"],
        )
        self.crosstab_btn_agg = pn.widgets.Button(
            name="Get",
            height=40,
            width=80,
            margin=38,
            button_type="primary",
            css_classes=["primary", "button"],
        )
        self.crosstab_btn_agg.on_click(self.get_cross_table_agg)
        self.crosstab_df_agg = pn.widgets.DataFrame(
            name="Metrics Dataframe", height=0, width=800, fit_columns=True
        )

        self.basic_granularity = pn.widgets.Select(
            width=200,
            name="Select Hierarchy",
            margin=10,
            height=60,
            css_classes=["custom_class"],
        )

        self.basic_model_selection = pn.widgets.Select(
            width=200,
            name="Select Model",
            margin=10,
            height=60,
            css_classes=["custom_class"],
        )

        # ------------------------------------ 2nd Tab aggregation ------------
        self.agg_granularity = pn.widgets.MultiChoice(
            width=200, name="Select Hierarchy Aggregation", margin=10,
        )
        self.agg_granularity_btn = pn.widgets.Button(
            name="Get",
            height=42,
            width=80,
            margin=28,
            button_type="primary",
            css_classes=["primary", "button"],
        )

        # Adding filters for granularity
        self.gran_filters_dist_plot = pn.panel(pn.Row())

        # Adding filters for granularity
        self.gran_filters = pn.panel(pn.Row())

        # Selection for IDV, Model and metric bins
        self.idv_cols = pn.widgets.Select(
            width=200,
            name="Independent Variable",
            margin=20,
            height=60,
            css_classes=["custom_class"],
        )

        # Aggregate TAB
        self.idv_cols_agg = pn.widgets.Select(
            width=200,
            name="Independent Variable",
            margin=20,
            height=60,
            css_classes=["custom_class"],
        )

        self.gran_filters_agg = pn.panel(pn.Row())

        self.model_selection = pn.widgets.Select(
            width=200,
            name="Select Model",
            margin=20,
            height=60,
            css_classes=["custom_class"],
        )

        self.model_selection_forecast = pn.widgets.Select(
            width=80,
            name="Select Model",
            margin=20,
            height=60,
            css_classes=["custom_class"],
        )

        self.model_selection_agg = pn.widgets.Select(
            width=200,
            name="Select Model",
            margin=20,
            height=60,
            css_classes=["custom_class"],
        )
        self.model_selection_agg_forecast = pn.widgets.Select(
            width=80,
            name="Select Model",
            margin=20,
            height=60,
            css_classes=["custom_class"],
        )

        self.metric_filters = pn.panel(pn.Row())

        # Aggregated metrics filter
        self.metric_filters_agg = pn.panel(pn.Row())

    def prepare_data(self):

        try:
            with open("../../configs/dev.yml", "r") as fp:
                config = yaml.load(fp, Loader=yaml.SafeLoader)
            bucket = config["credentials"]["tld_s3"]["prefix"].split("s3://")[1]
        except:
            bucket = "tiger-mle-tg"

        idv_path = f"s3://{bucket}/inputs/auto-gluonts-data/{self.experiment_name.value[0] if self.experiment_name.value else ''}"
        path = f"s3://{bucket}/outputs/forecast-results/{self.experiment_name.value[0] if self.experiment_name.value else ''}"

        if s3fs.S3FileSystem().ls(f"{idv_path}/input_variables.json"):

            metadata = json.loads(
                s3fs.S3FileSystem()
                .open(f"{idv_path}/input_variables.json", "rb")
                .read()
            )

            # json_path = 'D:/Forecasting_Accelerator/model_results/input_variables.json'

            # with open(json_path) as f:
            #    metadata = json.load(f)

            # Get from EDA Dashboard
            self.prediction_length = metadata["Forecast window"]
            self.data_freq = metadata["Data frequency"]
            self.test_end_date = metadata["Forecast end date"]
            self.granularity = [
                i[0].upper() + i[1:] for i in metadata["Data granularity"]
            ]
            self.dv_col = metadata["Target variable"]
            self.date_col = metadata["Date variable"]
            self.fdr = metadata["Feat Dynamic Real"]
            dataset_name = metadata["Dataset Name"]

            forecast_start_date = (
                f"FD_{''.join(metadata['Forecast start date'].split('-'))}"
            )
            idv_cols_names = metadata["Feat Dynamic Real"]
            use_cols = [
                "item_id",
                "busidaydt",
                "actual_values",
                "yhat",
                "yhat_lower",
                "yhat_upper",
            ]
            rem_cols = [
                "last_train_date",
                "type",
                "registered_model_name",
                "version",
                "yhat_0.50_left",
                "yhat_0.50_right",
                "yhat_0.95_left",
                "yhat_0.95_right",
            ]
            self.gran_cols = metadata["Data granularity"]

            model_fls = [
                i
                for i in s3fs.S3FileSystem().ls(idv_path)
                if i.split("/")[-1] == "model_evaluation_dashboard.pkl"
            ]

            if model_fls:
                with s3fs.S3FileSystem().open(model_fls[0], "rb",) as f:
                    self.data = pd.read_pickle(f)
            else:
                c = 0
                model_map = {}
                if s3fs.S3FileSystem().ls(path):
                    for i, model_dag in enumerate(s3fs.S3FileSystem().ls(path)):

                        if s3fs.S3FileSystem().ls(
                            f"s3://{model_dag}/{forecast_start_date}/{dataset_name}/ts_period_level_merged.csv"
                        ):
                            with s3fs.S3FileSystem().open(
                                f"s3://{model_dag}/{forecast_start_date}/{dataset_name}/ts_period_level_merged.csv",
                                "rb",
                            ) as f:
                                df = pd.read_csv(f)

                            if not c:
                                idv_cols = [
                                    col
                                    for col in df.columns
                                    if col.startswith("feat_dynamic_real")
                                    and not re.search("lower|upper", col)
                                ]
                                extra_idv = [
                                    col
                                    for col in df.columns
                                    if col not in use_cols + rem_cols
                                    and not re.search(
                                        "lower|upper|feat_dynamic_real", col
                                    )
                                ]
                                idv_cols_name = [
                                    f"{col}_model_{c+1}" for col in idv_cols_names
                                ]
                                if idv_cols:
                                    df = df[use_cols + idv_cols + extra_idv]
                                    extra_idv = [
                                        f"{col}_model_{c+1}" for col in extra_idv
                                    ]
                                    df.columns = (
                                        [
                                            "item_id",
                                            self.date_col,
                                            "Actual_test",
                                            f"Predicted_model_{c+1}",
                                            f"lower_bound_model_{c+1}",
                                            f"upper_bound_model_{c+1}",
                                        ]
                                        + idv_cols_name
                                        + extra_idv
                                    )
                                else:
                                    temp_use_cols = [
                                        "item_id",
                                        "busidaydt",
                                        "actual_values",
                                        "yhat",
                                        "yhat_0.95_left",
                                        "yhat_0.95_right",
                                    ]
                                    df = df[temp_use_cols + idv_cols + extra_idv]
                                    df.columns = [
                                        "item_id",
                                        self.date_col,
                                        "Actual_test",
                                        f"Predicted_model_{c+1}",
                                        f"lower_bound_model_{c+1}",
                                        f"upper_bound_model_{c+1}",
                                    ]
                                model_df = df
                            else:
                                idv_cols = [
                                    col
                                    for col in df.columns
                                    if col.startswith("feat_dynamic_real")
                                    and not re.search("lower|upper", col)
                                ]
                                extra_idv = [
                                    col
                                    for col in df.columns
                                    if col not in use_cols + rem_cols
                                    and not re.search(
                                        "lower|upper|feat_dynamic_real", col
                                    )
                                ]
                                idv_cols_name = [
                                    f"{col}_model_{c+1}" for col in idv_cols_names
                                ]
                                if idv_cols:
                                    temp_use_cols = [
                                        "item_id",
                                        "busidaydt",
                                        "yhat",
                                        "yhat_lower",
                                        "yhat_upper",
                                    ]
                                    df = df[temp_use_cols + idv_cols + extra_idv]
                                    extra_idv = [
                                        f"{col}_model_{c+1}" for col in extra_idv
                                    ]
                                    df.columns = (
                                        [
                                            "item_id",
                                            self.date_col,
                                            f"Predicted_model_{c+1}",
                                            f"lower_bound_model_{c+1}",
                                            f"upper_bound_model_{c+1}",
                                        ]
                                        + idv_cols_name
                                        + extra_idv
                                    )
                                else:
                                    temp_use_cols = [
                                        "item_id",
                                        "busidaydt",
                                        "yhat",
                                        "yhat_0.95_left",
                                        "yhat_0.95_right",
                                    ]
                                    df = df[temp_use_cols + idv_cols + extra_idv]
                                    df.columns = [
                                        "item_id",
                                        self.date_col,
                                        f"Predicted_model_{c+1}",
                                        f"lower_bound_model_{c+1}",
                                        f"upper_bound_model_{c+1}",
                                    ]
                                model_df = model_df.merge(
                                    df, on=["item_id", self.date_col], how="inner"
                                )
                            model_map[f"model_{c+1}"] = model_dag
                            c += 1

                    with s3fs.S3FileSystem().open(
                        f"{idv_path}/model_mapping.json", "w"
                    ) as f:
                        json.dump(model_map, f)

                    list_cols = [
                        i
                        for i in model_df.columns
                        if i not in [self.date_col] + ["item_id"]
                    ]

                    model_df = (
                        model_df.groupby(["item_id"])
                        .agg({k: list for k in list_cols})
                        .reset_index()
                    )

                    df = pd.read_pickle(f"{idv_path}/idv_data.pkl")

                    self.data = model_df.merge(df, on="item_id", how="left")

                    with s3fs.S3FileSystem().open(
                        f"{idv_path}/model_evaluation_dashboard.pkl", "wb",
                    ) as f:
                        self.data.to_pickle(f)
                else:
                    self.progress_text.value = "Experiment not found"
        else:
            self.progress_text.value = "Experiment not found"

    # Function to load data with experiment name input
    def load_data(self, event):

        self.progress.value = 5
        self.progress_text.value = "Resetting Dashboard"

        self.reset_dashboard()

        self.progress.value = 10
        self.progress_text.value = "Loading Data..."

        # self.data = pd.read_pickle(r'D:\Forecasting_Accelerator\model_results\all_3_models_pickle_sampled_testing_idvs_testing.pkl')

        # data_path = f"s3://tiger-mle-shipping-forecasting/inputs/auto-gluonts-data/model_evaluation_dashboard_idvs.pkl"

        # with s3fs.S3FileSystem().open(data_path, "rb",) as f:
        #     self.data = pd.read_pickle(f)

        self.prepare_data()

        if hasattr(self, "data"):
            self.progress.value = 25
            self.progress_text.value = "Data loading complete"

            self._declare_components()

            self.progress.value = 100
            self.progress_text.value = "Dashboard ready to use"
        else:
            self.progress_text.value = "Experiment not found"

    # Function to reset dashboard for new inputs
    def reset_dashboard(self):

        # - Dates
        self.model_metrics_df.height = 0
        self.model_metrics_df_agg.height = 0
        self.crosstab_df.height = 0
        self.crosstab_df_agg.height = 0
        self.metrics_df.height = 0
        self.metrics_df_agg.height = 0

        for plot in self.metrics_dist_plot_list:
            plot.object = None

        for plot in self.metrics_dist_plot_list_agg:
            plot.object = None

        self.forecast_plot.object = None
        self.forecast_plot_agg.object = None
        self.waterfall_plot.object = None
        self.waterfall_plot_agg.object = None

        self.start_date.options = []
        self.start_date_agg.options = []
        self.cross_start_date.options = []
        self.cross_start_date_agg.options = []
        self.end_date.options = []
        self.end_date_agg.options = []
        self.cross_end_date.options = []
        self.cross_end_date_agg.options = []

        self.gran_filters_dist_plot.clear()
        self.gran_filters.clear()

        self.idv_cols.options = []
        self.idv_cols_agg.options = []

        self.model_selection.options = []
        self.model_selection_forecast.options = []
        self.model_selection_agg.options = []
        self.model_selection_agg_forecast.options = []

        self.basic_granularity.options = []
        self.basic_model_selection.options = []

        self.agg_granularity.options = []

        self.gran_filters_agg.clear()
        self.metric_filters.clear()
        self.metric_filters_agg.clear()
        if hasattr(self, "data"):
            delattr(self, "data")

    # To initialize components after loading the data
    def _declare_components(self):
        # Initialize all components
        """
        json_path = 'D:/Forecasting_Accelerator/model_results/input_variables.json'
        # json_path = "s3://tiger-mle-shipping-forecasting/inputs/auto-gluonts-data/2020-07-21/input_variables.json"

        with open(json_path) as f:
            metadata = json.load(f)

        # with s3fs.S3FileSystem().open(json_path, "rb",) as f:
        #     metadata = json.load(f)

        # Get from EDA Dashboard
        self.prediction_length = metadata["Forecast window"]
        self.data_freq = metadata["Data frequency"]
        self.test_end_date = metadata["Forecast end date"]
        self.granularity = [i[0].upper() + i[1:] for i in metadata["Data granularity"]]
        self.dv_col = metadata["Target variable"]
        self.date_col = metadata["Date variable"]
        self.fdr = metadata["Feat Dynamic Real"]
        """

        self.data["Start_Date"] = pd.to_datetime(self.data["Start_Date"])
        self.data.rename(
            columns={k: k[0].upper() + k[1:] for k in self.gran_cols}, inplace=True,
        )
        for col in self.granularity:
            self.data[col] = self.data[col].astype(str)

        self.models = sorted(
            [
                i.split("Predicted_")[1]
                for i in self.data.columns
                if i.startswith("Predicted")
            ]
        )

        # Dates
        self.max_end_date = pd.Timestamp(self.test_end_date, freq=self.data_freq)
        self.forecast_dates_str = [
            str((self.max_end_date - pd.Timedelta(i, unit=self.data_freq[0])).date())
            for i in range(self.prediction_length - 1, -1, -1)
        ]
        self.forecast_dates = [
            (self.max_end_date - pd.Timedelta(i, unit=self.data_freq[0])).date()
            for i in range(self.prediction_length - 1, -1, -1)
        ]

        # TAB
        self.ts_level_tab = pn.Tabs()

        # ----------------------------- MAPE, WMAPE, MAD Metrics Distribution -
        # - Start Date Dropdown
        self.start_date.options = self.forecast_dates
        self.start_date.value = self.forecast_dates[0]

        self.start_date_agg.options = self.forecast_dates
        self.start_date_agg.value = self.forecast_dates[0]

        self.cross_start_date.options = self.forecast_dates
        self.cross_start_date.value = self.forecast_dates[0]

        self.cross_start_date_agg.options = self.forecast_dates
        self.cross_start_date_agg.value = self.forecast_dates[0]

        self.end_date.options = self.forecast_dates
        self.end_date.value = self.forecast_dates[-1]

        self.end_date_agg.options = self.forecast_dates
        self.end_date_agg.value = self.forecast_dates[-1]

        self.cross_end_date.options = self.forecast_dates
        self.cross_end_date.value = self.forecast_dates[-1]

        self.cross_end_date_agg.options = self.forecast_dates
        self.cross_end_date_agg.value = self.forecast_dates[-1]

        self.independent_vars = ["None"] + [
            col
            for col in self.data.columns
            if not re.search("model_[0-9][0-9]?$", col)
            and col
            not in ["item_id", "Actual", "Actual_test", "Start_Date"] + self.granularity
        ]

        # Adding filters for granularity
        for gran in self.granularity:
            exec(
                f"self.{gran}_filter_dist = pn.widgets.MultiChoice( \
                options={self.data[gran].unique().tolist()}, width=200, \
                name='{gran}', max_items=1, margin=20)"
            )
            self.gran_filters_dist_plot.append(eval(f"self.{gran}_filter_dist"))

        for filtr in self.gran_filters_dist_plot:
            filtr.param.watch(self.update_gran_filters_dist_plot, "value")

        # Adding filters for granularity
        for gran in self.granularity:
            exec(
                f"self.{gran}_filter = pn.widgets.MultiChoice( \
                options={self.data[gran].unique().tolist()}, \
                width=200, name='{gran}', max_items=1, margin=20)"
            )
            self.gran_filters.append(eval(f"self.{gran}_filter"))

        for filtr in self.gran_filters:
            filtr.param.watch(self.update_gran_filters, "value")
            filtr.param.watch(self.get_forecast_plot, "value")
            filtr.param.watch(self.get_waterfall_plot, "value")

        self.progress.value = 50
        self.progress_text.value = "Initializing Dashboard..."

        # Selection for IDV, Model and metric bins
        self.idv_cols.options = self.independent_vars

        self.model_selection.options = self.models
        self.model_selection.value = self.models[0]

        self.model_selection_forecast.options = self.models
        self.model_selection_forecast.value = self.models[0]

        self.idv_cols_agg.options = self.independent_vars

        self.model_selection_agg.options = self.models
        self.model_selection_agg.value = self.models[0]

        self.model_selection_agg_forecast.options = self.models
        self.model_selection_agg_forecast.value = self.models[0]

        self.basic_granularity.options = ["All"] + self.granularity
        self.basic_granularity.value = "All"

        self.basic_model_selection.options = []
        self.basic_model_selection.value = None

        # ------------------------------------ 2nd Tab aggregation ------------
        self.agg_granularity.options = self.granularity
        self.agg_granularity.value = [self.granularity[0]]
        self.agg_granularity.max_items = len(self.granularity) - 1

        self.idv_cols.param.watch(self.get_forecast_plot, "value")
        self.model_selection_forecast.param.watch(self.get_forecast_plot, "value")
        self.model_selection_forecast.param.watch(self.get_waterfall_plot, "value")
        self.idv_cols_agg.param.watch(self.get_forecast_plot_agg, "value")
        self.model_selection_agg_forecast.param.watch(
            self.get_forecast_plot_agg, "value"
        )
        self.model_selection_agg_forecast.param.watch(
            self.get_waterfall_plot_agg, "value"
        )
        self.model_selection_forecast.param.watch(self.update_gran_filters, "value")
        self.model_selection_agg_forecast.param.watch(
            self.update_gran_filter_agg, "value"
        )
        self.basic_granularity.param.watch(self.get_model_metrics_again, "value")
        self.basic_model_selection.param.watch(self.get_model_metrics_again, "value")
        self.agg_granularity_btn.on_click(self.get_model_metrics_agg)
        self.agg_granularity_btn.on_click(self.get_metrics_dist_plot_agg)
        self.agg_granularity_btn.on_click(self.get_cross_table_agg)
        self.agg_granularity_btn.on_click(self.update_gran_filter_agg)
        self.agg_granularity_btn.on_click(self.get_forecast_plot_agg)
        self.agg_granularity_btn.on_click(self.get_waterfall_plot_agg)

        for gran in self.granularity:
            exec(
                f"self.{gran}_filter_agg = pn.widgets.MultiChoice( \
                options={self.data[gran].unique().tolist()}, \
                width=200, name='{gran}', max_items=1, margin=20)"
            )
            self.gran_filters_agg.append(eval(f"self.{gran}_filter_agg"))

        for filtr in self.gran_filters_agg:
            filtr.param.watch(self.update_gran_filter_agg, "value")
            filtr.param.watch(self.get_forecast_plot_agg, "value")
            filtr.param.watch(self.get_waterfall_plot_agg, "value")

        for filtr in self.gran_filters_agg:
            if not filtr.name in self.agg_granularity.value:
                filtr.value = []
                filtr.options = []

        self.all_cols = []
        for metric in self.metrics_list:
            for model in self.models:
                self.all_cols.append(f"{metric}_{model}")

        self.progress.value = 75
        self.progress_text.value = "Initializing Dashboard..."

        self.get_model_metrics()
        self.mad_dynamic_bins("MAD")
        # self.bias_dynamic_bins("Bias")
        self.bias_dynamic_bins("Tracking_Signal")

        # Metrics Filters
        for metric in self.metrics_list:
            if metric in self.percentage_metric:
                exec(
                    f"self.{metric.lower()}_bins = pn.widgets.Select( \
                    options=self.metric_bins_dropdown, width=80, height=60,\
                    name='{metric} Bins', margin=20, css_classes=['custom_class'])"
                )
            else:
                exec(
                    f"self.{metric.lower()}_bins = pn.widgets.Select( \
                    options=self.{metric.lower()}_metric_bins_dropdown, width=80, height=60, \
                    name='{metric} Bins', margin=20, css_classes=['custom_class'])"
                )

            self.metric_filters.append(eval(f"self.{metric.lower()}_bins"))

        for filtr in self.metric_filters:
            filtr.param.watch(self.update_gran_filters, "value")

        # Aggregated metrics filter
        for metric in self.metrics_list:
            if metric in self.percentage_metric:
                exec(
                    f"self.{metric.lower()}_bins_agg = pn.widgets.Select( \
                    options=self.metric_bins_dropdown, width=80, height=60, \
                    name='{metric} Bins', margin=20, css_classes=['custom_class'])"
                )
            else:
                exec(
                    f"self.{metric.lower()}_bins_agg = pn.widgets.Select( \
                    options=self.{metric.lower()}_metric_bins_dropdown, width=80, height=60, \
                    name='{metric} Bins', margin=20, css_classes=['custom_class'])"
                )

            self.metric_filters_agg.append(eval(f"self.{metric.lower()}_bins_agg"))

        for filtr in self.metric_filters_agg:
            filtr.param.watch(self.update_gran_filter_agg, "value")

    # To created dynamic bins for MAD based on metric in data for metrics 0 to inf
    def mad_dynamic_bins(self, metric):
        mad_perc = pd.Series()
        for model in self.models:
            mad_perc = mad_perc.append(self.data[f"{metric}_{model}"])

        mad_perc_value_min = 0
        mad_perc_value_max = round(
            np.percentile(mad_perc, 95),
            -(len(str(int(np.percentile(mad_perc, 95)))) - 1)
            if len(str(int(np.percentile(mad_perc, 95)))) > 1
            else 1,
        )
        mad_perc_value = round((mad_perc_value_max - mad_perc_value_min) / 4, 1)

        mad_bins = [round(i * mad_perc_value, 1) for i in range(5)] + [np.inf]

        exec(
            f"self.{metric.lower()}_bins_axis = pd.IntervalIndex.from_breaks(mad_bins, closed='left')"
        )
        exec(
            f"self.{metric.lower()}_metric_bins_dropdown = ['None'] + [str(i) for i in self.{metric.lower()}_bins_axis]"
        )
        mad_bin_range_mapping = [None] + [
            (round(i * mad_perc_value, 1), round((i + 1) * mad_perc_value, 1))
            if i < 4
            else (round(i * mad_perc_value, 1), np.inf)
            for i in range(5)
        ]
        drop_dict = {
            v: k
            for k, v in zip(
                mad_bin_range_mapping,
                eval(f"self.{metric.lower()}_metric_bins_dropdown"),
            )
        }
        exec(f"self.{metric.lower()}_bin_range_mapping = drop_dict")

    # To created dynamic bins for Bias based on metric in data for metrics -inf to inf
    def bias_dynamic_bins(self, metric):
        bias_perc = pd.Series()
        for model in self.models:
            bias_perc = bias_perc.append(self.data[f"{metric}_{model}"])

        bias_perc_value_max = round(
            np.percentile(bias_perc, 95),
            -(len(str(int(np.percentile(bias_perc, 95)))) - 1)
            if len(str(int(np.percentile(bias_perc, 95)))) > 1
            else 1,
        )
        bias_perc_value_min = round(
            np.percentile(bias_perc, 5),
            -(len(str(int(np.percentile(bias_perc, 5)))) - 2)
            if len(str(int(np.percentile(bias_perc, 5)))) > 2
            else 1,
        )
        bias_perc_value = round((bias_perc_value_max - bias_perc_value_min) / 3, 1)

        bias_bins = (
            [-np.inf]
            + [round(i * bias_perc_value + bias_perc_value_min, 1) for i in range(4)]
            + [np.inf]
        )
        exec(
            f"self.{metric.lower()}_bins_axis = pd.IntervalIndex.from_breaks(bias_bins, closed='left')"
        )
        exec(
            f"self.{metric.lower()}_metric_bins_dropdown = ['None'] + [str(i) for i in self.{metric.lower()}_bins_axis]"
        )
        bias_bin_range_mapping = [None, (-np.inf, bias_perc_value_min)] + [
            (
                round(i * bias_perc_value + bias_perc_value_min, 1),
                round((i + 1) * bias_perc_value + bias_perc_value_min, 1),
            )
            if i < 3
            else (round(i * bias_perc_value + bias_perc_value_min, 1), np.inf)
            for i in range(4)
        ]
        drop_dict = {
            v: k
            for k, v in zip(
                bias_bin_range_mapping,
                eval(f"self.{metric.lower()}_metric_bins_dropdown"),
            )
        }
        exec(f"self.{metric.lower()}_bin_range_mapping = drop_dict")

    # To update granularity filters for any selection of granularity, model or metric bins in forecast plot
    def update_gran_filters(self, event):
        df = self.data.copy()

        others_score_range = []
        mape_score_range = []
        for metric in self.metrics_list:
            if metric not in self.percentage_metric:
                others_score_range.append(
                    eval(
                        f"self.{metric.lower()}_bin_range_mapping[self.{metric.lower()}_bins.value]"
                    )
                )
            else:
                mape_score_range.append(
                    eval(f"self.bin_range_mapping[self.{metric.lower()}_bins.value]")
                )

        score_ranges = mape_score_range + others_score_range

        bool_score_ranges = [bool(score) for score in score_ranges]
        if any(bool_score_ranges):

            for filtr in self.gran_filters:
                filtr.options = df[filtr.name].unique().tolist()

            for score_range, metric in zip(
                list(np.array(score_ranges)[bool_score_ranges]),
                list(np.array(self.metrics_list)[bool_score_ranges]),
            ):
                col = metric + "_" + self.model_selection_forecast.value
                if metric in self.percentage_metric:
                    df = df[
                        (df[col] * 100 >= score_range[0])
                        & (df[col] * 100 < score_range[1])
                    ]
                else:
                    df = df[(df[col] >= score_range[0]) & (df[col] < score_range[1])]

        for filtr in self.gran_filters:
            if filtr.value:
                df = df[df[filtr.name] == filtr.value[0]]

        for filtr in self.gran_filters:
            if not filtr.value:
                filtr.options = df[filtr.name].unique().tolist()

    # To update granularity filters for any selection of granularity in distribution plot
    def update_gran_filters_dist_plot(self, event):
        df = self.data.copy()

        for filtr in self.gran_filters_dist_plot:
            if filtr.value:
                df = df[df[filtr.name] == filtr.value[0]]

        for filtr in self.gran_filters_dist_plot:
            if not filtr.value:
                filtr.options = df[filtr.name].unique().tolist()

    # To update granularity filters for any selection of granularity, model or metric bins in aggregate forecast plot
    def update_gran_filter_agg(self, event):
        if self.progress.value == 100 and self.agg_granularity.value:

            if not self.gran_filters_agg.objects:
                for gran in self.granularity:
                    exec(
                        f"self.{gran}_filter_agg = pn.widgets.MultiChoice( \
                        options={self.data[gran].unique().tolist()}, \
                        width=200, name='{gran}', max_items=1, margin=20)"
                    )
                    self.gran_filters_agg.append(eval(f"self.{gran}_filter_agg"))

                for filtr in self.gran_filters_agg:
                    filtr.param.watch(self.update_gran_filter_agg, "value")
                    filtr.param.watch(self.get_forecast_plot_agg, "value")
                    filtr.param.watch(self.get_waterfall_plot_agg, "value")

                for filtr in self.gran_filters_agg:
                    if not filtr.name in self.agg_granularity.value:
                        filtr.value = []
                        filtr.options = []

            if not self.metric_filters_agg.objects:
                for metric in self.metrics_list:
                    if metric in self.percentage_metric:
                        exec(
                            f"self.{metric.lower()}_bins_agg = pn.widgets.Select( \
                            options=self.metric_bins_dropdown, width=80, height=60, \
                            name='{metric} Bins', margin=20, css_classes=['custom_class'])"
                        )
                    else:
                        exec(
                            f"self.{metric.lower()}_bins_agg = pn.widgets.Select( \
                            options=self.{metric.lower()}_metric_bins_dropdown, width=80, height=60, \
                            name='{metric} Bins', margin=20, css_classes=['custom_class'])"
                        )

                    self.metric_filters_agg.append(
                        eval(f"self.{metric.lower()}_bins_agg")
                    )

                for filtr in self.metric_filters_agg:
                    filtr.param.watch(self.update_gran_filter_agg, "value")

            df = self.data.copy()

            mape_score_range = []
            others_score_range = []
            for metric in self.metrics_list:
                if metric not in self.percentage_metric:
                    others_score_range.append(
                        eval(
                            f"self.{metric.lower()}_bin_range_mapping[self.{metric.lower()}_bins_agg.value]"
                        )
                    )
                else:
                    mape_score_range.append(
                        eval(
                            f"self.bin_range_mapping[self.{metric.lower()}_bins_agg.value]"
                        )
                    )

            score_ranges = mape_score_range + others_score_range

            bool_score_ranges = [bool(score) for score in score_ranges]
            if any(bool_score_ranges):

                for filtr in self.gran_filters_agg:
                    filtr.options = df[filtr.name].unique().tolist()

                agg_df = pd.DataFrame()
                for cols in [f"Predicted_{self.model_selection_agg_forecast.value}"] + [
                    "Actual_test"
                ]:
                    agg_df[cols] = (
                        self.data.groupby(self.agg_granularity.value)[cols]
                        .apply(list)
                        .apply(lambda x: np.array(x).sum(0))
                    )

                agg_df.reset_index(inplace=True)
                for metric in self.metrics_list:
                    metric_func = eval(f"metric_{metric}")
                    agg_df[
                        f"{metric}_{self.model_selection_agg_forecast.value}"
                    ] = agg_df.apply(
                        lambda x: metric_func(
                            x["Actual_test"],
                            x[f"Predicted_{self.model_selection_agg_forecast.value}"],
                        ),
                        axis=1,
                    )

                df = agg_df
                for score_range, metric in zip(
                    list(np.array(score_ranges)[bool_score_ranges]),
                    list(np.array(self.metrics_list)[bool_score_ranges]),
                ):
                    col = metric + "_" + self.model_selection_agg_forecast.value
                    if metric in self.percentage_metric:
                        df = df[
                            (df[col] * 100 >= score_range[0])
                            & (df[col] * 100 < score_range[1])
                        ]
                    else:
                        df = df[
                            (df[col] >= score_range[0]) & (df[col] < score_range[1])
                        ]

            for filtr in self.gran_filters_agg:
                if filtr.name in self.agg_granularity.value:
                    if filtr.value:
                        df = df[df[filtr.name] == filtr.value[0]]
                else:
                    filtr.value = []
                    filtr.options = []

            for filtr in self.gran_filters_agg:
                if filtr.name in self.agg_granularity.value:
                    if not filtr.value:
                        filtr.options = df[filtr.name].unique().tolist()
        else:
            self.gran_filters_agg.clear()
            self.metric_filters_agg.clear()

    # Function to plot the waterfall plot
    def get_waterfall_plot(self, event):
        if self.progress.value == 100:
            if not all([bool(filtr.value) for filtr in self.gran_filters]) or not [
                col
                for col in self.data.columns
                if col == f"trend_{self.model_selection_forecast.value}"
            ]:
                self.waterfall_plot.object = None
            else:
                df = self.data.copy()
                for filtr in self.gran_filters:
                    df = df[df[filtr.name] == filtr.value[0]]

                idv_data = pd.DataFrame()

                idv_data_col = [
                    f"{col}_{self.model_selection_forecast.value}" for col in self.fdr
                ]
                for col in idv_data_col:
                    idv_data[col] = df[col].iloc[0]

                trend_season = pd.DataFrame()
                trend_season[f"trend_{self.model_selection_forecast.value}"] = df[
                    f"trend_{self.model_selection_forecast.value}"
                ].iloc[0]

                trend_season[f"season_{self.model_selection_forecast.value}"] = 0
                for col in ["daily", "weekly", "yearly"]:
                    if f"{col}_{self.model_selection_forecast.value}" in df.columns:
                        trend_season[col] = df[
                            f"{col}_{self.model_selection_forecast.value}"
                        ].iloc[0]
                        trend_season[
                            f"season_{self.model_selection_forecast.value}"
                        ] += trend_season[col]

                index = ["trend", "seasonality"] + self.fdr

                if abs(
                    sum(
                        df[
                            f"multiplicative_terms_{self.model_selection_forecast.value}"
                        ].iloc[0]
                    )
                ):

                    trend_season["seasonality"] = (
                        trend_season[f"trend_{self.model_selection_forecast.value}"]
                        * trend_season[f"season_{self.model_selection_forecast.value}"]
                    )

                    idv_data = idv_data.apply(
                        lambda x: x
                        * trend_season[f"trend_{self.model_selection_forecast.value}"]
                    )

                else:
                    trend_season["seasonality"] = trend_season[
                        f"season_{self.model_selection_forecast.value}"
                    ]

                Final_data = pd.concat(
                    [
                        trend_season[
                            [
                                f"trend_{self.model_selection_forecast.value}",
                                "seasonality",
                            ]
                        ],
                        idv_data,
                    ],
                    axis=1,
                )

                plot_data = Final_data.agg(sum).to_frame("Contribution")

                plot_data.index = index

                zero_col = plot_data[plot_data["Contribution"] == 0].index.tolist()
                non_zero_col = [i for i in plot_data.index[2:] if i not in zero_col]
                non_zero_col = (
                    plot_data[plot_data.index.isin(non_zero_col)]
                    .sort_values("Contribution")
                    .index.tolist()
                )
                plot_data = plot_data.T[
                    [f"trend", "seasonality"] + non_zero_col + zero_col
                ].T

                plot_data["Cumulative"] = plot_data["Contribution"].cumsum()

                plot_data["y_start"] = (
                    plot_data["Cumulative"] - plot_data["Contribution"]
                )

                total = sum(
                    df[f"Predicted_{self.model_selection_forecast.value}"].iloc[0]
                )
                plot_data = plot_data.append(
                    pd.DataFrame(
                        [(total, total, 0)],
                        columns=["Contribution", "Cumulative", "y_start"],
                        index=["Forecast"],
                    )
                )

                max_val = plot_data["Contribution"].max()
                plot_data["color"] = "green"
                plot_data.loc[plot_data.Contribution < 0, "color"] = "red"

                source = ColumnDataSource(plot_data)
                TOOLS = "hover,box_zoom,reset,save"
                p = figure(
                    tools=TOOLS,
                    x_range=list(plot_data.index),
                    y_range=(0, max_val * 1.1),
                    y_axis_label=self.dv_col,
                    plot_width=800,
                    title=f"{self.dv_col} Feature Importance ({self.model_selection_forecast.value})",
                )

                p.segment(
                    x0="index",
                    x1="index",
                    y0="y_start",
                    y1="Cumulative",
                    source=source,
                    line_width=25,
                    color="color",
                )

                p.yaxis[0].formatter = NumeralTickFormatter(format="(0.0 a)")
                p.xaxis.major_label_orientation = np.pi / 2
                hover = p.select(dict(type=HoverTool))
                hover.tooltips = [
                    (f"Feature", f"@index",),
                    (f"Contribution", f"@Contribution" + "{0.0 a}",),
                ]
                hover.mode = "mouse"

                self.waterfall_plot.object = p

    # Function to plot the aggregate waterfall plot
    def get_waterfall_plot_agg(self, event):
        if self.progress.value == 100:
            if not all(
                [
                    bool(filtr.value)
                    for filtr in self.gran_filters_agg
                    if filtr.name in self.agg_granularity.value
                ]
            ) or not [
                col
                for col in self.data.columns
                if col == f"trend_{self.model_selection_agg_forecast.value}"
            ]:
                self.waterfall_plot_agg.object = None
            else:
                tmp_df = self.data.copy()

                for filtr in self.gran_filters_agg:
                    if filtr.name in self.agg_granularity.value:
                        tmp_df = tmp_df[tmp_df[filtr.name] == filtr.value[0]]

                idv_data = pd.DataFrame()

                idv_data_col = [
                    f"{col}_{self.model_selection_agg_forecast.value}"
                    for col in self.fdr
                ]
                for col in idv_data_col:
                    idv_data[col] = np.concatenate(
                        [i for i in tmp_df[col].apply(np.array).values]
                    )

                trend_season = pd.DataFrame()
                trend_season[
                    f"trend_{self.model_selection_agg_forecast.value}"
                ] = np.concatenate(
                    [
                        i
                        for i in tmp_df[
                            f"trend_{self.model_selection_agg_forecast.value}"
                        ]
                        .apply(np.array)
                        .values
                    ]
                )

                trend_season[f"season_{self.model_selection_agg_forecast.value}"] = 0
                for col in ["daily", "weekly", "yearly"]:
                    if (
                        f"{col}_{self.model_selection_agg_forecast.value}"
                        in tmp_df.columns
                    ):
                        trend_season[col] = np.concatenate(
                            [
                                i
                                for i in tmp_df[
                                    f"{col}_{self.model_selection_agg_forecast.value}"
                                ]
                                .apply(np.array)
                                .values
                            ]
                        )
                        trend_season[
                            f"season_{self.model_selection_agg_forecast.value}"
                        ] += trend_season[col]

                index = ["trend", "seasonality"] + self.fdr

                if abs(
                    sum(
                        tmp_df[
                            f"multiplicative_terms_{self.model_selection_agg_forecast.value}"
                        ].iloc[0]
                    )
                ):

                    trend_season["seasonality"] = (
                        trend_season[f"trend_{self.model_selection_agg_forecast.value}"]
                        * trend_season[
                            f"season_{self.model_selection_agg_forecast.value}"
                        ]
                    )

                    idv_data = idv_data.apply(
                        lambda x: x
                        * trend_season[
                            f"trend_{self.model_selection_agg_forecast.value}"
                        ]
                    )

                else:
                    trend_season["seasonality"] = trend_season[
                        f"season_{self.model_selection_agg_forecast.value}"
                    ]

                Final_data = pd.concat(
                    [
                        trend_season[
                            [
                                f"trend_{self.model_selection_agg_forecast.value}",
                                "seasonality",
                            ]
                        ],
                        idv_data,
                    ],
                    axis=1,
                )

                plot_data = Final_data.agg(sum).to_frame("Contribution")

                plot_data.index = index

                zero_col = plot_data[plot_data["Contribution"] == 0].index.tolist()
                non_zero_col = [i for i in plot_data.index[2:] if i not in zero_col]
                non_zero_col = (
                    plot_data[plot_data.index.isin(non_zero_col)]
                    .sort_values("Contribution")
                    .index.tolist()
                )
                plot_data = plot_data.T[
                    [f"trend", "seasonality"] + non_zero_col + zero_col
                ].T

                plot_data["Cumulative"] = plot_data["Contribution"].cumsum()

                plot_data["y_start"] = (
                    plot_data["Cumulative"] - plot_data["Contribution"]
                )

                total = sum(
                    tmp_df[f"Predicted_{self.model_selection_agg_forecast.value}"]
                    .apply(np.array)
                    .values.sum(0)
                    .tolist()
                )
                plot_data = plot_data.append(
                    pd.DataFrame(
                        [(total, total, 0)],
                        columns=["Contribution", "Cumulative", "y_start"],
                        index=["Forecast"],
                    )
                )

                max_val = plot_data["Contribution"].max()
                plot_data["color"] = "green"
                plot_data.loc[plot_data.Contribution < 0, "color"] = "red"

                source = ColumnDataSource(plot_data)
                TOOLS = "hover,box_zoom,reset,save"
                p = figure(
                    tools=TOOLS,
                    x_range=list(plot_data.index),
                    y_range=(0, max_val * 1.1),
                    y_axis_label=self.dv_col,
                    plot_width=800,
                    title=f"{self.dv_col} Feature Importance ({self.model_selection_agg_forecast.value})",
                )

                p.segment(
                    x0="index",
                    x1="index",
                    y0="y_start",
                    y1="Cumulative",
                    source=source,
                    line_width=25,
                    color="color",
                )

                p.yaxis[0].formatter = NumeralTickFormatter(format="(0.0 a)")
                p.xaxis.major_label_orientation = np.pi / 2
                hover = p.select(dict(type=HoverTool))
                hover.tooltips = [
                    (f"Feature", f"@index",),
                    (f"Contribution", f"@Contribution" + "{0.0 a}",),
                ]
                hover.mode = "mouse"

                self.waterfall_plot_agg.object = p

    # Function to plot the forecast plot
    def get_forecast_plot(self, event):
        if self.progress.value == 100:
            if not all([bool(filtr.value) for filtr in self.gran_filters]):
                self.forecast_plot.object = None
                self.metrics_df.height = 0
            else:
                df = self.data.copy()
                for filtr in self.gran_filters:
                    df = df[df[filtr.name] == filtr.value[0]]

                # get the time series for give filters
                ts = df["Actual"].values[0]

                start_date = pd.Timestamp(
                    df["Start_Date"].values[0], freq=self.data_freq
                )
                weekly_timeline = [
                    start_date + pd.Timedelta(i, unit=self.data_freq[0])
                    for i in range(len(ts))
                ]

                pred_val = np.pad(
                    np.array(
                        df[f"Predicted_{self.model_selection_forecast.value}"].values[0]
                    ),
                    (len(ts) - self.prediction_length, 0),
                )
                upper_val = np.pad(
                    np.array(
                        df[f"upper_bound_{self.model_selection_forecast.value}"].values[
                            0
                        ]
                    ),
                    (len(ts) - self.prediction_length, 0),
                )
                lower_val = np.pad(
                    np.array(
                        df[f"lower_bound_{self.model_selection_forecast.value}"].values[
                            0
                        ]
                    ),
                    (len(ts) - self.prediction_length, 0),
                )

                plot_ts = ColumnDataSource(
                    pd.DataFrame(
                        {
                            "timeline": weekly_timeline,
                            self.dv_col: ts,
                            f"{self.dv_col}_{self.model_selection_forecast.value}": np.where(
                                pred_val == 0, None, pred_val
                            ),
                            f"upper_bound_{self.model_selection_forecast.value}": np.where(
                                upper_val == 0, None, upper_val
                            ),
                            f"lower_bound_{self.model_selection_forecast.value}": np.where(
                                lower_val == 0, None, lower_val
                            ),
                        },
                    )
                )

                # Create the Figure: fig
                fig = figure(
                    x_axis_label=self.date_col,
                    y_axis_label=self.dv_col,
                    x_axis_type="datetime",
                    plot_width=1300,
                    plot_height=300,
                )
                fig.xaxis.formatter = DatetimeTickFormatter(
                    hours=["%b %Y"], months=["%b %Y"], years=["%b %Y"],
                )
                fig.yaxis.formatter = NumeralTickFormatter(format="0.0a")
                fig.xaxis[0].ticker.desired_num_ticks = 25
                fig.xaxis.major_label_orientation = np.pi / 4
                fig.xaxis.axis_label_text_color = (
                    fig.yaxis.axis_label_text_color
                ) = "teal"
                legends_iter = []
                # Plot Actual Time Series Data
                p1 = fig.line(
                    x="timeline",
                    y=self.dv_col,
                    source=plot_ts,
                    color="navy",
                    line_width=1,
                )
                legends_iter.append(("Actual", [p1]))

                # Plot a Vertical Line to Denote the Start Point of Forecast
                p3 = fig.ray(
                    x=weekly_timeline[-self.prediction_length],
                    y=[0],
                    color="red",
                    length=0,
                    angle=np.pi / 2,
                    line_width=1,
                )
                pr = fig.ray(
                    x=weekly_timeline[-self.prediction_length],
                    y=[0],
                    color="red",
                    length=0,
                    angle=3 * (np.pi / 2),
                    line_width=1,
                )
                legends_iter.append(("Forecast Start Point", [p3, pr]))

                # Plot Predicted Data
                p4 = fig.line(
                    x="timeline",
                    y=f"{self.dv_col}_{self.model_selection_forecast.value}",
                    source=plot_ts,
                    color="green",
                    line_width=1,
                    name=f"pred_line_{self.model_selection_forecast.value}",
                )
                legends_iter.append(
                    (f"Predicted_{self.model_selection_forecast.value}", [p4])
                )

                # Add a square glyph to fig
                p5 = fig.circle(
                    x="timeline",
                    y=f"{self.dv_col}_{self.model_selection_forecast.value}",
                    source=plot_ts,
                    line_width=0.5,
                    color="green",
                    fill_alpha=0.3,
                    name=f"pred_circle_{self.model_selection_forecast.value}",
                )
                # Add hover tool
                p6 = fig.add_tools(
                    HoverTool(
                        tooltips=[
                            ("timeline", "@timeline{%F}"),
                            (
                                f"{self.dv_col}_{self.model_selection_forecast.value}",
                                f"@{self.dv_col}_{self.model_selection_forecast.value}"
                                + "{0.0 a}",
                            ),
                            (f"{self.dv_col}", f"@{self.dv_col}" + "{0.0 a}",),
                            (
                                f"upper_bound_{self.model_selection_forecast.value}",
                                f"@upper_bound_{self.model_selection_forecast.value}"
                                + "{0.0 a}",
                            ),
                            (
                                f"lower_bound_{self.model_selection_forecast.value}",
                                f"@lower_bound_{self.model_selection_forecast.value}"
                                + "{0.0 a}",
                            ),
                        ],
                        formatters={"@timeline": "datetime"},
                        name=f"pred_hover_{self.model_selection_forecast.value}",
                    )
                )

                # Plot Upper Confidence
                p_up = fig.line(
                    x="timeline",
                    y=f"upper_bound_{self.model_selection_forecast.value}",
                    source=plot_ts,
                    color="#29e646",
                    line_width=1,
                    name=f"upper_confidence_{self.model_selection_forecast.value}",
                )
                legends_iter.append((f"95% upper confidence", [p_up]))

                # Plot Lower Confidence
                p_lo = fig.line(
                    x="timeline",
                    y=f"lower_bound_{self.model_selection_forecast.value}",
                    source=plot_ts,
                    color="#29e646",
                    line_width=1,
                    name=f"lower_confidence_{self.model_selection_forecast.value}",
                )
                legends_iter.append((f"95% Lower confidence", [p_lo]))

                self.prediction_dict[self.model_selection_forecast.value] = [
                    p4,
                    p5,
                    p6,
                    p_up,
                    p_lo,
                ]

                # Secondary Axis for Independent Variable
                if self.idv_cols.value != "None" and self.idv_cols.value:
                    idv_data = df[self.idv_cols.value].values[0]
                    if min(idv_data) == max(idv_data):
                        fig.extra_y_ranges = {
                            "idv_range": Range1d(
                                start=min(idv_data) * 0.75, end=max(idv_data) * 1.25
                            )
                        }
                    else:
                        fig.extra_y_ranges = {
                            "idv_range": Range1d(start=min(idv_data), end=max(idv_data))
                        }
                    fig.add_layout(
                        LinearAxis(
                            y_range_name="idv_range",
                            axis_label=f"{self.idv_cols.value}",
                        ),
                        "right",
                    )
                    plot_ts.data[self.idv_cols.value] = idv_data

                    p8 = fig.line(
                        x="timeline",
                        y=self.idv_cols.value,
                        source=plot_ts,
                        color="#AABBCC",
                        y_range_name="idv_range",
                        line_width=1,
                    )
                    p6 = fig.add_tools(
                        HoverTool(
                            tooltips=[
                                ("timeline", "@timeline{%F}"),
                                (
                                    f"{self.dv_col}_{self.model_selection_forecast.value}",
                                    f"@{self.dv_col}_{self.model_selection_forecast.value}"
                                    + "{0.0 a}",
                                ),
                                (f"{self.dv_col}", f"@{self.dv_col}" + "{0.0 a}",),
                                (
                                    f"upper_bound_{self.model_selection_forecast.value}",
                                    f"@upper_bound_{self.model_selection_forecast.value}"
                                    + "{0.0 a}",
                                ),
                                (
                                    f"lower_bound_{self.model_selection_forecast.value}",
                                    f"@lower_bound_{self.model_selection_forecast.value}"
                                    + "{0.0 a}",
                                ),
                                (
                                    f"{self.idv_cols.value}",
                                    f"@{self.idv_cols.value}" + "{0.0 a}",
                                ),
                            ],
                            formatters={"@timeline": "datetime"},
                            name=f"pred_hover_{self.model_selection_forecast.value}",
                        )
                    )
                    legends_iter.append((f"{self.idv_cols.value}", [p8]))

                # Add Legends
                legends = Legend(items=legends_iter)
                legends.click_policy = "hide"
                fig.add_layout(legends, "right")

                self.forecast_plot.height = 300
                self.forecast_plot.object = fig
                self.metrics_df.height = 50
                metrics_df = df[self.granularity]
                for metric in self.metrics_list:
                    metric_func = eval(f"metric_{metric}")
                    metrics_df[metric] = metric_func(
                        df["Actual_test"].iloc[0],
                        df[f"Predicted_{self.model_selection_forecast.value}"].iloc[0],
                    )
                    if metric in self.percentage_metric:
                        metrics_df[metric] = metrics_df[metric] * 100
                metrics_df.rename(
                    columns={k: f"{k} %" for k in self.percentage_metric}, inplace=True,
                )
                metrics_df = metrics_df.round(2)
                self.metrics_df.value = metrics_df.set_index(self.granularity[0])

    # Function to plot the aggregaetd forecast plot
    def get_forecast_plot_agg(self, event):
        if self.progress.value == 100:
            if not all(
                [
                    bool(filtr.value)
                    for filtr in self.gran_filters_agg
                    if filtr.name in self.agg_granularity.value
                ]
            ):
                self.forecast_plot_agg.object = None
                self.metrics_df_agg.height = 0
            else:
                model_cols = [
                    f"{n}_{self.model_selection_agg_forecast.value}"
                    for n in ["Predicted", "lower_bound", "upper_bound"]
                ]

                tmp_df = self.data.copy()

                for filtr in self.gran_filters_agg:
                    if filtr.name in self.agg_granularity.value:
                        tmp_df = tmp_df[tmp_df[filtr.name] == filtr.value[0]]

                agg_df = pd.DataFrame()
                for cols in model_cols + ["Actual_test"]:
                    agg_df[cols] = [tmp_df[cols].apply(np.array).values.sum(0).tolist()]

                maxx = tmp_df["Actual"].map(len).max()

                for cols in self.independent_vars + ["Actual"]:
                    if cols != "None":
                        agg_df[cols] = [
                            tmp_df[cols]
                            .apply(lambda x: np.pad(x, (maxx - len(x), 0)))
                            .values.sum()
                            .tolist()
                        ]

                agg_df["Start_Date"] = tmp_df["Start_Date"].min()

                for filtr in self.gran_filters_agg:
                    if filtr.name in self.agg_granularity.value:
                        agg_df[filtr.name] = filtr.value

                df = agg_df

                # get the time series for given filters
                ts = df["Actual"].values[0]

                start_date = pd.Timestamp(
                    df["Start_Date"].values[0], freq=self.data_freq
                )
                weekly_timeline = [
                    start_date + pd.Timedelta(i, unit=self.data_freq[0])
                    for i in range(len(ts))
                ]

                pred_val = np.pad(
                    np.array(
                        df[
                            f"Predicted_{self.model_selection_agg_forecast.value}"
                        ].values[0]
                    ),
                    (len(ts) - self.prediction_length, 0),
                )
                upper_val = np.pad(
                    np.array(
                        df[
                            f"upper_bound_{self.model_selection_agg_forecast.value}"
                        ].values[0]
                    ),
                    (len(ts) - self.prediction_length, 0),
                )
                lower_val = np.pad(
                    np.array(
                        df[
                            f"lower_bound_{self.model_selection_agg_forecast.value}"
                        ].values[0]
                    ),
                    (len(ts) - self.prediction_length, 0),
                )

                plot_ts = ColumnDataSource(
                    pd.DataFrame(
                        {
                            "timeline": weekly_timeline,
                            self.dv_col: ts,
                            f"{self.dv_col}_{self.model_selection_agg_forecast.value}": np.where(
                                pred_val == 0, None, pred_val
                            ),
                            f"upper_bound_{self.model_selection_agg_forecast.value}": np.where(
                                upper_val == 0, None, upper_val
                            ),
                            f"lower_bound_{self.model_selection_agg_forecast.value}": np.where(
                                lower_val == 0, None, lower_val
                            ),
                        },
                    )
                )

                # Create the Figure: fig
                fig = figure(
                    x_axis_label=self.date_col,
                    y_axis_label=self.dv_col,
                    x_axis_type="datetime",
                    plot_width=1300,
                    plot_height=300,
                )
                fig.xaxis.formatter = DatetimeTickFormatter(
                    hours=["%b %Y"], days=["%b %Y"], months=["%b %Y"], years=["%b %Y"],
                )
                fig.yaxis.formatter = NumeralTickFormatter(format="0.0a")
                fig.xaxis[0].ticker.desired_num_ticks = 25
                fig.xaxis.major_label_orientation = np.pi / 4
                fig.xaxis.axis_label_text_color = (
                    fig.yaxis.axis_label_text_color
                ) = "teal"
                legends_iter = []
                # Plot Actual Time Series Data
                p1 = fig.line(
                    x="timeline",
                    y=self.dv_col,
                    source=plot_ts,
                    color="navy",
                    line_width=1,
                )
                legends_iter.append(("Actual", [p1]))

                # Plot a Vertical Line to Denote the Start Point of Forecast
                p3 = fig.ray(
                    x=weekly_timeline[-self.prediction_length],
                    y=[0],
                    color="red",
                    length=0,
                    angle=np.pi / 2,
                    line_width=1,
                )
                pr = fig.ray(
                    x=weekly_timeline[-self.prediction_length],
                    y=[0],
                    color="red",
                    length=0,
                    angle=3 * (np.pi / 2),
                    line_width=1,
                )
                legends_iter.append(("Forecast Start Point", [p3, pr]))

                # Plot Predicted Data
                p4 = fig.line(
                    x="timeline",
                    y=f"{self.dv_col}_{self.model_selection_agg_forecast.value}",
                    source=plot_ts,
                    color="green",
                    line_width=1,
                    name=f"pred_line_{self.model_selection_agg_forecast.value}",
                )
                legends_iter.append(
                    (f"Predicted_{self.model_selection_agg_forecast.value}", [p4])
                )

                # Add a square glyph to fig
                p5 = fig.circle(
                    x="timeline",
                    y=f"{self.dv_col}_{self.model_selection_agg_forecast.value}",
                    source=plot_ts,
                    line_width=0.5,
                    color="green",
                    fill_alpha=0.3,
                    name=f"pred_circle_{self.model_selection_agg_forecast.value}",
                )
                # Add hover tool
                p6 = fig.add_tools(
                    HoverTool(
                        tooltips=[
                            ("timeline", "@timeline{%F}"),
                            (
                                f"{self.dv_col}_{self.model_selection_agg_forecast.value}",
                                f"@{self.dv_col}_{self.model_selection_agg_forecast.value}"
                                + "{0.0 a}",
                            ),
                            (f"{self.dv_col}", f"@{self.dv_col}" + "{0.0 a}",),
                            (
                                f"upper_bound_{self.model_selection_agg_forecast.value}",
                                f"@upper_bound_{self.model_selection_agg_forecast.value}"
                                + "{0.0 a}",
                            ),
                            (
                                f"lower_bound_{self.model_selection_agg_forecast.value}",
                                f"@lower_bound_{self.model_selection_agg_forecast.value}"
                                + "{0.0 a}",
                            ),
                        ],
                        formatters={"@timeline": "datetime"},
                        name=f"pred_hover_{self.model_selection_agg_forecast.value}",
                    )
                )

                # Plot Upper Confidence
                p_up = fig.line(
                    x="timeline",
                    y=f"upper_bound_{self.model_selection_agg_forecast.value}",
                    source=plot_ts,
                    color="#29e646",
                    line_width=1,
                    name=f"upper_confidence_{self.model_selection_agg_forecast.value}",
                )
                legends_iter.append((f"95% upper confidence", [p_up]))

                # Plot Lower Confidence
                p_lo = fig.line(
                    x="timeline",
                    y=f"lower_bound_{self.model_selection_agg_forecast.value}",
                    source=plot_ts,
                    color="#29e646",
                    line_width=1,
                    name=f"lower_confidence_{self.model_selection_agg_forecast.value}",
                )
                legends_iter.append((f"95% Lower confidence", [p_lo]))

                self.prediction_dict[self.model_selection_agg_forecast.value] = [
                    p4,
                    p5,
                    p6,
                    p_up,
                    p_lo,
                ]

                # Secondary Axis for Independent Variable
                if self.idv_cols_agg.value != "None" and self.idv_cols_agg.value:
                    idv_data = df[self.idv_cols_agg.value].values[0]
                    if min(idv_data) == max(idv_data):
                        fig.extra_y_ranges = {
                            "idv_range": Range1d(
                                start=min(idv_data) * 0.75, end=max(idv_data) * 1.25
                            )
                        }
                    else:
                        fig.extra_y_ranges = {
                            "idv_range": Range1d(start=min(idv_data), end=max(idv_data))
                        }
                    fig.add_layout(
                        LinearAxis(
                            y_range_name="idv_range",
                            axis_label=f"{self.idv_cols_agg.value} ({'mean' if re.match('(?i)price|weight', self.idv_cols_agg.value) else 'sum'})",
                        ),
                        "right",
                    )

                    plot_ts.data[self.idv_cols_agg.value] = idv_data
                    p8 = fig.line(
                        x="timeline",
                        y=self.idv_cols_agg.value,
                        source=plot_ts,
                        color="#AABBCC",
                        y_range_name="idv_range",
                        line_width=1,
                    )
                    p6 = fig.add_tools(
                        HoverTool(
                            tooltips=[
                                ("timeline", "@timeline{%F}"),
                                (
                                    f"{self.dv_col}_{self.model_selection_agg_forecast.value}",
                                    f"@{self.dv_col}_{self.model_selection_agg_forecast.value}"
                                    + "{0.0 a}",
                                ),
                                (f"{self.dv_col}", f"@{self.dv_col}" + "{0.0 a}",),
                                (
                                    f"upper_bound_{self.model_selection_agg_forecast.value}",
                                    f"@upper_bound_{self.model_selection_agg_forecast.value}"
                                    + "{0.0 a}",
                                ),
                                (
                                    f"lower_bound_{self.model_selection_agg_forecast.value}",
                                    f"@lower_bound_{self.model_selection_agg_forecast.value}"
                                    + "{0.0 a}",
                                ),
                                (
                                    f"{self.idv_cols_agg.value}",
                                    f"@{self.idv_cols_agg.value}" + "{0.0 a}",
                                ),
                            ],
                            formatters={"@timeline": "datetime"},
                            name=f"pred_hover_{self.model_selection_agg_forecast.value}",
                        )
                    )
                    legends_iter.append((f"{self.idv_cols_agg.value}", [p8]))

                # Add Legends
                legends = Legend(items=legends_iter)
                legends.click_policy = "hide"
                fig.add_layout(legends, "right")

                self.forecast_plot_agg.height = 300
                self.forecast_plot_agg.object = fig
                self.metrics_df_agg.height = 50
                metrics_df = df[self.agg_granularity.value]
                for metric in self.metrics_list:
                    metric_func = eval(f"metric_{metric}")
                    metrics_df[metric] = metric_func(
                        df["Actual_test"].iloc[0],
                        df[f"Predicted_{self.model_selection_agg_forecast.value}"].iloc[
                            0
                        ],
                    )
                    if metric in self.percentage_metric:
                        metrics_df[metric] = metrics_df[metric] * 100
                metrics_df.rename(
                    columns={k: f"{k} %" for k in self.percentage_metric}, inplace=True
                )
                metrics_df = metrics_df.round(2)
                self.metrics_df_agg.value = metrics_df.set_index(metrics_df.columns[0])

    # ---------------------- Start Date and End Date Handler -----------------

    # To dynamically change the dates based on selection
    def handle_start_date_selection(self, start_date):
        # Select End Date dropdown values based on the value of start date.
        start_dates = np.array(self.forecast_dates)
        self.end_date.options = list(
            start_dates[
                start_dates >= pd.Timestamp(start_date.obj.value, freq=self.data_freq)
            ]
        )

    # To dynamically change the dates based on selection
    def handle_start_date_selection_agg(self, start_date):
        # Select End Date dropdown values based on the value of start date.
        start_dates = np.array(self.forecast_dates)
        self.end_date_agg.options = list(
            start_dates[
                start_dates >= pd.Timestamp(start_date.obj.value, freq=self.data_freq)
            ]
        )

    # To dynamically change the dates based on selection
    def handle_cross_start_date_selection(self, start_date):
        # Select End Date dropdown values based on the value of start date.
        start_dates = np.array(self.forecast_dates)
        self.cross_end_date.options = list(
            start_dates[
                start_dates >= pd.Timestamp(start_date.obj.value, freq=self.data_freq)
            ]
        )

    # To dynamically change the dates based on selection
    def handle_cross_start_date_selection_agg(self, start_date):
        # Select End Date dropdown values based on the value of start date.
        start_dates = np.array(self.forecast_dates)
        self.cross_end_date_agg.options = list(
            start_dates[
                start_dates >= pd.Timestamp(start_date.obj.value, freq=self.data_freq)
            ]
        )

    # To calculate model metrics for different hierarchy
    def get_model_metrics_again(self, event):
        if self.progress.value == 100:
            if self.basic_granularity.value == "All":
                self.basic_model_selection.options = []
                self.basic_model_selection.value = None

                model_metrics = pd.DataFrame(
                    columns=self.metrics_list, index=self.models
                )
                for metric in self.metrics_list:
                    model_metrics[metric] = [
                        self.data[f"{metric}_{model}"].median() for model in self.models
                    ]
                    if metric in self.percentage_metric:
                        model_metrics[metric] = model_metrics[metric] * 100

                model_metrics.rename(
                    columns={k: f"{k} %" for k in self.percentage_metric}, inplace=True
                )
                model_metrics = model_metrics.round(2)
                model_metrics.index.name = "Models"
                model_metrics["Derived_metric"] = (
                    0.2 * (model_metrics["MAPE %"] / 100)
                    + 0.5 * (model_metrics["WMAPE %"] / 100)
                    + 0.3 * (model_metrics["Tracking_Signal"].abs())
                )
                model_metrics.sort_values("Derived_metric", inplace=True)
                del model_metrics["Derived_metric"]
                self.model_metrics_df.value = model_metrics
            else:
                if not self.basic_model_selection.value:
                    self.basic_model_selection.options = self.models
                    self.basic_model_selection.value = self.models[0]

                metric_cols = [
                    f"{metric}_{self.basic_model_selection.value}"
                    for metric in self.metrics_list
                ]
                df = self.data.copy()
                df = (
                    df.groupby(self.basic_granularity.value)[metric_cols]
                    .median()
                    .reset_index()
                )
                for metric in self.metrics_list:
                    if metric in self.percentage_metric:
                        df[f"{metric}_{self.basic_model_selection.value}"] = (
                            df[f"{metric}_{self.basic_model_selection.value}"] * 100
                        )
                        df.rename(
                            columns={
                                f"{metric}_{self.basic_model_selection.value}": f"{metric}_{self.basic_model_selection.value}"
                            },
                            inplace=True,
                        )
                df = df.round(2)
                df.set_index(self.basic_granularity.value, inplace=True)
                df.index.name = f"{self.basic_granularity.value}"
                df["Derived_metric"] = (
                    0.2 * (df[f"MAPE_{self.basic_model_selection.value}"] / 100)
                    + 0.5 * (df[f"WMAPE_{self.basic_model_selection.value}"] / 100)
                    + 0.3
                    * (df[f"Tracking_Signal_{self.basic_model_selection.value}"].abs())
                )
                df.sort_values("Derived_metric", inplace=True)
                del df["Derived_metric"]
                self.model_metrics_df.value = df

    # To calculate overall model metrics for when initializing the dashboard
    def get_model_metrics(self):
        for metric in self.metrics_list:
            metric_func = eval(f"metric_{metric}")
            for model in self.models:
                self.data[f"{metric}_{model}"] = self.data.apply(
                    lambda x: metric_func(x["Actual_test"], x[f"Predicted_{model}"]),
                    axis=1,
                )

        model_metrics = pd.DataFrame(columns=self.metrics_list, index=self.models)
        for metric in self.metrics_list:
            model_metrics[metric] = [
                self.data[f"{metric}_{model}"].median() for model in self.models
            ]
            if metric in self.percentage_metric:
                model_metrics[metric] = model_metrics[metric] * 100

        model_metrics.rename(
            columns={k: f"{k} %" for k in self.percentage_metric}, inplace=True
        )
        model_metrics = model_metrics.round(2)
        model_metrics.index.name = "Models"
        model_metrics["Derived_metric"] = (
            0.2 * (model_metrics["MAPE %"] / 100)
            + 0.5 * (model_metrics["WMAPE %"] / 100)
            + 0.3 * (model_metrics["Tracking_Signal"].abs())
        )
        model_metrics.sort_values("Derived_metric", inplace=True)
        del model_metrics["Derived_metric"]
        self.model_metrics_df.height = 200
        self.model_metrics_df.width = 800
        self.model_metrics_df.value = model_metrics

        # For Aggregated tab
        agg_df = pd.DataFrame()
        for cols in ["Actual_test"] + [f"Predicted_{model}" for model in self.models]:
            agg_df[cols] = (
                self.data.groupby(self.agg_granularity.value)[cols]
                .apply(list)
                .apply(lambda x: np.array(x).sum(0))
            )

        agg_df.reset_index(inplace=True)
        for metric in self.metrics_list:
            metric_func = eval(f"metric_{metric}")
            for model in self.models:
                agg_df[f"{metric}_{model}"] = agg_df.apply(
                    lambda x: metric_func(x["Actual_test"], x[f"Predicted_{model}"]),
                    axis=1,
                )

        model_metrics = pd.DataFrame(columns=self.metrics_list, index=self.models)
        for metric in self.metrics_list:
            model_metrics[metric] = [
                agg_df[f"{metric}_{model}"].median() for model in self.models
            ]
            if metric in self.percentage_metric:
                model_metrics[metric] = model_metrics[metric] * 100

        model_metrics.rename(
            columns={k: f"{k} %" for k in self.percentage_metric}, inplace=True
        )
        model_metrics = model_metrics.round(2)
        model_metrics.index.name = f"Models ({self.agg_granularity.value[0]} level)"
        model_metrics["Derived_metric"] = (
            0.2 * (model_metrics["MAPE %"] / 100)
            + 0.5 * (model_metrics["WMAPE %"] / 100)
            + 0.3 * (model_metrics["Tracking_Signal"].abs())
        )
        model_metrics.sort_values("Derived_metric", inplace=True)
        del model_metrics["Derived_metric"]
        self.model_metrics_df_agg.height = 200
        self.model_metrics_df_agg.width = 800
        self.model_metrics_df_agg.value = model_metrics

    # To calculate model metrics after aggregating the data
    def get_model_metrics_agg(self, event):
        if self.agg_granularity.value:
            agg_df = pd.DataFrame()
            for cols in ["Actual_test"] + [
                f"Predicted_{model}" for model in self.models
            ]:
                agg_df[cols] = (
                    self.data.groupby(self.agg_granularity.value)[cols]
                    .apply(list)
                    .apply(lambda x: np.array(x).sum(0))
                )

            agg_df.reset_index(inplace=True)
            for metric in self.metrics_list:
                metric_func = eval(f"metric_{metric}")
                for model in self.models:
                    agg_df[f"{metric}_{model}"] = agg_df.apply(
                        lambda x: metric_func(
                            x["Actual_test"], x[f"Predicted_{model}"]
                        ),
                        axis=1,
                    )

            model_metrics = pd.DataFrame(columns=self.metrics_list, index=self.models)
            for metric in self.metrics_list:
                model_metrics[metric] = [
                    agg_df[f"{metric}_{model}"].median() for model in self.models
                ]
                if metric in self.percentage_metric:
                    model_metrics[metric] = model_metrics[metric] * 100

            model_metrics.rename(
                columns={k: f"{k} %" for k in self.percentage_metric}, inplace=True
            )
            model_metrics = model_metrics.round(2)
            model_metrics.index.name = (
                f"Models ({' * '.join(self.agg_granularity.value)} level)"
            )
            model_metrics["Derived_metric"] = (
                0.2 * (model_metrics["MAPE %"] / 100)
                + 0.5 * (model_metrics["WMAPE %"] / 100)
                + 0.3 * (model_metrics["Tracking_Signal"].abs())
            )
            model_metrics.sort_values("Derived_metric", inplace=True)
            del model_metrics["Derived_metric"]
            self.model_metrics_df_agg.value = model_metrics
        else:
            met_df = pd.DataFrame()
            for cols in ["Actual_test"] + [
                f"Predicted_{model}" for model in self.models
            ]:
                met_df[cols] = self.data[cols].apply(np.array).values.sum(0).tolist()

            agg_df = pd.DataFrame()
            for metric in self.metrics_list:
                metric_func = eval(f"metric_{metric}")
                for model in self.models:
                    agg_df[f"{metric}_{model}"] = [
                        metric_func(met_df["Actual_test"], met_df[f"Predicted_{model}"])
                    ]

            model_metrics = pd.DataFrame(columns=self.metrics_list, index=self.models)
            for metric in self.metrics_list:
                model_metrics[metric] = [
                    agg_df[f"{metric}_{model}"].median() for model in self.models
                ]
                if metric in self.percentage_metric:
                    model_metrics[metric] = model_metrics[metric] * 100

            model_metrics.rename(
                columns={k: f"{k} %" for k in self.percentage_metric}, inplace=True
            )
            model_metrics = model_metrics.round(2)
            model_metrics.index.name = f"Models (Overall level)"
            model_metrics["Derived_metric"] = (
                0.2 * (model_metrics["MAPE %"] / 100)
                + 0.5 * (model_metrics["WMAPE %"] / 100)
                + 0.3 * (model_metrics["Tracking_Signal"].abs())
            )
            model_metrics.sort_values("Derived_metric", inplace=True)
            del model_metrics["Derived_metric"]
            self.model_metrics_df_agg.value = model_metrics

    # To get the distribution plot with gievn filters
    def get_metrics_dist_plot(self, event):
        indexes = (
            self.forecast_dates.index(self.start_date.value),
            self.forecast_dates.index(self.end_date.value),
        )
        for metric in self.metrics_list:
            self.get_metric_dist_plot(indexes, False, metric)

    # To get the aggregated distribution plot with gievn filters
    def get_metrics_dist_plot_agg(self, event):
        indexes = (
            self.forecast_dates.index(self.start_date_agg.value),
            self.forecast_dates.index(self.end_date_agg.value),
        )
        for metric in self.metrics_list:
            self.get_metric_dist_plot_agg(indexes, False, metric)

    # To get the aggregated distribution plot with gievn filters
    def get_metric_dist_plot_agg(self, indexes, agg, metric):
        if self.agg_granularity.value:
            agg_df = pd.DataFrame()
            agg_df["Actual_test"] = (
                self.data.groupby(self.agg_granularity.value)["Actual_test"]
                .apply(list)
                .apply(lambda x: np.array(x).sum(0))
            )

            for model in self.models:
                agg_df[f"Predicted_{model}"] = (
                    self.data.groupby(self.agg_granularity.value)[f"Predicted_{model}"]
                    .apply(list)
                    .apply(lambda x: np.array(x).sum(0))
                )

            count_df = self.get_filtered_score_all_agg(agg_df, metric, *indexes)

            plot = (
                self.agg_mape_dist_plot
                if agg
                else eval(f"self.{metric.lower()}_dist_plot_agg")
            )
            plot.object = self.get_countplot(count_df, metric=metric)
        else:
            for plot in self.metrics_dist_plot_list_agg:
                plot.object = None

    # To get the distribution plot with gievn filters
    def get_metric_dist_plot(self, indexes, agg, metric):
        df = self.data.copy()

        for filtr in self.gran_filters_dist_plot:
            if filtr.value:
                df = df[df[filtr.name] == filtr.value[0]]

        count_df = self.get_filtered_score_all(df, metric, *indexes)

        plot = (
            self.agg_mape_dist_plot if agg else eval(f"self.{metric.lower()}_dist_plot")
        )
        plot.object = self.get_countplot(count_df, metric=metric)

    # Function to calculate the bin frequency all metrics
    def get_filtered_score_all(self, df, metric, start, end):
        actual_predicted_ts = pd.DataFrame()

        if metric in self.percentage_metric:
            bins = self.bins
        else:
            bins = eval(f"self.{metric.lower()}_bins_axis")

        if (end - start) + 1 == self.prediction_length:
            df_res = pd.DataFrame(
                {
                    model_name: pd.cut(
                        df[f"{metric}_{model_name}"] * 100
                        if metric in self.percentage_metric
                        else df[f"{metric}_{model_name}"],
                        bins=bins,
                    )
                    .value_counts(sort=False)
                    .values
                    for model_name in self.models
                }
            )

        else:
            actual_predicted_ts["actual_ts_slice"] = np.array(
                df["Actual_test"].apply(lambda x: x[start : end + 1])
            )
            for model in self.models:
                actual_predicted_ts[f"predicted_ts_slice_{model}"] = np.array(
                    df[f"Predicted_{model}"].apply(lambda x: x[start : end + 1])
                )

            metric_func = eval(f"metric_{metric}")

            if metric in self.percentage_metric:
                df_res = pd.DataFrame(
                    {
                        model_name: pd.cut(
                            pd.Series(
                                actual_predicted_ts.apply(
                                    lambda x: metric_func(
                                        x["actual_ts_slice"],
                                        x[f"predicted_ts_slice_{model_name}"],
                                    ),
                                    axis=1,
                                )
                            ).multiply(100),
                            bins=bins,
                        )
                        .value_counts(sort=False)
                        .values
                        for model_name in self.models
                    }
                )
            else:
                df_res = pd.DataFrame(
                    {
                        model_name: pd.cut(
                            pd.Series(
                                actual_predicted_ts.apply(
                                    lambda x: metric_func(
                                        x["actual_ts_slice"],
                                        x[f"predicted_ts_slice_{model_name}"],
                                    ),
                                    axis=1,
                                )
                            ),
                            bins=bins,
                        )
                        .value_counts(sort=False)
                        .values
                        for model_name in self.models
                    }
                )

        df_res["score_bins"] = [str(i) for i in bins]
        df_res["colors"] = Spectral5
        return df_res

    # Function to calculate the bin frequency all metrics
    def get_filtered_score_all_agg(self, df, metric, start, end):
        actual_predicted_ts = pd.DataFrame()
        actual_predicted_ts["actual_ts_slice"] = np.array(
            df["Actual_test"].apply(lambda x: x[start : end + 1])
        )
        for model in self.models:
            actual_predicted_ts[f"predicted_ts_slice_{model}"] = np.array(
                df[f"Predicted_{model}"].apply(lambda x: x[start : end + 1])
            )

        metric_func = eval(f"metric_{metric}")

        if metric in ["MAPE", "WMAPE"]:
            bins = self.bins
        else:
            bins = eval(f"self.{metric.lower()}_bins_axis")

        if metric in ["MAPE", "WMAPE"]:
            df_res = pd.DataFrame(
                {
                    model_name: pd.cut(
                        pd.Series(
                            actual_predicted_ts.apply(
                                lambda x: metric_func(
                                    x["actual_ts_slice"],
                                    x[f"predicted_ts_slice_{model_name}"],
                                ),
                                axis=1,
                            )
                        ).multiply(100),
                        bins=bins,
                    )
                    .value_counts(sort=False)
                    .values
                    for model_name in self.models
                }
            )
        else:
            df_res = pd.DataFrame(
                {
                    model_name: pd.cut(
                        pd.Series(
                            actual_predicted_ts.apply(
                                lambda x: metric_func(
                                    x["actual_ts_slice"],
                                    x[f"predicted_ts_slice_{model_name}"],
                                ),
                                axis=1,
                            )
                        ),
                        bins=bins,
                    )
                    .value_counts(sort=False)
                    .values
                    for model_name in self.models
                }
            )

        df_res["score_bins"] = [str(i) for i in bins]
        df_res["colors"] = Spectral5
        return df_res

    # To convert the metrics bin frequency into plot
    def get_countplot(self, count_df, metric):
        source = ColumnDataSource(data=count_df)
        x_range = count_df["score_bins"]

        # Create the Figure: fig
        fig = figure(
            x_axis_label="Score Bins",
            y_axis_label="# Time Series",
            plot_width=600,
            plot_height=300,
            x_range=x_range,
            title=f"{metric} Score Distribution",
        )

        hover_tool_bars = []

        if len(self.models) == 1:
            bin_range_value = [0]
            width = 0.2

        elif len(self.models) == 2:
            bin_range_value = [-0.1, 0.1]
            width = 0.2

        elif len(self.models) == 3:
            bin_range_value = [-0.2, 0, 0.2]
            width = 0.2

        elif len(self.models) == 4:
            bin_range_value = [-0.25, -0.1, 0.05, 0.2]
            width = 0.15

        elif len(self.models) == 5:
            bin_range_value = [-0.25, -0.1, 0.05, 0.2, 0.35]
            width = 0.15

        elif len(self.models) == 6:
            bin_range_value = [-0.3, -0.2, -0.1, 0, 0.1, 0.2]
            width = 0.1

        for i, model_name in enumerate(self.models[:6]):
            vbar = fig.vbar(
                x=dodge("score_bins", bin_range_value[i], range=fig.x_range),
                top=model_name,
                width=width,
                source=source,
                color=Spectral6[i],
                legend=value(model_name),
            )
            hover_tool_vbar = HoverTool(
                tooltips=[(model_name, f"@{model_name}")],
                show_arrow=False,
                renderers=[vbar],
            )
            hover_tool_bars.append(hover_tool_vbar)

        fig.x_range.range_padding = width
        fig.xgrid.grid_line_color = None
        fig.legend.location = "top_right"
        fig.legend.glyph_height = 14
        fig.legend.glyph_width = 14
        fig.legend.label_text_font_size = "12px"
        fig.legend.click_policy = "hide"
        fig.legend.orientation = "horizontal"

        fig.add_tools(*tuple(hover_tool_bars))

        return fig

    # To get the cross table distribution for any 2 given metrics
    def get_cross_table(self, event):
        indexes = (
            self.forecast_dates.index(self.cross_start_date.value),
            self.forecast_dates.index(self.cross_end_date.value),
        )
        index, column = self.x_axis_metrics.value, self.y_axis_metrics.value

        if index in self.percentage_metric:
            index_bins = self.bins
        else:
            index_bins = eval(f"self.{index.lower()}_bins_axis")

        if column in self.percentage_metric:
            column_bins = self.bins
        else:
            column_bins = eval(f"self.{column.lower()}_bins_axis")

        if (indexes[1] - indexes[0]) + 1 == self.prediction_length:
            index_filtered_scores = pd.cut(
                self.data[f"{index}_{self.model_selection.value}"] * 100
                if index in self.percentage_metric
                else self.data[f"{index}_{self.model_selection.value}"],
                bins=index_bins,
            )
            columns_filtered_scores = pd.cut(
                self.data[f"{column}_{self.model_selection.value}"] * 100
                if column in self.percentage_metric
                else self.data[f"{column}_{self.model_selection.value}"],
                bins=column_bins,
            )

        else:
            index_filtered_scores = pd.cut(
                self.get_filtered_score(self.data, index, *indexes), bins=index_bins,
            )
            columns_filtered_scores = pd.cut(
                self.get_filtered_score(self.data, column, *indexes), bins=column_bins,
            )

        df = pd.crosstab(index=index_filtered_scores, columns=columns_filtered_scores)
        df.index = index + "_" + df.index.astype(str)
        df.columns = column + "_" + df.columns.astype(str)
        df["Total Time Series"] = df.sum(1)
        df = df.T
        df["Total Time Series"] = df.sum(1)
        df = df.T
        df.index.name = self.model_selection.value
        self.crosstab_df.height = 200
        self.crosstab_df.value = df

    # To get the aggregate cross table distribution for any 2 given metrics
    def get_cross_table_agg(self, event):
        if self.agg_granularity.value:
            indexes = (
                self.forecast_dates.index(self.cross_start_date_agg.value),
                self.forecast_dates.index(self.cross_end_date_agg.value),
            )
            index, column = (
                self.x_axis_metrics_agg.value,
                self.y_axis_metrics_agg.value,
            )

            if index in self.percentage_metric:
                index_bins = self.bins
            else:
                index_bins = eval(f"self.{index.lower()}_bins_axis")

            if column in self.percentage_metric:
                column_bins = self.bins
            else:
                column_bins = eval(f"self.{column.lower()}_bins_axis")

            agg_df = pd.DataFrame()
            agg_df["Actual_test"] = (
                self.data.groupby(self.agg_granularity.value)["Actual_test"]
                .apply(list)
                .apply(lambda x: np.array(x).sum(0))
            )
            agg_df[f"Predicted_{self.model_selection_agg.value}"] = (
                self.data.groupby(self.agg_granularity.value)[
                    f"Predicted_{self.model_selection_agg.value}"
                ]
                .apply(list)
                .apply(lambda x: np.array(x).sum(0))
            )
            index_filtered_scores = pd.cut(
                self.get_filtered_score_agg(agg_df, index, *indexes), bins=index_bins,
            )
            columns_filtered_scores = pd.cut(
                self.get_filtered_score_agg(agg_df, column, *indexes), bins=column_bins,
            )

            df = pd.crosstab(
                index=index_filtered_scores, columns=columns_filtered_scores
            )
            df.index = index + "_" + df.index.astype(str)
            df.columns = column + "_" + df.columns.astype(str)
            df["Total Time Series"] = df.sum(1)
            df = df.T
            df["Total Time Series"] = df.sum(1)
            df = df.T
            df.index.name = self.model_selection_agg.value
            self.crosstab_df_agg.height = 200
            self.crosstab_df_agg.value = df
        else:
            self.crosstab_df_agg.height = 0

    # Function to calculate the bin frequency all metrics
    def get_filtered_score(self, df, metric, start, end):
        actual_predicted_ts = pd.DataFrame()
        actual_predicted_ts["actual_ts_slice"] = np.array(
            df["Actual_test"].apply(lambda x: x[start : end + 1])
        )
        actual_predicted_ts["predicted_ts_slice"] = np.array(
            df[f"Predicted_{self.model_selection.value}"].apply(
                lambda x: x[start : end + 1]
            )
        )

        metric_func = eval(f"metric_{metric}")

        if metric in self.percentage_metric:
            return pd.Series(
                actual_predicted_ts.apply(
                    lambda x: metric_func(
                        x["actual_ts_slice"], x["predicted_ts_slice"]
                    ),
                    axis=1,
                )
            ).multiply(100)
        else:
            return pd.Series(
                actual_predicted_ts.apply(
                    lambda x: metric_func(
                        x["actual_ts_slice"], x["predicted_ts_slice"]
                    ),
                    axis=1,
                )
            )

    # Function to calculate the bin frequency all metrics
    def get_filtered_score_agg(self, df, metric, start, end):
        actual_predicted_ts = pd.DataFrame()
        actual_predicted_ts["actual_ts_slice"] = np.array(
            df["Actual_test"].apply(lambda x: x[start : end + 1])
        )
        actual_predicted_ts["predicted_ts_slice"] = np.array(
            df[f"Predicted_{self.model_selection_agg.value}"].apply(
                lambda x: x[start : end + 1]
            )
        )

        metric_func = eval(f"metric_{metric}")

        if metric in self.percentage_metric:
            return pd.Series(
                actual_predicted_ts.apply(
                    lambda x: metric_func(
                        x["actual_ts_slice"], x["predicted_ts_slice"]
                    ),
                    axis=1,
                )
            ).multiply(100)
        else:
            return pd.Series(
                actual_predicted_ts.apply(
                    lambda x: metric_func(
                        x["actual_ts_slice"], x["predicted_ts_slice"]
                    ),
                    axis=1,
                )
            )

    # Returns Dashboard
    def return_dash(self):

        # Models summary plot
        models_summary = pn.Column(
            self.models_summary_heading,
            pn.Row(
                self.basic_granularity,
                pn.Spacer(margin=20),
                self.basic_model_selection,
                align="center",
            ),
            pn.pane.Markdown(
                "#### Table showing median values of metrics across time series",
                align="center",
            ),
            self.model_metrics_df,
            align="center",
        )

        # Metrics Distribution plot
        metrics_distribution = pn.Column(
            self.metrics_heading,
            pn.panel(
                pn.Column(
                    pn.Column(
                        pn.Row(
                            self.gran_filters_dist_plot,
                            pn.Spacer(width=10),
                            self.start_date,
                            #                             pn.Spacer(width=10),
                            self.end_date,
                            pn.Spacer(width=5),
                            self.metrics_dist_btn,
                        ),
                        margin=(5, 5, 5, 10),
                        align="center",
                    ),
                    pn.Spacer(height=1, width=1240),
                    pn.Column(
                        pn.Row(
                            pn.Spacer(width=5),
                            self.mape_dist_plot,
                            pn.Spacer(width=5),
                            self.wmape_dist_plot,
                            pn.Spacer(width=5),
                        ),
                        pn.Spacer(height=5, width=5),
                        pn.Row(
                            pn.Spacer(width=5),
                            self.mad_dist_plot,
                            pn.Spacer(width=5),
                            # self.bias_dist_plot,
                            self.tracking_signal_dist_plot,
                            pn.Spacer(width=5),
                        ),
                    ),
                    pn.Spacer(height=0, width=5),
                )
            ),
            align="center",
        )

        # Forecast Plot
        ts_forecast_plot = pn.Column(
            self.forecast_heading,
            pn.panel(
                pn.Column(
                    pn.Row(
                        self.gran_filters,
                        pn.Spacer(width=10),
                        self.idv_cols,
                        self.model_selection_forecast,
                        self.metric_filters,
                        #                              pn.Column(self.reset_filter_btn),
                    ),
                    pn.Spacer(height=50),
                    pn.Column(self.forecast_plot),
                    pn.Spacer(height=50),
                    pn.Row(pn.Spacer(width=200), self.metrics_df),
                    pn.Spacer(height=40),
                    pn.Row(pn.Spacer(width=200), self.waterfall_plot),
                )
            ),
            align="center",
        )

        # Cross Tab
        cross_tab = pn.Column(
            self.crosstable_heading,
            pn.Row(
                pn.panel(
                    pn.Column(
                        pn.Row(
                            self.model_selection,
                            self.cross_start_date,
                            self.cross_end_date,
                            self.x_axis_metrics,
                            self.y_axis_metrics,
                            pn.Spacer(width=10),
                            self.crosstab_btn,
                        ),
                        pn.pane.Markdown(
                            "#### Table showing # Time Series falling under each bucket",
                            align="center",
                        ),
                        pn.Column(self.crosstab_df, align="center"),
                    ),
                ),
                pn.Spacer(sizing_mode="stretch_both"),
            ),
            align="center",
        )

        self.ts_level_tab.append(
            (
                "Time Series Level",
                pn.Column(
                    models_summary,
                    pn.Spacer(height=50),
                    metrics_distribution,
                    pn.Spacer(height=50),
                    cross_tab,
                    pn.Spacer(height=50),
                    ts_forecast_plot,
                ),
            )
        )

        # Models summary plot
        models_summary_agg = pn.Column(
            self.models_summary_heading,
            pn.pane.Markdown(
                "#### Table showing median values of metrics across time series",
                align="center",
            ),
            self.model_metrics_df_agg,
            align="center",
        )

        #         Metrics Distribution plot
        metrics_distribution_agg = pn.Column(
            self.metrics_heading,
            pn.panel(
                pn.Column(
                    pn.Column(
                        pn.Row(
                            self.start_date_agg,
                            pn.Spacer(width=10),
                            self.end_date_agg,
                            pn.Spacer(width=5),
                            self.metrics_dist_btn_agg,
                        ),
                        margin=(5, 5, 5, 10),
                        align="center",
                    ),
                    pn.Spacer(height=1, width=1240),
                    pn.Column(
                        pn.Row(
                            pn.Spacer(width=5),
                            self.mape_dist_plot_agg,
                            pn.Spacer(width=5),
                            self.wmape_dist_plot_agg,
                            pn.Spacer(width=5),
                        ),
                        pn.Spacer(height=5, width=5),
                        pn.Row(
                            pn.Spacer(width=5),
                            self.mad_dist_plot_agg,
                            pn.Spacer(width=5),
                            # self.bias_dist_plot_agg,
                            self.tracking_signal_dist_plot_agg,
                            pn.Spacer(width=5),
                        ),
                    ),
                    pn.Spacer(height=0, width=5),
                ),
            ),
            align="center",
        )

        # Cross Tab
        cross_tab_agg = pn.Column(
            self.crosstable_heading,
            pn.Row(
                pn.panel(
                    pn.Column(
                        pn.Row(
                            self.model_selection_agg,
                            self.cross_start_date_agg,
                            self.cross_end_date_agg,
                            self.x_axis_metrics_agg,
                            self.y_axis_metrics_agg,
                            pn.Spacer(width=10),
                            self.crosstab_btn_agg,
                            align="center",
                        ),
                        pn.pane.Markdown(
                            "#### Table showing # Time Series falling under each bucket",
                            align="center",
                        ),
                        pn.Column(self.crosstab_df_agg, align="center"),
                    ),
                ),
                pn.Spacer(sizing_mode="stretch_both"),
            ),
            align="center",
        )

        # Forecast Plot
        ts_forecast_plot_agg = pn.Column(
            self.forecast_heading,
            pn.panel(
                pn.Column(
                    pn.Row(
                        self.gran_filters_agg,
                        pn.Spacer(width=10),
                        self.idv_cols_agg,
                        self.model_selection_agg_forecast,
                        self.metric_filters_agg,
                        align="center",
                    ),
                    pn.Spacer(height=50),
                    pn.Column(self.forecast_plot_agg),
                    pn.Spacer(height=50),
                    pn.Row(pn.Spacer(width=200), self.metrics_df_agg),
                    pn.Spacer(height=40),
                    pn.Row(pn.Spacer(width=200), self.waterfall_plot_agg),
                )
            ),
            align="center",
        )

        self.ts_level_tab.append(
            (
                "Aggregated Level",
                pn.Column(
                    pn.Row(
                        self.agg_granularity,
                        pn.Spacer(width=20),
                        self.agg_granularity_btn,
                    ),
                    pn.pane.Markdown(
                        "#### Selection applies to the full tab", margin=(0, 0, 0, 10)
                    ),
                    models_summary_agg,
                    pn.Spacer(height=50),
                    metrics_distribution_agg,
                    pn.Spacer(height=50),
                    cross_tab_agg,
                    pn.Spacer(height=50),
                    ts_forecast_plot_agg,
                ),
            )
        )

        dashboard = pn.Column(
            self.dash_heading,
            pn.Row(
                pn.pane.Markdown(
                    "### Select experiment name: ", margin=(25, 40, 30, 20)
                ),
                self.experiment_name,
                pn.Spacer(width=20),
                self.experiment_name_btn,
                pn.Spacer(width=20),
                self.progress,
                pn.Spacer(width=20),
                self.progress_text,
            ),
            self.ts_level_tab,
            css_classes=["gray_bg"],
        )
        # dashboard.show(title='Model Evaluation Dashboard')
        return dashboard


def generate_dashboard():

    ds = ModelEvaluation()
    dashboard = ds.return_dash()
    return dashboard.servable()


generate_dashboard()
