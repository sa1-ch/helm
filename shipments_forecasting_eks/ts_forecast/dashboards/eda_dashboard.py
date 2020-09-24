import gzip
import json
import math
import os
import warnings
from datetime import datetime
from functools import reduce

import boto3
import holoviews as hv
import numpy as np
import pandas as pd
import panel as pn
import ruptures as rpt
import s3fs
import seaborn as sns
import yaml
from bokeh.events import Tap
from bokeh.models import (
    ColumnDataSource,
    DataTable,
    HoverTool,
    Legend,
    LinearAxis,
    Range1d,
    TableColumn,
)
from bokeh.models.formatters import DatetimeTickFormatter, NumeralTickFormatter
from bokeh.models.widgets import Div
from bokeh.plotting import figure
from gluonts.dataset.common import BasicFeatureInfo, CategoricalFeatureInfo, MetaData
from gluonts.dataset.field_names import FieldName
from luminol import anomaly_detector

warnings.filterwarnings("ignore")




css = """
.widget_background {
  overflow: auto;
  background: #f5f5f5;
}
.tabs .bk-active, .tabs .bk-btn:hover {
  background: #F68F25 !important;
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
    padding: 5px !important;
    font-weight: bold;
    font-size: 14px !important;
    text-align: center
}
.flags_title {
    border: 0 !important;
    background: #3D5366 !important;
    color: #fff !important;
    padding: 5px !important;
    font-weight: bold;
    font-size: 10px !important;
    text-align: center !important;
}
.univ_title {
    border: 0 !important;
    background: #3D5366 !important;
    color: #fff !important;
    padding: 5px !important;
    font-weight: bold;
    font-size: 10px !important;
    text-align: center !important;
    width: 950px !important;
}
.headers_css {
    border: 0 !important;
    background: #3D5366 !important;
    color: #fff !important;
    font-size:12px !important;
    font-weight: bold;
    font-width: 220px !important;
    text-align: center !important;
}
.custom_select .bk-input {
     min-height: 40px !important;
    background-color: #F2EFC7;
    font-size: 14px !important;
    padding: 10px;
    -moz-appearance: none;
    -webkit-appearance: none;
    border-radius: 0;
}
.custom_secondary .bk-input {
     background-color: #F7FFE0;
     font-size: 14px !important;
     padding: 10px;
     -moz-appearance: none;
     -webkit-appearance: none;
     border-radius: 0;
}
.gray_bg {
  background: #F7FFE0;
}
.gray_bg_univ {
  background: #F7FFE0;
  min-height: 500px;
}
"""


pn.extension(raw_css=[css])
hv.extension("bokeh")

def load_yaml(file):
    with open(file, "r") as fp:
        config = yaml.load(fp, Loader=yaml.SafeLoader)

    return config


package_dir = os.path.dirname(os.path.abspath(__file__))
creds_file = load_yaml(os.path.join(package_dir, "..", "..", "configs/dev.yml"))



class data_interaction:
    def __init__(self, data, callback=None):

        # Initialise all components

        self._declare_components(data)
        # Data loader
        self.selected_files = []
        self.data_files = []
        self.file_map = {}
        self.load_data_file = pn.widgets.Select(
            options=self.data_files,
            name="Selected Files",
            width=250,
            css_classes=["custom_secondary"],
        )
        self.load_button = pn.widgets.Button(
            name="Load Data",
            css_classes=["primary", "button"],
            disabled=len(self.selected_files) > 0,
            width=250,
            height=40,
        )
        self.current_file = None
        self.data_1 = None
        self.callback = callback
        if callback:
            self.load_button.on_click(self.pass_data_to)
        else:
            self.load_button.js_on_click(code="location.reload();")
        self.select_files_button = pn.widgets.Button(
            name="Select files from computer",
            css_classes=["tertiary", "button"],
            width=250,
            height=40,
        )
        self.minimised_view = pn.WidgetBox(
            pn.Row(
                pn.Column(pn.Spacer(height=8), self.select_files_button),
                self.load_data_file,
                pn.Column(pn.Spacer(height=8), self.load_button),
                css_classes=["is_visible", "gray_bg"],
            )
        )
        self.is_selecting = False
        self.select_files_button.on_click(self.start_selection)
        self.select_files = pn.widgets.FileSelector(
            "/", file_pattern="*.[cxt][sl][vs]*"
        )
        self.selected_files_summary = pn.widgets.StaticText()
        self.add_selected_files = pn.widgets.Button(
            name="Add Selected Files", css_classes=["primary", "button", "is_hidden"]
        )
        self.cancel_selection = pn.widgets.Button(
            name="Cancel", css_classes=["primary", "button"]
        )
        self.select_files.link(
            self.add_selected_files, {"value": self.toggle_add_button}
        )
        self.add_selected_files.on_click(self.add_to_files)
        self.cancel_selection.on_click(self.end_selection)
        self.selection_widget = pn.Column(
            self.select_files,
            self.selected_files_summary,
            pn.Row(self.cancel_selection, self.add_selected_files),
        )
        self.data_loader = pn.Column(self.minimised_view)
        s3 = boto3.resource('s3')
        my_bucket = s3.Bucket('tiger-mle-tg')
        list_of_files = []
        for object_summary in my_bucket.objects.filter(Prefix="inputs/dashboard-input/"):
            if object_summary.key.find('.csv') != -1:
                list_of_files.append(object_summary.key.rsplit('/',1)[1])
        
        self.file_selection_drop = pn.widgets.Select(
            options = list_of_files,
            value = 'Demo_data_17k.csv',
            width=250,
            css_classes=["custom_secondary"]
            )
        self.file_choose_button = pn.widgets.Button(
            name="Load Data",
            css_classes=["primary", "button"],
            width=250,
            height=40
            )
        self.file_choose_button.on_click(self.load_data_drop)

    def _declare_components(self, data):
        self.data = data
        self.comments_table = pd.DataFrame()
        
        # Declaring widgets for all tabs and lists to store tables
        # Headers

        self.heading1 = pn.pane.Markdown("""# Data Interaction""")
        self.heading2 = pn.pane.Markdown("""# Data Summary""", align="center")
        self.heading3 = pn.pane.Markdown(
            """<h2> Time Series Exploration""",
            align="center",
            width=220,
            height=40,
            css_classes=["headers_css"],
        )
        a = "Click the Accept button to generate flags based on thresholds"
        self.heading7 = pn.pane.Markdown("<h4>" + a, min_width=800, max_height=35)
        self.heading4 = pn.pane.Markdown(
            """<h2> Univariate Analysis""",
            max_height=40,
            width=220,
            css_classes=["headers_css"],
        )
        a = "Visualise basic statistics, time series exploration and data interaction"
        b = "over time across 3 tabs "
        self.heading5 = pn.pane.Markdown("<h2>" + a + b, max_height=20)

        a = "Pick time variable, frequency of forecast,"
        b = "data field to be forecasted, variables to identify unique time series"
        self.heading8 = pn.pane.Markdown("<h4>" + a + b, max_height=15)

        a = "The selections made will be used across all tabs for analysis"
        self.heading9 = pn.pane.Markdown("<h5>" + a, max_height=15)
        self.heading6 = pn.pane.Markdown(
            """<h2> Time Series Statistics""",
            align="center",
            width=220,
            max_height=40,
            css_classes=["headers_css"],
        )
        self.heading10 = pn.pane.Markdown(
            """<h5> * Applicable for basic statistics page only""",
            align="center",
            max_height=5,
        )
        self.heading11 = pn.pane.Markdown(
            """<h2> Load Data""", max_height=40, width=220, css_classes=["headers_css"]
        )
        self.heading12 = pn.widgets.StaticText(width=1200)
        self.heading15 = pn.widgets.StaticText()
        self.heading16 = pn.widgets.StaticText()

        self.reason_list = [
            "Reason1",
            "Reason2",
            "Reason3",
            "Reason4",
            "Reason5",
            "Reason6",
            "Reason7",
            "Reason8",
            "Reason9",
            "Reason10",
            "Others",
        ]
        # Interaction tab elements
        self.x_var = pn.widgets.Select(
            width=200,
            name="Select primary variable",
            margin=10,
            css_classes=["custom_secondary"],
        )
        self.y_var = pn.widgets.Select(
            width=200,
            name="Select secondary variable",
            margin=10,
            css_classes=["custom_secondary"],
        )
        self.interaction_select = pn.widgets.MultiChoice(
            name="Select Heirarchy",
            margin=10,
            width=250,
            css_classes=["custom_secondary"],
        )
        self.hier_button = pn.widgets.Button(
            name="Get granular dropdowns",
            width=250,
            button_type="primary",
            css_classes=["primary", "button"],
        )
        self.hier_button.on_click(self.update_dropdowns)
        self.plot = pn.pane.Bokeh()
        self.plot_dense = pn.pane.Matplotlib()
        self.button_upd = pn.widgets.Button(
            name="Update Plot",
            width=250,
            button_type="primary",
            margin=10,
            css_classes=["primary", "button"],
        )
        self.button_upd.on_click(self.get_plot)
        self.dash = pn.WidgetBox()
        self.dropdowns = pn.panel(pn.Column())
        self.low_value_plot = pn.pane.Bokeh()
        self.dynamic_drops = pn.Row()
        self.flags_panel = pn.Row()
        self.flags_dropdown = pn.panel(pn.Column())
        self.cat_heading = pn.widgets.StaticText()
        self.cont_heading = pn.widgets.StaticText()
        self.drops = []
        self.drops_2 = []
        self.flags_drops_2 = []
        self.prediction_length = pn.widgets.IntSlider(
            name="Select Forecast Window", start=1, end=16, value=8, step=1, width=250
        )
        self.experiment_name = pn.widgets.TextInput(
            placeholder="Enter experiment_name", width=250
        )
        self.data_frequency = pn.widgets.Select(
            name="Select Frequency of forecast",
            margin=10,
            width=200,
            css_classes=["custom_secondary"],
        )
        self.progress = pn.widgets.Progress(
            name="Calculating metrics", value=0, width=250, height=25, disabled=True
        )
        self.progress_text = pn.widgets.StaticText(value = 'Progress bar')
        self.comment_box = pn.panel(pn.Column())
        self.outlier_table = pn.widgets.DataFrame(
            name="DataFrame", width=1200, fit_columns=True
        )
        self.show_table = pn.widgets.Button(
            name="Show outliers and changepoints tags",
            button_type="primary",
            width=250,
            css_classes=["primary", "button"],
        )
        self.show_table.on_click(self.get_comments_table)
        self.gluonts_data = pn.widgets.Button(
            name="Create data for modelling",
            button_type="primary",
            width=250,
            css_classes=["primary", "button"],
        )
        self.gluonts_data.on_click(self.prepare_gluonts_data)
        
        # Widgets to select DV, Date Column, granularity and heirarchy of the data

        self.dv_select = pn.widgets.Select(
            width=200,
            name="Select Data field to forecast",
            margin=10,
            css_classes=["custom_secondary"],
        )
        self.date_select = pn.widgets.Select(
            width=200,
            name="Select Time variable",
            margin=10,
            css_classes=["custom_secondary"],
        )
        self.heir_select = pn.widgets.MultiChoice(
            name="Select Aggregation Hierarchy for Time series Statistics (optional)",
            margin=10,
            width=280,
            css_classes=["custom_secondary"],
        )
        self.gran_select = pn.widgets.MultiChoice(
            name="Select granularity of time series",
            margin=10,
            width=280,
            css_classes=["custom_secondary"],
            max_height = 40
        )
        self.pareto_select = pn.widgets.Select(
            width=200, name="Select aggregate level", margin=10
        )

        # Widgets for getting uniques values and also the summary dateframe

        self.data_cols = pn.widgets.Select(
            options=list(data.columns),
            width=200,
            name="Select column to view univariate statistics",
            margin=10,
            css_classes=["custom_secondary"],
        )
        self.univar = pn.widgets.DataFrame(
            name="Univariate summary",
            height=50,
            width=950,
            fit_columns=True,
            sizing_mode="stretch_width",
        )
        self.univar_2 = pn.widgets.DataFrame(
            name="Univariate summary",
            height=50,
            width=950,
            fit_columns=True,
            sizing_mode="stretch_width",
        )
        self.univariate_button = pn.widgets.Button(
            name="Click to get univariate statistics",
            button_type="primary",
            width=200,
            margin = 10,
            css_classes=["primary", "button"],
        )
        self.univariate_button.on_click(self.num_unique)
        self.heir_dataframe = pn.widgets.DataFrame(
            pd.DataFrame(), name="DataFrame", width=1200, fit_columns=True
        )
        self.button = pn.widgets.Button(
            name="Start Processing",
            button_type="primary",
            height=40,
            css_classes=["primary", "button"],
        )
        self.button.on_click(self.num_series)
        self.flag_plot = pn.WidgetBox()
        self.line_plot = pn.pane.Bokeh()
        self.table_button = pn.widgets.Button(
            name="Accept", button_type="primary", css_classes=["primary", "button"],
        )
        self.table_button.on_click(self.update_table)
        self.progress_load = pn.widgets.Progress(
            name="Loading data", value=100, width=250, height=25, disabled=False
        )
        self.progress_load_text = pn.widgets.StaticText(value = 'Data loaded')
        self.likely_cat = {}
        self.cat_vars = []
        self.cont_vars = []
        self.date_vars = []
        self.interaction_list = []
        self.data_explore_tab = pn.Tabs()
        self.return_interaction_tab()

    def initialise_data(self, data):
        # On Load data, variables/widgets re-initialised
        self.data = data
        self.comments_table = pd.DataFrame()
        self.low_value_plot = pn.pane.Bokeh()
        self.heading15 = pn.widgets.StaticText()
        self.heading16 = pn.widgets.StaticText()
        self.flags_panel = pn.Row()
        self.flags_dropdown = pn.panel(pn.Column())
        self.drops = []
        self.drops_2 = []
        self.flags_drops_2 = []
        self.flag_plot = pn.WidgetBox()
        self.line_plot = pn.pane.Bokeh()
        self.likely_cat = {}
        self.cat_vars = []
        self.cont_vars = []
        self.date_vars = []
        self.interaction_list = []
        self.return_interaction_tab()
       

    def get_comments_table(self, event):
            if 'Index' in self.comments_table.columns:
                self.comments_table.drop(["Index"], inplace=True, axis=1)
                # Ordering columns
                if (len(self.interaction_list) > 0) | (len(self.gran_select.value) > 0):
                    new_cols = (np.unique(
                        self.gran_select.value + self.interaction_list).tolist())
                    col_order = new_cols + (
                            self.comments_table.columns.drop(new_cols).tolist())
                    self.comments_table = self.comments_table[col_order]
            self.outlier_table.value = self.comments_table
            self.outlier_table.height = 200

    def num_series(self, event):
        self.data[self.gran_select.value] = self.data[self.gran_select.value].astype(
            str
        )
        t_df = self.data
        col_left = self.gran_select.value.copy()
        for col in self.heir_select.value:
            col_left.remove(col)

        # If some heirarchy is selected
        if self.heir_select.value:
            tmp_df = (
                t_df.groupby(self.heir_select.value)
                .agg(
                    {
                        self.date_select.value: [min, max],
                        self.dv_select.value: [
                            lambda x: x.isnull().sum(),
                            sum,
                            "mean",
                            "var",
                            lambda x: np.percentile(x, 5),
                            lambda x: np.percentile(x, 25),
                            lambda x: np.percentile(x, 75),
                            lambda x: np.percentile(x, 95),
                            "median",
                        ],
                    }
                )
                .reset_index()
            )
            tmp_df.columns = self.heir_select.value + [
                "Start_date",
                "End_date",
                "# Missing",
                "Sum",
                "Mean",
                "Variance",
                "5th Percentile",
                "25th Percentile",
                "75th Percentile",
                "95th Percentile",
                "Median",
            ]
            tmp_df["# data_points"] = t_df.groupby(self.heir_select.value).size().values
            if col_left:
                tmp_df["# time_series"] = (
                    t_df.groupby(self.gran_select.value)
                    .size()
                    .groupby(self.heir_select.value)
                    .size()
                    .values
                )
            else:
                tmp_df["# time_series"] = (
                    t_df.groupby(self.heir_select.value)[self.heir_select.value[0]]
                    .nunique()
                    .values
                )
            tmp_df = tmp_df[
                self.heir_select.value
                + [
                    "Start_date",
                    "End_date",
                    "# data_points",
                    "# Missing",
                    "# time_series",
                    "Sum",
                    "Mean",
                    "Variance",
                    "5th Percentile",
                    "25th Percentile",
                    "Median",
                    "75th Percentile",
                    "95th Percentile",
                ]
            ]
            tmp_df.set_index(self.heir_select.value[0], inplace=True)
            self.heir_dataframe.height = 500
        # IF no heirarchy is selected
        else:
            tmp_df = pd.DataFrame()
            tmp_df["Start_date"] = [t_df[self.date_select.value].min()]
            tmp_df["End_date"] = [t_df[self.date_select.value].max()]
            tmp_df["# Missing"] = [t_df[self.dv_select.value].isnull().sum()]
            tmp_df["# data_points"] = [t_df.shape[0]]
            tmp_df["# time_series"] = [
                t_df[self.gran_select.value].drop_duplicates().shape[0]
            ]
            tmp_df["Sum"] = [t_df[self.dv_select.value].sum()]
            tmp_df["Mean"] = [t_df[self.dv_select.value].mean()]
            tmp_df["Variance"] = [t_df[self.dv_select.value].var()]
            tmp_df["5th Percentile"] = [t_df[self.dv_select.value].quantile(0.05)]
            tmp_df["25th Percentile"] = [t_df[self.dv_select.value].quantile(0.25)]
            tmp_df["75th Percentile"] = [t_df[self.dv_select.value].quantile(0.75)]
            tmp_df["95th Percentile"] = [t_df[self.dv_select.value].quantile(0.95)]
            tmp_df["Median"] = [t_df[self.dv_select.value].quantile(0.5)]
            tmp_df = tmp_df[
                [
                    "Start_date",
                    "End_date",
                    "# data_points",
                    "# Missing",
                    "# time_series",
                    "Sum",
                    "Mean",
                    "Variance",
                    "5th Percentile",
                    "25th Percentile",
                    "Median",
                    "75th Percentile",
                    "95th Percentile",
                ]
            ]
            tmp_df.set_index("Start_date", inplace=True)
            self.heir_dataframe.height = 50

        cols = [
            "Sum",
            "Mean",
            "Variance",
            "5th Percentile",
            "25th Percentile",
            "Median",
            "75th Percentile",
            "95th Percentile",
        ]
        tmp_df[cols] = tmp_df[cols].round(0)
        self.heading12.css_classes = ["story_title_input"]
        self.heading12.value = "Statistics of " + self.dv_select.value
        self.heir_dataframe.value = tmp_df
        self.data_explore(self.data)

        

    def update_dropdowns(self, event):
        # Dynamic dropdown creation
        hier = self.interaction_select.value
        self.dynamic_drops.clear()
        self.dropdowns.clear()
        for i in range(0, len(hier)):
            self.dropdowns.append(
                pn.widgets.MultiChoice(
                    options=list(self.data[hier[i]].unique()),
                    name=hier[i],
                    margin=10,
                    max_items=1,
                )
            )
        self.dynamic_drops.extend(pn.Row(self.dropdowns))
        
        temp_list = [x for x in np.unique(self.gran_select.value + self.interaction_select.value).tolist() if x not in self.interaction_list]

        if len(temp_list) > 0:
            self.interaction_list.extend(temp_list)

        # Dependent filtering
        def update_gran_filters_dist_plot(event):
            df = self.data[self.interaction_select.value].copy()
            for filtr in self.dropdowns.objects:
                if filtr.value: 
                    df = df[df[filtr.name] == filtr.value[0]]
            for filtr in self.dropdowns.objects:
                if not filtr.value:
                    filtr.options = df[filtr.name].unique().tolist()
                    
        for filt in self.dropdowns.objects:
            filt.param.watch(update_gran_filters_dist_plot,'value')
      
    def get_data_frequency(self,data,var):
        # Frequency of data restricted to daily weekly monthly and yearly
        # For hourly data, need to modify this
        frequencies = ['Daily','Weekly','Monthly','Yearly']
        data = data[[var]]
        data.drop_duplicates(subset = var,inplace = True)
        data.sort_values(by = var,inplace = True)
        days = (data[var].iloc[1] - data[var].iloc[0]).days
        date_map = {
            1: "Daily",
            7: "Weekly",
            30: "Monthly",
            31: "Monthly",
            28: "Monthly",
            29: "Monthly",
            365: "Yearly",
            366: "Yearly",
        }
        try:
            frequency = date_map[days]
        except:
            frequency = 'Daily'
        self.data_frequency.options = frequencies[frequencies.index(frequency):]
        self.data_frequency.value = self.data_frequency.options[0]
        

    def return_interaction_tab(self):

        # All data changes, data for dropdowns are made in this function 
        self.data_cols.options = list(self.data.columns)
        # Identify type of variable
        for var in self.data.columns:
            if self.data[var].dtype in ["float", "float16", "float32","float64"]:
                self.likely_cat[var] = False
            elif len(self.data[var]) > 100:
                self.likely_cat[var] = (
                    1.0 * self.data[var].nunique() / self.data[var].count() < 0.01
                )
            elif self.data[var].nunique() < 10:
                self.likely_cat[var] = True
            else:
                self.likely_cat[var] = False

        self.cat_vars = [var for var in self.data.columns if self.likely_cat[var]]
        
        # All strings qualify for date variables
        # If date in your data is integer, change to string
        self.date_vars = [
            var
            for var in self.data.columns
            if self.data[var].dtype not in ["float", "float16", "float32","float64"]
            and self.data[var].dtype not in ["int", "int8", "int32", "int16","int64"]
        ]
        self.cont_vars = [var for var in self.data.columns if not self.likely_cat[var]]
        self.cont_vars = [
            var 
            for var in self.cont_vars
            if self.data[var].dtype in ["float", "float16", "float32","float64"] 
            or self.data[var].dtype in ["int", "int8", "int32", "int16","int64"]
        ]
        
        # Of all the string columns trying to convert the variables to date
        # Columns that do not get converted are dropped from date vars
        temp_date_vars = self.date_vars.copy()
        for i in temp_date_vars:
            try:
                self.data[i] = pd.to_datetime(self.data[i])
            except Exception:
                self.date_vars.remove(i)
                
        # temp variable stores the original data, self.data is modified in the code on various selections        
        self.temp = self.data.copy()

        self.cat_vars = [var for var in self.cat_vars if var not in self.date_vars]
        self.price_vars = [var for var in self.cont_vars if var.find("price") != -1]
        self.vol_vars = [var for var in self.cont_vars if var not in self.price_vars]

        self.gran_select.options = self.cat_vars
        self.heir_select.options = self.cat_vars
        self.date_select.options = self.date_vars
        self.dv_select.options = self.cont_vars
        self.interaction_select.options = self.cat_vars
        
        # Temporary selection. To be removed for other datasets
        gran_vars = ['retailer','region','SKU_code']
        self.gran_select.value = []
        self.gran_select.value = [x for x in gran_vars if x in self.cat_vars]

        # Primary and Secondary dropdown 
        self.x_var.options = self.cont_vars
        first_element = ["None"]
        y_vars = [n for n in self.cont_vars if n != self.x_var.value]
        self.y_var.options = first_element + y_vars

        self.date = self.data[self.date_select.value].max()

        @pn.depends(self.date_select.param.value, watch=True)
        def change_max_date(val):
            self.date = self.data[self.date_select.value].max()

        # Aggregation dropdown to have only granularity columns
        def hier_dropdown_select(event):
            self.heir_select.options = self.gran_select.value

        self.gran_select.param.watch(hier_dropdown_select, "value")
        
        self.get_data_frequency(self.data,self.date_vars[0])

        # Data frequency dropdown function
        # temp data is copied to data var and rolledup
        # this data is then used for all graphs in exploration and interaction tab
        # Granularity selection is must before roll up
        @pn.depends(self.data_frequency.param.value, watch=True)
        def update_data(frequency):
            if frequency == 'Daily':
                self.data = ''
                self.data = self.temp.copy()
                self.date = self.data[self.date_select.value].max()                
            elif frequency == "Weekly":
                if len(self.gran_select.value) > 0:
                    self.data = ''
                    data = self.temp.copy()
                    data["fiscal_week_monthly"] = data[self.date_select.value].dt.to_period(
                        "W"
                    )
                    granularity = self.gran_select.value.copy()
                    granularity.append("fiscal_week_monthly")
                    cat_vars = [var for var in self.cat_vars if var not in granularity]
                    date_vars = [var for var in self.date_vars if var not in granularity]
                    price_vars = [var for var in self.price_vars if var not in granularity]
                    vol_vars = [var for var in self.vol_vars if var not in granularity]
                    if cat_vars:
                        d1 = data.groupby(granularity, as_index=False)[cat_vars].max()
                        self.weekly  = d1
                    if date_vars:
                        d2 = data.groupby(granularity, as_index=False)[date_vars].max()
                        self.weekly = pd.concat([self.weekly,d2[date_vars]],axis = 1)
                    if price_vars:
                        d3 = data.groupby(granularity, as_index=False)[price_vars].mean()
                        self.weekly = pd.concat([self.weekly,d3[price_vars]],axis = 1)
                    if vol_vars:
                        d4 = data.groupby(granularity, as_index=False)[vol_vars].sum()
                        self.weekly = pd.concat([self.weekly,d4[vol_vars]],axis = 1)
                    self.data = self.weekly.copy()
                    self.weekly = ""
                    self.data[self.date_select.value] = (
                        self.data[self.date_select.value]
                        .dt.to_period("W")
                        .dt.to_timestamp()
                    )
                    self.date = self.data[self.date_select.value].max()
            elif frequency == "Monthly":
                if len(self.gran_select.value) > 0:
                    self.data = ""
                    data = self.temp.copy()
                    data["fiscal_week_monthly"] = data[self.date_select.value].dt.to_period(
                        "M"
                    )
                    granularity = self.gran_select.value.copy()
                    granularity.append("fiscal_week_monthly")
                    cat_vars = [var for var in self.cat_vars if var not in granularity]
                    date_vars = [var for var in self.date_vars if var not in granularity]
                    price_vars = [var for var in self.price_vars if var not in granularity]
                    vol_vars = [var for var in self.vol_vars if var not in granularity]
                    if cat_vars:
                        d1 = data.groupby(granularity, as_index=False)[cat_vars].max()
                        self.monthly = d1
                    if date_vars:
                        d2 = data.groupby(granularity, as_index=False)[date_vars].max()
                        self.monthly = pd.concat([self.monthly,d2[date_vars]],axis = 1)
                    if price_vars:
                        d3 = data.groupby(granularity, as_index=False)[price_vars].mean()
                        self.monthly = pd.concat([self.monthly,d3[price_vars]],axis = 1)
                    if vol_vars:
                        d4 = data.groupby(granularity, as_index=False)[vol_vars].sum()
                        self.monthly = pd.concat([self.monthly,d4[vol_vars]],axis = 1)
                    self.data = self.monthly.copy()
                    self.monthly = ""
                    self.data[self.date_select.value] = (
                        self.data[self.date_select.value]
                        .dt.to_period("M")
                        .dt.to_timestamp()
                    )
                    self.date = self.data[self.date_select.value].max()
            else:
                if len(self.gran_select.value) > 0:
                    self.data = ""
                    data = self.temp.copy()
                    data["fiscal_week_monthly"] = data["fiscal_week"].dt.year
                    granularity = self.gran_select.value.copy()
                    granularity.append("fiscal_week_monthly")
                    cat_vars = [var for var in self.cat_vars if var not in granularity]
                    date_vars = [var for var in self.date_vars if var not in granularity]
                    price_vars = [var for var in self.price_vars if var not in granularity]
                    vol_vars = [var for var in self.vol_vars if var not in granularity]
                    if cat_vars:
                        d1 = data.groupby(granularity, as_index=False)[cat_vars].max()
                        self.yearly = d1
                    if date_vars:
                        d2 = data.groupby(granularity, as_index=False)[date_vars].max()
                        self.yearly = pd.concat([self.yearly,d2[date_vars]],axis = 1)
                    if price_vars:
                        d3 = data.groupby(granularity, as_index=False)[price_vars].mean()
                        self.yearly = pd.concat([self.yearly,d3[price_vars]],axis = 1)
                    if vol_vars:
                        d4 = data.groupby(granularity, as_index=False)[vol_vars].sum()
                        self.yearly = pd.concat([self.yearly,d4[vol_vars]],axis = 1)
                    self.yearly = pd.concat(
                        [d1, d2[date_vars], d3[price_vars], d4[vol_vars]], axis=1
                    )
                    self.data = self.yearly.copy()
                    self.yearly = ""
                    self.data[self.date_select.value] = (
                        self.data[self.date_select.value]
                        .dt.to_period("Y")
                        .dt.to_timestamp()
                    )
                    self.date = self.data[self.date_select.value].max()

        def _update_y_var(event):
            y_value = self.y_var.value
            y_variables = list(set(self.cont_vars) - set([self.x_var.value]))
            first_element = ["None"]
            self.y_var.options = first_element + y_variables
            self.y_var.value = y_value

        def _update_x_var(event):
            x_value = self.x_var.value
            x_variables = list(set(self.cont_vars) - set([self.y_var.value]))
            self.x_var.options = x_variables
            self.x_var.value = x_value

        self.y_var.param.watch(_update_x_var, "value")
        self.x_var.param.watch(_update_y_var, "value")

    def num_unique(self,event):
        # Univariate table generation
        Continuous_table = pd.DataFrame()
        Categorical_table = pd.DataFrame()
        for column in self.cat_vars + self.cont_vars:
            Total = self.data[column].count()
            Total_unq = self.data[column].nunique()
            Variable_type = "Categorical" if self.likely_cat[column] else "Continuous"
            Mode_value = str(self.data[column].mode(dropna=True)[0])
            Na_count = self.data[column].isna().sum()
            if type(self.data[column][0]) != str and Variable_type != "Categorical":
                Min_val = round(self.data[column].min(), 2)
                Max_val = round(self.data[column].max(), 2)
                Mean_val = round(np.mean(self.data[column]), 2)
                Median_val = round(self.data[column].quantile(0.5), 2)
                Perc_25 = round(self.data[column].quantile(0.25), 2)
                Perc_75 = round(self.data[column].quantile(0.75), 2)
                if Mean_val == np.nan:
                    Mean_val = 0
                df = pd.DataFrame(
                    {
                        'Variable' : [column],
                        "# of data points": [Total],
                        "Missing value count": Na_count,
                        "Minimum value": Min_val,
                        "Maximum value": Max_val,
                        "Average": Mean_val,
                        "25th percentile": Perc_25,
                        "Median": Median_val,
                        "75th percentile": Perc_75,
                    }
                )
                Continuous_table = pd.concat([Continuous_table,df],axis = 0)
            else:
                df = pd.DataFrame(
                    {
                        'Variable' : [column],
                        "# of data points": [Total],
                        "Unique values": [Total_unq],
                        "Mode": [Mode_value],
                        "Missing value count": Na_count,
                    }
                )
                Categorical_table = pd.concat([Categorical_table,df],axis = 0)
                
        # Formatting univariate tables
        if(len(Continuous_table) > 0):
            self.cont_heading.height = 25
            self.cont_heading.css_classes = ['univ_title']
            Continuous_table.set_index("Variable", inplace=True)
            self.univar.value = Continuous_table
            self.univar.height = 35* len(Continuous_table)
            self.cont_heading.value = 'Continuous variables'
        if(len(Categorical_table) > 0):
            self.cat_heading.height = 25
            self.cat_heading.css_classes = ['univ_title']
            Categorical_table.set_index("Variable", inplace=True)
            self.univar_2.value = Categorical_table
            self.univar_2.height = 35* len(Categorical_table)
            self.cat_heading.value = 'Categorical variables'
               

    def get_plot(self, event):
        df = self.data
        df["None"] = 1

        # Filtering data based on hierarchy selected
        for i in range(0, len(self.interaction_select.value)):
            df = df[
                df[self.interaction_select.value[i]]
                == self.dropdowns.objects[i].value[0]
            ]
        grouper_key = self.interaction_select.value.copy()
        grouper_key.append(self.date_select.value)
        
        # Aggregating Primary and Secondary variables based on type
        # This could be customised for different datasets
        if (
            self.x_var.value.lower().find("price") != -1
            or self.x_var.value.lower().find("weight") != -1
        ):
            summation_x = "mean"
            y_label = "Average of " + self.x_var.value
        else:
            summation_x = sum
            y_label = "Sum of " + self.x_var.value
        if (
            self.y_var.value.lower().find("price") != -1
            or self.y_var.value.lower().find("weight") != -1
        ):
            summation_y = "mean"
            second_y_label = "Average of " + self.y_var.value
        else:
            summation_y = sum
            second_y_label = "Sum of " + self.y_var.value
        df[self.x_var.value].fillna(0, inplace=True)
        df[self.y_var.value].fillna(0, inplace=True)
        df = (
            df.groupby(grouper_key)
            .agg({self.x_var.value: [summation_x], self.y_var.value: [summation_y]})
            .reset_index()
        )
        df.columns = grouper_key + [self.x_var.value, self.y_var.value]
        df = df.sort_values(by=[self.date_select.value])
        likely_cat = self.likely_cat
        series = pd.Series(df[self.x_var.value].values, name=self.x_var.value)
        # Outlier detection
        detector = anomaly_detector.AnomalyDetector(series.to_dict())
        outliers = detector.get_anomalies()
        anomaly_dict = {}
        for outlier in outliers:
            time_period = outlier.get_time_window()
            if time_period[1] - time_period[0] > 0:
                current_time = time_period[0]
                while current_time <= time_period[1]:
                    try:
                        value = series.loc[current_time]
                        if "Series" in str(type(value)):
                            for val in value:
                                anomaly_dict.update({current_time: val})
                                # scores.append(outlier.anomaly_score)
                        else:
                            anomaly_dict.update({current_time: value})
                    except Exception:
                        pass
                    current_time += 1

            else:
                time_period = outlier.get_time_window()
                value = series.loc[time_period[0]]
                anomaly_dict.update({time_period[0]: value})

        outliers_df = pd.DataFrame()
        outliers_df["Outliers"] = anomaly_dict.values()
        outliers_df["Index"] = anomaly_dict.keys()

        df.index.name = "Index"
        # If no outlier is found
        if len(outliers_df) > 0:
            df = pd.merge(df, outliers_df, on=["Index"], how="outer")
        
        # Change points
        try:
            model = "l2"  # "l1", "rbf", "linear", "normal", "ar"
            algo = rpt.Window(width=int(0.02 * len(series)), model=model).fit(
                series.values
            )
            my_bkps = algo.predict(pen=np.log(len(series)) * 2 * (series.std() ** 2))
            if len(series) in my_bkps:
                my_bkps.remove(len(series))
            if len(my_bkps) > 0:
                indices = [
                    series.reset_index().iloc[ind - 1][self.x_var.value]
                    for ind in my_bkps
                ]
                changepoints = pd.DataFrame()
                changepoints["Index"] = [i - 1 for i in my_bkps]
                changepoints["Changepoints"] = indices
                df = pd.merge(df, changepoints, on=["Index"], how="outer")
        except Exception:
            my_bkps = []

        legend_names = []
        legend_val = []

        # Comments tagging
        def callback(event):
            selected = source.selected.indices
            if len(selected) > 0:
                date_selected = df.iloc[selected][self.date_select.value].values[0]
                self.comment_box.clear()
                # Defining tag type - Dropdown or text
                self.comment_box.append(
                    pn.panel(
                        pn.Column(
                            pn.widgets.Select(
                                options=self.reason_list, name="Select reason code"
                            ),
                            pn.widgets.TextInput(
                                height=40,
                                disabled=True,
                                placeholder="Select Others to specify custom reason",
                            ),
                            pn.widgets.Button(
                                name="Save comment", button_type="primary"
                            ),
                            pn.panel("Date : " + str(date_selected).split(".")[0]),
                        )
                    )
                )

                @pn.depends(self.comment_box.objects[0][0].param.value, watch=True)
                def reason_drop(val):
                    if val == "Others":
                        self.comment_box.objects[0][1].disabled = False
                        self.comment_box.objects[0][
                            1
                        ].placeholder = " Tag outlier/changepoints"
                    else:
                        self.comment_box.objects[0][1].disabled = True
                        self.comment_box.objects[0][
                            1
                        ].placeholder = "Select Others to specify custom reason"

                def update_comment_table(event):
                    update_comment_table_param(selected)

                self.comment_box.objects[0][2].on_click(update_comment_table)

        # Comment table generation
        # Filling all for hierarchy and granularity column if it is dropped after being selected once
        # Filling Na values with No and random values with Yes for outliers/changepoints
        def update_comment_table_param(selected):
            if self.comment_box.objects[0][0].value == "Others":
                comment_written = self.comment_box.objects[0][1].value
            else:
                comment_written = self.comment_box.objects[0][0].value
            select_table = df.iloc[selected]
            cols_add = [
                x
                for x in np.unique(self.gran_select.value + self.interaction_list).tolist()
                if x not in self.interaction_select.value
            ]
            select_table[cols_add] = pd.DataFrame(
                [["All"] * len(cols_add)], index=select_table.index
            )
            if "Outliers" in select_table.columns:
                select_table["Outliers"] = [
                    "No" if np.isnan(val) else "Yes" for val in select_table["Outliers"]
                ]
            else:
                select_table["Outliers"] = "No"
            if "Changepoints" in select_table.columns:
                select_table["Changepoints"] = [
                    "No" if np.isnan(val) else "Yes"
                    for val in select_table["Changepoints"]
                ]
            else:
                select_table["Changepoints"] = "No"
            select_table["Comment"] = comment_written
            select_table.drop(self.x_var.value,axis = 1,inplace = True)
            select_table.drop(self.y_var.value, axis=1, inplace=True)
            self.comments_table = pd.concat(
                [self.comments_table, select_table], axis=0, ignore_index=True
            )
            na_list = self.comments_table.columns[self.comments_table.isna().any()].tolist()
            na_list = [x for x in na_list if x in self.interaction_list]
            if na_list:
                for i in na_list:
                    self.comments_table[i].fillna('All',inplace = True)
            self.comment_box.clear()

        # If both primary and secondary variables are selected
        if self.y_var.value != "None" and not likely_cat[self.y_var.value]:
            source = ColumnDataSource(df)
            tools = "hover,box_zoom,pan,save,reset,wheel_zoom,tap"
            p = figure(
                x_axis_type="datetime",
                plot_height=400,
                plot_width=900,
                tools=tools,
                toolbar_location="above",
            )
            # Axis label formatting
            if df[self.x_var.value].max() > 1000000:
                p.yaxis.axis_label = y_label + "(In millions)"
            elif df[self.x_var.value].max() > 1000:
                p.yaxis.axis_label = y_label + "(In thousands)"
            else:
                p.yaxis.axis_label = y_label
            if df[self.y_var.value].max() > 1000000:
                second_y_label = second_y_label + "(In millions)"
            elif df[self.y_var.value].max() > 1000:
                second_y_label = second_y_label + "(In thousands)"
            else:
                second_y_label = second_y_label

            # Capping if all values are same
            if df[self.x_var.value].min() == df[self.x_var.value].max():
                min_val = 0.75 * df[self.x_var.value].min()
                max_val = 1.25 * df[self.x_var.value].max()
            else:
                min_val = df[self.x_var.value].min()
                max_val = df[self.x_var.value].max()
            if df[self.y_var.value].min() == df[self.y_var.value].max():
                min_val_sec = 0.75 * df[self.y_var.value].min()
                max_val_sec = 1.25 * df[self.y_var.value].max()
            else:
                min_val_sec = df[self.y_var.value].min()
                max_val_sec = df[self.y_var.value].max()

            p.y_range = Range1d(start=min_val, end=max_val)
            p.extra_y_ranges[self.y_var.value] = Range1d(
                start=min_val_sec, end=max_val_sec
            )
            p.add_layout(
                LinearAxis(y_range_name=self.y_var.value, axis_label=second_y_label),
                "right",
            )
            p1 = p.line(
                self.date_select.value,
                self.y_var.value,
                y_range_name=self.y_var.value,
                source=source,
                color="Grey",
                line_width=3,
            )
            p2 = p.line(
                self.date_select.value, self.x_var.value, source=source, line_width=3
            )
            p.circle(
                self.date_select.value, self.x_var.value, source=source, line_width=1
            )
            legend_names.append(self.x_var.value)
            legend_names.append(self.y_var.value)
            legend_val.append([p2])
            legend_val.append([p1])
            if len(outliers_df["Outliers"]) > 0:
                p3 = p.circle(
                    self.date_select.value,
                    "Outliers",
                    source=source,
                    color="Red",
                    size=7,
                )
                legend_names.append("Outliers")
                legend_val.append([p3])

            if len(my_bkps) > 0:
                p4 = p.square(
                    self.date_select.value,
                    "Changepoints",
                    source=source,
                    color="Green",
                    size=7,
                )
                legend_names.append("Changepoints")
                legend_val.append([p4])
            legends = Legend(items=list(zip(legend_names, legend_val)))
            p.add_layout(legends, "right")
            # Formatting and creating data labels
            p.toolbar.logo = None
            p.xaxis.axis_label = self.date_select.value
            p.xaxis.formatter = DatetimeTickFormatter(
                hours=["%b %Y"], days=["%b %Y"], months=["%b %Y"], years=["%b %Y"]
            )
            p.xaxis[0].ticker.desired_num_ticks = 25
            p.xaxis.major_label_orientation = math.pi / 2
            p.yaxis.formatter = NumeralTickFormatter(format="0.0a")
            p.xgrid.grid_line_color = None
            p.ygrid.grid_line_color = None
            p.xaxis.major_tick_line_color = None
            p.xaxis.minor_tick_line_color = None
            p.yaxis.major_tick_line_color = None
            p.yaxis.minor_tick_line_color = None
            p.on_event(Tap, callback)
            p.add_layout(Legend(), "right")
            hover = p.select(dict(type=HoverTool))
            hover.tooltips = [
                (self.x_var.value, "@{" + self.x_var.value + "}" + "{0.0a}"),
                (self.y_var.value, "@{" + self.y_var.value + "}" + "{0.0a}"),
            ]
            hover.mode = "mouse"
        else:
            # If Secondary variable is None
            source = ColumnDataSource(df)
            tools = "hover,box_zoom,pan,save,reset,wheel_zoom,tap"
            p = figure(
                x_axis_type="datetime", plot_height=400, plot_width=900, tools=tools
            )
            if df[self.x_var.value].max() > 1000000:
                p.yaxis.axis_label = y_label + "(In millions)"
            elif df[self.x_var.value].max() > 1000:
                p.yaxis.axis_label = y_label + "(In thousands)"
            else:
                p.yaxis.axis_label = y_label
            if df[self.x_var.value].min() == df[self.x_var.value].max():
                min_val = 0.75 * df[self.x_var.value].min()
                max_val = 1.25 * df[self.x_var.value].max()
            else:
                min_val = df[self.x_var.value].min()
                max_val = df[self.x_var.value].max()
            p.y_range = Range1d(start=min_val, end=max_val)
            p1 = p.line(
                self.date_select.value, self.x_var.value, source=source, line_width=3
            )
            p.circle(
                self.date_select.value, self.x_var.value, source=source, line_width=1
            )
            legend_names.append(self.x_var.value)
            legend_val.append([p1])
            if len(outliers_df["Outliers"]) > 0:
                p2 = p.circle(
                    self.date_select.value,
                    "Outliers",
                    source=source,
                    color="Red",
                    size=7,
                )
                legend_names.append("Outliers")
                legend_val.append([p2])
            if len(my_bkps) > 0:
                p3 = p.square(
                    self.date_select.value,
                    "Changepoints",
                    source=source,
                    color="Green",
                    size=7,
                )
                legend_names.append("Changepoints")
                legend_val.append([p3])
            legends = Legend(items=list(zip(legend_names, legend_val)))
            p.add_layout(legends, "right")
            p.on_event(Tap, callback)
            p.xaxis.formatter = DatetimeTickFormatter(
                hours=["%b %Y"], days=["%b %Y"], months=["%b %Y"], years=["%b %Y"]
            )
            p.xaxis[0].ticker.desired_num_ticks = 25
            p.yaxis.formatter = NumeralTickFormatter(format="0.0a")
            p.xaxis.major_label_orientation = math.pi / 2
            p.toolbar.logo = None
            p.xaxis.axis_label = self.date_select.value
            p.xgrid.grid_line_color = None
            p.ygrid.grid_line_color = None
            p.xaxis.major_tick_line_color = None
            p.xaxis.minor_tick_line_color = None
            p.yaxis.major_tick_line_color = None
            p.yaxis.minor_tick_line_color = None
            hover = p.select(dict(type=HoverTool))
            hover.tooltips = [
                (self.x_var.value, "@{" + self.x_var.value + "}" + "{0.0a}")
            ]
            hover.mode = "mouse"
        self.plot.object = p

    # Alignment/arrangement of widgets/charts/tables
    def return_dash(self):
        dashboard = pn.Tabs(
            (
                "Univariate Analysis",
                pn.Column(
                    self.heading11,
                    #self.data_loader,
                    pn.Row(self.file_selection_drop,self.file_choose_button,
                           pn.Column(self.progress_load,self.progress_load_text)),
                    pn.Spacer(height=10),
                    self.heading4,
                    pn.WidgetBox(
                        pn.Row(self.univariate_button, pn.Spacer(width=20)),
                        self.cont_heading,
                        self.univar,
                        self.cat_heading,
                        self.univar_2,
                        css_classes=["gray_bg_univ"],
                    ),
                    css_classes=["gray_bg"],
                ),
            ),
            (
                "Time Series Exploration",
                pn.Column(
                    pn.WidgetBox(
                        pn.Row(
                            self.dv_select,
                            self.gran_select,
                            pn.Spacer(width=10),
                            self.date_select,
                            self.data_frequency,
                        ),
                        pn.Spacer(height = 20),
                        pn.Row(self.heir_select),
                        pn.Spacer(height=40),
                        self.button,
                        self.heading6,
                        self.heading12,
                        self.heir_dataframe,
                        pn.Spacer(height=20),
                        self.heading3,
                        self.dash,
                        css_classes=["gray_bg"],
                    ),
                ),
            ),
            (
                "Data Interaction",
                pn.Column(
                    pn.Row(
                        self.x_var,
                        self.y_var,
                        self.interaction_select,
                        pn.Spacer(width=20, height=40),
                        self.dynamic_drops,
                    ),
                    pn.Spacer(height=80),
                    self.hier_button,
                    self.button_upd,
                    pn.Row(self.plot, self.comment_box),
                    self.show_table,
                    self.outlier_table,
                    css_classes=["gray_bg"],
                ),
            ),
            (
                "Model Activation",
                pn.Column(
                    self.prediction_length,
                    self.experiment_name,
                    pn.Row(self.gluonts_data,
                    pn.Column(self.progress,
                    self.progress_text))
                ),
            ),
        )
        return dashboard

    # Computing series for exploration tab
    def sparse_series(self, x):
        sparse = sum(x == 0 | x.isna()) / len(x)
        return sparse

    def low_value_series(self, m):
        if self.pareto_select.value == "All":
            m = (
                m.groupby(self.gran_select.value)[self.dv_select.value]
                .sum()
                .sort_values(ascending=False)
                .to_frame(name="Total")
                .reset_index()
            )
        else:
            m = (
                m.groupby(self.pareto_select.value)[self.dv_select.value]
                .sum()
                .sort_values(ascending=False)
                .to_frame(name="Total")
                .reset_index()
            )
        m["Cumulative_total"] = m["Total"].cumsum()
        m["Cumulative_percentage_contribution"] = m["Cumulative_total"] / (
            m["Total"].sum()
        )
        m["Low_value_series"] = [
            1 if x > 0.8 else 0 for x in m["Cumulative_percentage_contribution"]
        ]
        return m

    def active_series(self, data):
        m = (
            data.groupby(self.gran_select.value)[self.date_select.value]
            .max()
            .to_frame(name="Recent")
        )
        m = (
            m.groupby("Recent")
            .size()
            .to_frame(name="Total")
            .sort_values(by=["Recent"], ascending=False)
            .reset_index()
        )
        return m

    def new_series(self, data):
        if self.data_frequency.value == "Daily":
            window = 1
        elif self.data_frequency == "Weekly":
            window = 7
        elif self.data_frequency == "Monthly":
            window = 30
        else:
            window = 365
        m = (
            data.groupby(self.gran_select.value)[self.date_select.value]
            .min()
            .to_frame(name="Recent")
        )
        dys = (
            data[self.date_select.value].max() - data[self.date_select.value].min()
        ) / window
        if self.data_frequency.value == "Daily":
            datelist = pd.date_range(
                start=data[self.date_select.value].min(),
                periods=round(dys.days + 1, 0),
                freq="D",
            )
        else:
            datelist = pd.date_range(
                start=data[self.date_select.value].min(),
                periods=round(dys.days + 1, 0),
                freq="W-MON",
            )
        dt = pd.DataFrame({"Recent": datelist})
        dt.sort_values(by=["Recent"], inplace=True)
        m = (
            m.groupby("Recent")
            .size()
            .to_frame(name="Total")
            .sort_values(by=["Recent"], ascending=False)
            .reset_index()
        )
        m = pd.merge(m, dt, on=["Recent"], how="outer")
        m["Total"].fillna(0, inplace=True)
        m.sort_values(by=["Recent"], ascending=False, inplace=True)
        return m

    # Generating flags table
    def generate_table(self, Sparse, m, active, new, val_sparse, val_lv):
        dfs = [Sparse, active, new, m]
        if self.pareto_select.value == "All":
            df_final = reduce(
                lambda left, right: pd.merge(left, right, on=self.gran_select.value),
                dfs,
            )
        else:
            dfs = [Sparse, active, new]
            df_final = reduce(
                lambda left, right: pd.merge(left, right, on=self.gran_select.value),
                dfs,
            )
            df_final = pd.merge(df_final, m, on=[self.pareto_select.value])
        df_final["Sparse_flag"] = [
            1 if i >= val_sparse else 0 for i in Sparse["Sparse_series"]
        ]
        df_final["Low_value_flag"] = [
            1 if i >= val_lv else 0
            for i in df_final["Cumulative_percentage_contribution"]
        ]
        return df_final

    # Searchable dropdown for flags table
    # Uses the same logic as for hierarchy dropdown in interaction sheet for dependent filtering
    def get_searchable_dropdowns(self, data):
        self.flags_dropdown.clear()
        for i in range(0, len(self.gran_select.value)):
            self.flags_dropdown.append(
                pn.widgets.MultiChoice(
                    options=list(data[self.gran_select.value[i]].unique()),
                    name=self.gran_select.value[i],
                    margin=10,
                    width=220,
                    height=100,
                )
            )
        self.flags_panel.extend(pn.Row(self.flags_dropdown))

            
            
        def update_gran_filters_dist_plot(event):
            df = self.flags_table.copy()
            for filtr in self.flags_dropdown.objects:
                if filtr.value: 
                    df = df[df[filtr.name].isin(filtr.value)]
            for filtr in self.flags_dropdown.objects:
                if not filtr.value:
                    filtr.options = df[filtr.name].unique().tolist()
            data_table.source.data = df
            data_table.update()
            data_table.source.selected.indices = []
            self.line_plot.object = None
        
        for filt in self.flags_dropdown.objects:
            filt.param.watch(update_gran_filters_dist_plot,'value')


        
    # Computing the number of series that qualify based on thresholds
    def update_table(self, event):
        # Active flags assignment across series
        def active_flag_generator(x, cutoff):
            if self.data_frequency.value == "Daily":
                window = 1
            elif self.data_frequency.value == "Weekly":
                window = 7
            elif self.data_frequency.value == "Monthly":
                window = 30
            else:
                window = 365
            return int((((self.date - x.max()).days) / window) <= cutoff)

        self.active_flag = (
            self.data.groupby(self.gran_select.value)[self.date_select.value]
            .apply(lambda x: active_flag_generator(x, self.range_slider_active.value))
            .to_frame(name="Active_series")
        )
        # New flag assignment across series
        def new_flag_generator(x, cutoff):
            if self.data_frequency.value == "Daily":
                window = 1
            elif self.data_frequency.value == "Weekly":
                window = 7
            elif self.data_frequency.value == "Monthly":
                window = 30
            else:
                window = 365
            return int((((self.date - x.min()).days) / window) <= cutoff)

        self.new_flag = (
            self.data.groupby(self.gran_select.value)[self.date_select.value]
            .apply(lambda x: new_flag_generator(x, self.range_slider_new.value))
            .to_frame(name="New_series")
        )
        self.flags_table = self.generate_table(
            self.Sparse,
            self.m,
            self.active_flag,
            self.new_flag,
            self.range_slider.value,
            self.range_slider_lv.value,
        )
        # Computing qualified series
        Total_series = self.flags_table[
            (self.flags_table["Active_series"] == 1)
            & (self.flags_table["New_series"] == 0)
            & (self.flags_table["Low_value_flag"] == 0)
            & (self.flags_table["Sparse_flag"] == 0)
        ].shape[0]

        a = "# of series satisfying set thresholds :"

        self.heading15.value = a + str(Total_series)
        self.heading15.css_classes = ["story_title_input"]
        self.heading16.value = "Flags: Active = 1, Sparse = 0, LowValue = 0, New = 0"
        self.heading16.css_classes = ["flags_title"]

        self.flags_panel.clear()
        source = ColumnDataSource(self.flags_table)
        columns = []
        for i in self.gran_select.value:
            columns.append(TableColumn(field=i, title=i))
        columns.extend(
            [
                TableColumn(field="Active_series", title="Active_flag"),
                TableColumn(field="New_series", title="New_flag"),
                TableColumn(field="Low_value_flag", title="Low_value_flag"),
                TableColumn(field="Sparse_flag", title="Sparse_flag"),
            ]
        )
        global data_table
        data_table = DataTable(source=source, columns=columns, width=800, height=280)
        self.flag_plot.clear()
        self.flag_plot.append(data_table)
        self.get_searchable_dropdowns(self.flags_table)
        
        # Plot generating on row selection from table
        def function_source(attr, old, new):
            try:
                selected_index = source.selected.indices[0]
                df = self.data
                for i in range(0, len(self.gran_select.value)):
                    df = df[
                        df[self.gran_select.value[i]]
                        == source.data[self.gran_select.value[i]][selected_index]
                    ]
                df.sort_values(by=[self.date_select.value], inplace=True)
                self.line_plot.object = self.get_line_plot(df)
            except IndexError:
                pass

        data_table.source.selected.on_change("indices", function_source)

    # Charts for data exploration tab
    def data_explore(self, data):
        # Sparse block
        self.dash.clear()

        self.range_slider = pn.widgets.FloatSlider(
            name="Sparse series cutoff", start=0, end=1, step=0.1, value=0.5
        )

        data["dummy"] = data[self.dv_select.value].astype(bool)
        data["dummy"].fillna(0, inplace=True)
        self.Sparse = (
            data.groupby(self.gran_select.value)["dummy"]
            .mean()
            .to_frame(name="Sparse_series")
            .reset_index()
        )
        self.Sparse["Sparse_series"] = 1 - self.Sparse["Sparse_series"]
        self.sparse_plot = self.get_sparse_plot(self.Sparse)

        def return_sparse(cutoff):
            return "{} Series have {}% or greater zero volume data".format(
                self.Sparse[self.Sparse["Sparse_series"] >= cutoff].shape[0],
                cutoff * 100,
            )

        a = pn.interact(return_sparse, cutoff=self.range_slider)
        
        # Low value block
        self.range_slider_lv = pn.widgets.FloatSlider(
            name="Low value series cutoff", start=0, end=1, step=0.05, value=0.8
        )
        self.pareto_select.options = self.gran_select.value + ["All"]
        self.pareto_select.value = "All"

        @pn.depends(self.pareto_select.param.value, watch=True)
        def pareto_update(val):
            self.m = self.low_value_series(self.data)
            self.low_value_plot.object = self.get_low_value_plot(self.m)
            temp = self.range_slider.value
            self.range_slider_lv.value = self.range_slider_lv.value + 0.1
            self.range_slider_lv.value = temp

        self.m = self.low_value_series(data)
        self.low_value_plot.object = self.get_low_value_plot(self.m)

        def return_low_value(cutoff):
            return "{} Series contribute to {}% volume".format(
                self.m[
                    self.m["Cumulative_percentage_contribution"].round(2) <= cutoff
                ].shape[0],
                cutoff * 100,
            )

        b = pn.interact(return_low_value, cutoff=self.range_slider_lv)

        # Active block #
        if self.data_frequency.value == 'Daily':
            range_window = 30 
            start_window = 1
            value = 1
            new_value = 7
        elif self.data_frequency.value == "Weekly":
            range_window = 52
            start_window = 4
            value = 4
            new_value = 16
        elif self.data_frequency.value == "Monthly":
            range_window = 12
            start_window = 1
            value = 1
            new_value = 4
        else:
            range_window = 5
            start_window = 1
            value = 1
            new_value = 1
        self.range_slider_active = pn.widgets.IntSlider(
            name="Active series cutoff",
            start=start_window,
            end=range_window,
            step=1,
            value=value,
        )
        self.active = self.active_series(data)
       

        self.active_plot = self.get_active_plot(self.active)

        def return_active(cutoff):
            if self.data_frequency.value == "Daily":
                slider_val = "days"
            elif self.data_frequency.value == "Weekly":
                slider_val = "weeks"
            elif self.data_frequency.value == "Monthly":
                slider_val = "months"
            else:
                slider_val = "years"
            return "{} Series are active in recent {} {}".format(
                self.active["Total"].head(cutoff).sum(), cutoff, slider_val
            )

        c = pn.interact(return_active, cutoff=self.range_slider_active)

        # New block 
        self.range_slider_new = pn.widgets.IntSlider(
            name="New series cutoff",
            start=start_window,
            end=range_window,
            step=1,
            value=new_value,
        )
        self.new = self.new_series(data)

        self.new_plot = self.get_new_plot(self.new)

        def return_new(cutoff):
            if self.data_frequency.value == "Daily":
                slider_val = "days"
            elif self.data_frequency.value == "Weekly":
                slider_val = "weeks"
            elif self.data_frequency.value == "Monthly":
                slider_val = "months"
            else:
                slider_val = "years"
            return "{} Series are new in recent {} {}".format(
                self.new["Total"].head(cutoff).sum(), cutoff, slider_val
            )

        d = pn.interact(return_new, cutoff=self.range_slider_new)

        # Arrangement of sliders and charts
        self.dash.extend(
            pn.WidgetBox(
                pn.Row(self.sparse_plot, pn.Column(a)),
                pn.Row(self.low_value_plot, pn.Column(b, self.pareto_select)),
                pn.Row(self.active_plot, pn.Column(c)),
                pn.Row(self.new_plot, pn.Column(d)),
                pn.Row(self.heading7),
                pn.Row(self.table_button, self.heading15),
                pn.Row(pn.Spacer(width=320), self.heading16),
                pn.Row(self.flag_plot, self.flags_panel),
                pn.Row(self.line_plot),
            )
        )

    # Line plot for exploration tab
    def get_line_plot(self, df):
        df.fillna(0, inplace=True)
        source = ColumnDataSource(df)
        tools = "hover,box_zoom,pan,save,reset,wheel_zoom"
        p7 = figure(
            x_axis_type="datetime", plot_width=800, plot_height=350, tools=tools
        )
        p7.xaxis.formatter = DatetimeTickFormatter(
            hours=["%b %Y"], days=["%b %Y"], months=["%b %Y"], years=["%b %Y"]
        )
        p7.xaxis[0].ticker.desired_num_ticks = 25
        p7.line(
            self.date_select.value, self.dv_select.value, source=source, line_width=3
        )
        p7.xaxis.axis_label = "Dates"
        p7.yaxis.axis_label = self.dv_select.value

        p7.toolbar.logo = None
        p7.xaxis.major_tick_line_color = None  # turn off x-axis major ticks
        p7.xaxis.minor_tick_line_color = None  # turn off x-axis minor ticks
        p7.yaxis.major_tick_line_color = None
        p7.xgrid.grid_line_color = None
        p7.xaxis.major_label_orientation = math.pi / 2
        p7.yaxis.minor_tick_line_color = None
        hover = p7.select(dict(type=HoverTool))
        hover.tooltips = [("Volume", "@{" + self.dv_select.value + "}" + "{0.0a}")]
        hover.mode = "mouse"

        return p7

    # New series bar chart
    def get_new_plot(self, m):

        df2 = m.head(26)
        if self.data_frequency.value == "Daily":
            df2['Recent'] = df2['Recent'].apply(lambda x: x.strftime("%Y-%m-%d"))
            label_x = 'Days'
        elif self.data_frequency.value == "Weekly":
            df2["Recent"] = df2["Recent"].apply(lambda x: x.strftime("%Y-%m-%d"))
            label_x = 'Weeks'
        elif self.data_frequency.value == "Monthly":
            df2["Recent"] = df2["Recent"].apply(lambda x: x.strftime("%Y-%m"))
            df2 = df2.groupby("Recent")["Total"].sum().reset_index()
            label_x = 'Months'
        else:
            df2["Recent"] = df2["Recent"].apply(lambda x: x.strftime("%Y"))
            df2 = df2.groupby("Recent")["Total"].sum().reset_index()
            label_x = 'Years'
        df2.sort_values(by=["Recent"], inplace=True, ascending=False)
        df2["Total"] = df2["Total"].round(0)
        self.new = df2
        source = ColumnDataSource(df2)
        tools = "hover,box_zoom,pan,save,reset,wheel_zoom"
        p4 = figure(
            x_range=list(df2["Recent"]),
            tools=tools,
            plot_height=350,
            plot_width=800,
            title="Recency of series over time",
            x_axis_label=label_x,
            y_axis_label=f"# of new series starting across {label_x}",
        )
        p4.vbar("Recent", top="Total", source=source, width=0.9)
        # Formatting
        p4.xgrid.grid_line_color = None
        p4.ygrid.grid_line_color = None
        p4.y_range.start = 0
        p4.xaxis.major_label_orientation = math.pi / 2
        p4.toolbar.logo = None
        p4.xaxis.major_tick_line_color = None  # turn off x-axis major ticks
        p4.xaxis.minor_tick_line_color = None  # turn off x-axis minor ticks
        p4.yaxis.major_tick_line_color = None

        p4.yaxis.minor_tick_line_color = None
        hover = p4.select(dict(type=HoverTool))
        hover.tooltips = [("Number of series", "@Total")]
        hover.mode = "mouse"

        return p4
    
    # Active series bar chart
    def get_active_plot(self, m):

        df2 = m.head(26)
        if self.data_frequency.value == "Daily":
            df2['Recent'] = df2['Recent'].apply(lambda x: x.strftime("%Y-%m-%d"))
            window_per = " Days"
        elif self.data_frequency.value == "Weekly":
            df2["Recent"] = df2["Recent"].apply(lambda x: x.strftime("%Y-%m-%d"))
            window_per = " Weeks"
        elif self.data_frequency.value == "Monthly":
            df2["Recent"] = df2["Recent"].apply(lambda x: x.strftime("%Y-%m"))
            df2 = df2.groupby("Recent")["Total"].sum().reset_index()
            window_per = " Months"
        else:
            df2["Recent"] = df2["Recent"].apply(lambda x: x.strftime("%Y"))
            df2 = df2.groupby("Recent")["Total"].sum().reset_index()
            window_per = " Years"
        df2.sort_values(by=["Recent"], inplace=True, ascending=False)
        title_name = min(26, len(df2))
        self.active = df2
        source = ColumnDataSource(df2)
        tools = "hover,box_zoom,pan,save,reset,wheel_zoom"
        p3 = figure(
            x_range=list(df2["Recent"]),
            tools=tools,
            plot_height=350,
            plot_width=800,
            title="Activity of Series over last " + str(title_name) + str(window_per),
            x_axis_label=window_per,
            y_axis_label=f"# of series last active across{window_per}",
        )
        p3.vbar(x="Recent", top="Total", source=source, width=0.9)
        # Formatting
        p3.xgrid.grid_line_color = None
        p3.ygrid.grid_line_color = None
        p3.y_range.start = 0
        p3.xaxis.major_label_orientation = math.pi / 2
        p3.toolbar.logo = None
        p3.xaxis.major_tick_line_color = None  # turn off x-axis major ticks
        p3.xaxis.minor_tick_line_color = None  # turn off x-axis minor ticks
        p3.yaxis.major_tick_line_color = None

        p3.yaxis.minor_tick_line_color = None
        hover = p3.select(dict(type=HoverTool))
        hover.tooltips = [("Number of series", "@Total")]
        hover.mode = "mouse"

        return p3

    # Low value bar chart
    def get_low_value_plot(self, m):
        # Creating bins for % of series - X - axis
        bins = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        labels = [
            "0-10",
            "10-20",
            "20-30",
            "30-40",
            "40-50",
            "50-60",
            "60-70",
            "70-80",
            "80-90",
            "90-100",
        ]
        # Computing % of series
        m["Num_series"] = range(1, len(m) + 1)
        m["Cumulative_series"] = m["Num_series"] / len(m)
        m["Low_value_buckets"] = pd.cut(
            m["Cumulative_series"] * 100, bins=bins, labels=labels
        ).fillna(labels[1])
        Total_sum = m["Total"].sum()
        df1 = (
            m.groupby("Low_value_buckets")["Total"]
            .apply(lambda x: (100 * (x.sum() / Total_sum)).round(1))
            .to_frame("Low_value_series")
            .reset_index()
        )
        df1["Low_value_sum"] = df1["Low_value_series"].cumsum()
        
        source = ColumnDataSource(df1)
        tools = "hover,box_zoom,pan,save,reset,wheel_zoom"
        p2 = figure(
            x_range=list(df1["Low_value_buckets"]),
            tools=tools,
            plot_height=250,
            plot_width=800,
            title="Pareto chart of " + self.dv_select.value,
            x_axis_label="%  of Series",
            y_axis_label="Volume contribution in %",
        )
        p2.vbar(x="Low_value_buckets", top="Low_value_series", source=source, width=0.9)
        p2.line(
            "Low_value_buckets",
            "Low_value_sum",
            source=source,
            color="Grey",
            line_width=3,
        )
        # Formatting
        p2.xgrid.grid_line_color = None
        p2.ygrid.grid_line_color = None
        p2.y_range.start = 0
        p2.toolbar.logo = None
        p2.xaxis.major_tick_line_color = None  # turn off x-axis major ticks
        p2.xaxis.minor_tick_line_color = None  # turn off x-axis minor ticks
        p2.yaxis.major_tick_line_color = None

        p2.yaxis.minor_tick_line_color = None
        hover = p2.select(dict(type=HoverTool))
        hover.tooltips = [("% of volume contribution", "@Low_value_series")]
        hover.mode = "mouse"

        return p2

    # Sparse series bar chart
    def get_sparse_plot(self, Sparse):
        bins = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        labels = [
            "0-10",
            "10-20",
            "20-30",
            "30-40",
            "40-50",
            "50-60",
            "60-70",
            "70-80",
            "80-90",
            "90-100",
        ]
        Sparse["Sparse_data_buckets"] = pd.cut(
            Sparse["Sparse_series"] * 100, bins=bins, labels=labels
        ).fillna(labels[1])
        df = Sparse.groupby("Sparse_data_buckets").count().reset_index()
        x = list(df["Sparse_data_buckets"])
        # y = df['Sparse_series']
        source = ColumnDataSource(df)
        tools = "hover,box_zoom,pan,save,reset,wheel_zoom"
        p = figure(
            x_range=x,
            plot_height=250,
            tools=tools,
            plot_width=800,
            title="% of missing/zero values across series",
            x_axis_label="% Zeroes",
            y_axis_label="Number of series",
        )
        p.vbar("Sparse_data_buckets", top="Sparse_series", source=source, width=0.9)
        # Formatting
        p.xgrid.grid_line_color = None
        p.ygrid.grid_line_color = None
        p.y_range.start = 0
        p.toolbar.logo = None
        p.xaxis.major_tick_line_color = None
        p.xaxis.minor_tick_line_color = None
        p.yaxis.major_tick_line_color = None
        p.yaxis.minor_tick_line_color = None
        hover = p.select(dict(type=HoverTool))
        hover.tooltips = [("Number of series", "@Sparse_series")]
        hover.mode = "mouse"

        return p

    # Unused. Need to work on this to generate density across time for multiple series
    def dense_plot(self):
        df = self.data
        for i in range(0, len(self.interaction_select.value)):
            df = df[
                df[self.interaction_select.value[i]]
                == self.dropdowns.objects[i].value[0]
            ]
        df[self.dv_select.value] = [
            0 if val < 0 else val for val in df[self.dv_select.value]
        ]
        df1 = (
            df.groupby(self.gran_select.value)
            .agg({self.dv_select.value: [sum]})
            .reset_index()
        )
        df1.columns = self.gran_select.value + ["Dv_sum"]
        df = pd.merge(df, df1, on=self.gran_select.value)
        df["Normalised_" + self.dv_select.value] = (
            df[self.dv_select.value] / df["Dv_sum"]
        )
        df = df.sort_values(by=[self.date_select.value])
        df["Normalised_" + self.dv_select.value] = df[
            "Normalised_" + self.dv_select.value
        ].fillna(0)
        df["date_bins"] = pd.cut(df[self.date_select.value], bins=5)
        df["dv_bins"] = pd.cut(df["Normalised_" + self.dv_select.value], bins=20)
        p1 = sns.heatmap(pd.crosstab(df["dv_bins"], df["date_bins"]), cbar=False)
        p1.set_xlabel("Date", fontsize=100)
        p = p1.get_figure()
        p.set_size_inches(14, 18)
        self.plot_dense.state_pop()
        self.plot_dense.object = p

    # Getting data frequency for gluonts data generation
    def get_data_freq(self):
        tmp_df = self.data.copy()

        for col in self.gran_select.value:
            tmp_df = tmp_df[tmp_df[col] == tmp_df[col].iloc[0]]

        tmp_df.sort_values(self.date_select.value, inplace=True)
        days_diff = (
            tmp_df[self.date_select.value].iloc[1]
            - tmp_df[self.date_select.value].iloc[0]
        ).days
        date_map = {
            1: "D",
            7: "W",
            30: "M",
            31: "M",
            28: "M",
            29: "M",
            365: "Y",
            366: "Y",
        }
        self.data_freq = date_map[days_diff]

        if self.data_freq == "W":
            self.data_freq = (
                self.data_freq
                + "-"
                + tmp_df[self.date_select.value].iloc[0].day_name()[:3].upper()
            )

        tmp_df = ""

    # Preparing gluonts data
    # Shaping the data into required format and saving all the files
    # the variables are cleaned to reduce memory usage
    def prepare_gluonts_data(self, event):

        self.progress_text.value = "Aggregating data"
        comment_cols = []
        # Aggregating data based on the selections
        rollup = {self.dv_select.value: sum}
        rollup.update({i: sum for i in self.cont_vars if i not in self.dv_select.value})
        rollup.update(
            {i: max for i in self.cat_vars if i not in self.gran_select.value}
        )
        gran_val = self.gran_select.value.copy()
        gran_val.append(self.date_select.value)
        self.data = self.data.groupby(gran_val).agg(rollup).reset_index()
        
        gran_val.extend([i for i in self.interaction_list if i not in gran_val])
        

        self.disabled = False
        self.progress.value = 15

        self.progress_text.value = "Adding outliers and changepoints to data"
        # Comments for outliers and changepoints
        # Comments are created as columns in the data and signals are provided based on each tag
        # These go as features/regressors to the model
        for i in range(0, len(self.comments_table)):
            rows = []
            comment_selected = self.comments_table[self.comments_table.index == i]
            comment = comment_selected["Comment"].iloc[0]
            for j in gran_val:
                if comment_selected[j].iloc[0] != "All":
                    rows.extend([j])
            comment_selected = comment_selected[rows + ["Comment"]]
            self.data = pd.merge(self.data, comment_selected, on=rows, how="left")
            self.data["Comment"] = (
                self.data["Comment"].fillna(0).astype(bool).astype(int)
            )
            if comment in self.data.columns:
                self.data[comment] = self.data[[comment, "Comment"]].max(axis=1)
                self.data.drop("Comment", inplace=True, axis=1)
            else:
                self.data.rename(columns={"Comment": comment}, inplace=True)

        if len(self.comments_table) > 0:
            comment_cols = self.comments_table["Comment"].unique().tolist()

        self.progress.value = 30

        self.progress_text.value = "Creating unique id for a time series"
        self.flags_table["unique_id"] = (
            self.flags_table[self.gran_select.value].astype(str).apply("_".join, axis=1)
        )

        self.progress.value = 45
        data = self.data.copy()
        self.get_data_freq()
        self.data = ""
        self.temp = ""
        self.progress_text.value = "Merging flags table"
        # Creating an ID column
        data["Unique_ID"] = (
            data[self.gran_select.value].astype(str).apply("_".join, axis=1)
        )
        data["Unique_ID"] = data["Unique_ID"].astype("category").cat.codes.values

        data.sort_values(["Unique_ID", self.date_select.value], inplace=True)

        self.progress.value = 50

        # Preparing Metadata
        dynamic_real = []
        static_real = []
        static_cat = []

        prediction_length = self.prediction_length.value

        time_period = (
            data[self.date_select.value]
            .sort_values()
            .unique()[-self.prediction_length.value :]
        )
        time_period = pd.to_datetime(time_period)
        input_dict = {}
        input_dict["Date variable"] = self.date_select.value
        input_dict["Target variable"] = self.dv_select.value
        input_dict["Data granularity"] = self.gran_select.value
        input_dict["Forecast window"] = self.prediction_length.value
        input_dict["Data frequency"] = self.data_freq
        input_dict["Forecast start date"] = min(time_period).strftime("%Y-%m-%d")
        input_dict["Forecast end date"] = max(time_period).strftime("%Y-%m-%d")

        self.progress_text.value = "Defining variables into real and categorical"

        real = (
            [i for i in self.cont_vars if i not in [self.dv_select.value]]
            + comment_cols
        )

        cat = [
            i
            for i in self.cat_vars
            if i
            not in [
                self.date_select.value
            ]
        ]
        feat_static_cat = []
        # feat_dynamic_cat = []
        feat_static_real = []
        feat_dynamic_real = []

        # Feat Static and Dynamic Cat
        for col in cat:
            if not sum(data.groupby("Unique_ID")[col].nunique() > 1):
                feat_static_cat.append(col)
            else:
                feat_dynamic_real.append(col)

        # Feat Static and Dynamic Real
        for col in real:
            if not sum(data.groupby("Unique_ID")[col].nunique() > 1):
                feat_static_real.append(col)
            else:
                feat_dynamic_real.append(col)

        for col in feat_static_real:
            static_real.append(BasicFeatureInfo(name=col))

        for col in feat_dynamic_real:
            dynamic_real.append(BasicFeatureInfo(name=col))

        for col in feat_static_cat:
            static_cat.append(
                CategoricalFeatureInfo(name=col, cardinality=data[col].nunique())
            )

        idv_cols = [i for i in feat_dynamic_real]
        list_cols = [self.date_select.value, self.dv_select.value] + idv_cols
        df_idv = (
            data.groupby(["Unique_ID"] + self.gran_select.value)
            .agg({k: list if i else min for i, k in enumerate(list_cols)})
            .reset_index()
        )
        df_idv.columns = (
            ["item_id"] + self.gran_select.value + ["Start_Date", "Actual"] + idv_cols
        )
        self.progress.value = 60

        self.progress_text.value = "Creating metadata"
        metadata = MetaData(
            freq=self.data_freq,
            prediction_length=prediction_length,
            feat_dynamic_real=dynamic_real,
            feat_static_cat=static_cat,
            feat_static_real=static_real,
        )

        self.progress.value = 65
        # Identifying columns with missing values
        t = data.isna().sum()
        missing_val_columns = t[t > 0].index.tolist()

        self.progress_text.value = "Creating gluonts data"
        # Filling missing values
        for mc in missing_val_columns:
            data[mc] = data[mc].fillna(method="ffill")

        # Laeblencoding categorical columns
        for col in feat_static_cat:
            data[col] = data[col].astype("category").cat.codes.values

        feat = {self.date_select.value: min, self.dv_select.value: list}
        feat.update({i: list for i in feat_dynamic_real})

        df = data.groupby("Unique_ID").agg(feat)
        self.flags_table["Keep_Series_Flag"] = (
            (self.flags_table["Active_series"])
            * (1 - self.flags_table["Sparse_flag"])
            * (1 - self.flags_table["Low_value_flag"])
            * (1 - self.flags_table["New_series"])
        )
        self.flags_table["Unique_ID"] = (
            self.flags_table["unique_id"].astype("category").cat.codes.values
        )
        df = pd.merge(
            df,
            self.flags_table[["Unique_ID", "Keep_Series_Flag"]],
            left_index=True,
            on="Unique_ID",
            how="left",
        ).set_index("Unique_ID")
        del self.flags_table["Unique_ID"]
        df.sort_values(by=["Keep_Series_Flag"], inplace=True, ascending=False)

        if feat_dynamic_real:
            df["dynamic_real"] = df[feat_dynamic_real].values.tolist()

        if feat_static_cat:
            df["static_cat"] = (
                data.groupby("Unique_ID")
                .agg({i: "first" for i in feat_static_cat})
                .values.tolist()
            )

        if feat_static_real:
            df["static_real"] = (
                data.groupby("Unique_ID")
                .agg({i: "first" for i in feat_static_real})
                .values.tolist()
            )


        # Number of data points
        datapoints = len(df)    
            
        all_variables = np.array(
            [1, 1, 1]
            + [
                1 if feat_dynamic_real else 0,
                1 if feat_static_cat else 0,
                1 if feat_static_real else 0,
            ]
        )
        all_variable_names = np.array(
            [
                FieldName.ITEM_ID,
                FieldName.START,
                FieldName.TARGET,
                FieldName.FEAT_DYNAMIC_REAL,
                FieldName.FEAT_STATIC_CAT,
                FieldName.FEAT_STATIC_REAL,
            ]
        )

        all_variable = all_variable_names[all_variables == 1]

        # Comb 1
        if len(all_variable) == 3:
            test_ds = [
                json.dumps(
                    {
                        all_variable[0]: str(ID),
                        all_variable[1]: str(start_date),
                        all_variable[2]: target,
                    }
                )
                for ID, (start_date, target, *_) in df.iterrows()
            ]

        # Comb 2
        if len(all_variable) == 4:
            test_ds = [
                json.dumps(
                    {
                        all_variable[0]: str(ID),
                        all_variable[1]: str(start_date),
                        all_variable[2]: target,
                        all_variable[3]: f1,
                    }
                )
                for ID, (start_date, target, *_, f1) in df.iterrows()
            ]

        # Comb 3
        if len(all_variable) == 5:
            test_ds = [
                json.dumps(
                    {
                        all_variable[0]: str(ID),
                        all_variable[1]: str(start_date),
                        all_variable[2]: target,
                        all_variable[3]: f1,
                        all_variable[4]: f2,
                    }
                )
                for ID, (start_date, target, *_, f1, f2) in df.iterrows()
            ]

        # Comb 4
        if len(all_variable) == 6:
            test_ds = [
                json.dumps(
                    {
                        all_variable[0]: str(ID),
                        all_variable[1]: str(start_date),
                        all_variable[2]: target,
                        all_variable[3]: f1,
                        all_variable[4]: f2,
                        all_variable[5]: f3,
                    }
                )
                for ID, (start_date, target, *_, f1, f2, f3) in df.iterrows()
            ]

        input_dict["Feat Dynamic Real"] = feat_dynamic_real
        input_dict["experiment name"] = self.experiment_name.value
        self.progress.value = 90
        self.progress_text.value = "Saving the dataset"
        client = boto3.client("s3")
        bucket = "tiger-mle-tg"
        key = f"inputs/auto-gluonts-data/{self.experiment_name.value}"
        path = creds_file["credentials"]['tld_s3']['prefix'] + '/' + key


        exp_name_dict = {}
        exp_name_dict['experiment_name'] = self.experiment_name.value
        json_str = json.dumps(exp_name_dict, default=str)
        client.put_object(
            Bucket=bucket,
            Body=json_str,
            Key=f"inputs/auto-gluonts-data/experiments.json",
        )

        data = ""
        # Save the dataset in Gluonts format
        test_ds_json = "\n".join(test_ds)
        json_bytes = test_ds_json.encode("utf-8")
        data_gzip_object = gzip.compress(json_bytes)
        client.put_object(
            Bucket=bucket, Body=data_gzip_object, Key=f"{key}/data/data.json.gz"
        )

        # Save the metadata
        json_str = json.dumps(metadata.dict(), default=str)
        json_bytes = json_str.encode("utf-8")
        metadata_gzip_object = gzip.compress(json_bytes)
        client.put_object(
            Bucket=bucket,
            Body=metadata_gzip_object,
            Key=f"{key}/metadata/metadata.json.gz",
        )

        # Load fulltrain files to update parameters
        input_dict["Data path"] = f"{key}"
        creds_file_deepstate = load_yaml(
            os.path.join(package_dir, "..", "..", "configs/fulltrain_deepstate.yml"))
        input_dict['Dataset Name'] = creds_file_deepstate['dataset_name']
        creds_file_deepar = load_yaml(
            os.path.join(package_dir, "..", "..", "configs/fulltrain_deepar.yml"))
        creds_file_prophet = load_yaml(
            os.path.join(package_dir, "..", "..", "configs/fulltrain_prophet.yml"))
        
        
        # Changing YML files
        creds_file_deepstate['name'] = self.experiment_name.value
        creds_file_deepstate['forecast_start_date'] = datetime.strptime(
            input_dict['Forecast start date'],'%Y-%m-%d').date()
        creds_file_deepstate['forecast_end_date'] = datetime.strptime(
            input_dict['Forecast end date'],'%Y-%m-%d').date()
        if self.data_frequency.value == 'Weekly':
            number_of_days = self.prediction_length.value * 7
        elif self.data_frequency.value == 'Monthly':
            number_of_days = self.prediction_length.value * 30
        elif self.data_frequency.value == 'Yearly':
            number_of_days = self.prediction_length.value * 365
        else:
            number_of_days = self.prediction_length.value
        creds_file_deepstate['training_frequency']['full'] = number_of_days
        creds_file_deepstate['run_params']['evaluation']['data_set_length'] = datapoints
        creds_file_deepar['run_params']['datapath'] = path
        
        # Deepstate.yml
        yaml_file = yaml.dump(creds_file_deepstate,default_flow_style = False)
        client.put_object(
            Bucket=bucket, Body=yaml_file, Key=f"{key}/configs/fulltrain_deepstate.yml"
        )
        
        # Changing deepar YML files
        creds_file_deepar['name'] = self.experiment_name.value
        creds_file_deepar['forecast_start_date'] = datetime.strptime(
            input_dict['Forecast start date'],'%Y-%m-%d').date()
        creds_file_deepar['forecast_end_date'] = datetime.strptime(
            input_dict['Forecast end date'],'%Y-%m-%d').date()
        if self.data_frequency.value == 'Weekly':
            number_of_days = self.prediction_length.value * 7
        elif self.data_frequency.value == 'Monthly':
            number_of_days = self.prediction_length.value * 30
        elif self.data_frequency.value == 'Yearly':
            number_of_days = self.prediction_length.value * 365
        else:
            number_of_days = self.prediction_length.value
        creds_file_deepar['training_frequency']['full'] = number_of_days
        creds_file_deepar['run_params']['evaluation']['data_set_length'] = datapoints
        creds_file_deepar['run_params']['datapath'] = path
        
        # Deepar.yml
        yaml_file = yaml.dump(creds_file_deepar,default_flow_style = False)
        client.put_object(
            Bucket=bucket, Body=yaml_file, Key=f"{key}/configs/fulltrain_deepar.yml"
        )
        
         # Changing prophet YML files
        creds_file_prophet['name'] = self.experiment_name.value
        creds_file_prophet['forecast_start_date'] = datetime.strptime(
            input_dict['Forecast start date'],'%Y-%m-%d').date()
        creds_file_prophet['forecast_end_date'] = datetime.strptime(
            input_dict['Forecast end date'],'%Y-%m-%d').date()
        if self.data_frequency.value == 'Weekly':
            number_of_days = self.prediction_length.value * 7
        elif self.data_frequency.value == 'Monthly':
            number_of_days = self.prediction_length.value * 30
        elif self.data_frequency.value == 'Yearly':
            number_of_days = self.prediction_length.value * 365
        else:
            number_of_days = self.prediction_length.value
        creds_file_prophet['training_frequency']['full'] = number_of_days
        creds_file_prophet['run_params']['evaluation']['data_set_length'] = datapoints
        creds_file_deepar['run_params']['datapath'] = path
        
        # FbProphet.yml
        yaml_file = yaml.dump(creds_file_prophet,default_flow_style = False)
        client.put_object(
            Bucket=bucket, Body=yaml_file, Key=f"{key}/configs/fulltrain_prophet.yml"
        )
        
        
        json_str = json.dumps(input_dict, default=str)
        client.put_object(
            Bucket=bucket, Body=json_str, Key=f"{key}/input_variables.json",
        )

        self.progress.value = 95
        self.progress_text.value = "Saving IDvs"
        # idv_cols = all feat_dynamic_real with type as float
        with s3fs.S3FileSystem().open(
            creds_file["credentials"]["dashboard"]["idv_output"]
            + self.experiment_name.value
            + "/idv_data.pkl",
            "wb",
        ) as fp:
            df_idv.to_pickle(fp)
            
        with s3fs.S3FileSystem().open(
            creds_file["credentials"]["dashboard"]["idv_output"]
            + self.experiment_name.value
            + "/comments_table.csv",'w'
        ) as fp:
            self.comments_table.to_csv(fp)

        self.progress.value = 100
        self.progress_text.value = "Process completed"
        self.progress.disabled = True

    @property
    def selected_file(self):
        return self.load_data_file.value

    def set_callback(self, callback):
        self.callback = callback
        self.load_button.on_click(self.pass_data_to)

    def start_selection(self, event=None):
        self.data_loader[0] = self.selection_widget
        

    def end_selection(self, event=None):
        self.data_loader[0] = self.minimised_view
        
    def toggle_add_button(self, target, event):
        if event.new:
            target.css_classes = ["secondary", "button", "is_visible"]
        else:
            target.css_classes = ["secondary", "button", "is_hidden"]

    def add_to_files(self, event=None):
        self.end_selection()
        files = self.select_files.value
        self.selected_files = files.copy()
        new_files = [val for val in files if val not in self.select_files]
        for file in new_files:
            if os.path.isdir(file):
                dir_files = os.listdir(file)
                applicable_files = [
                    os.path.join(file, x)
                    for x in dir_files
                    if x.split(".")[-1] in ["csv", "tsv", "xls", "xlsx"]
                ]
            else:
                applicable_files = [file]
            self.file_map.update({file: applicable_files})
        self.data_files = []
        for file in self.selected_files:
            self.data_files += self.file_map[file]
        self.load_data_file.options = self.data_files

    @property
    def has_changes(self):
        return self.selected_file != self.current_file

    def read_file(self, file):
        if ".csv" in file:
            data = pd.read_csv(file)
        elif ".tsv" in file:
            data = pd.read_csv(file, delimiter="\t")
        elif ".xls" in file:
            data = pd.read_excel(file, sheet_name=None)
        else:
            raise Exception(
                "Does not support the chosen file format - {}".format(
                    file.split(".")[-1]
                )
            )
        return data

    def pass_data_to(self, event=None):
        if self.has_changes:
            file = self.selected_file
            self.data = pd.DataFrame()
            data_1 = self.read_file(file)
            self.current_file = file
            self.initialise_data(data_1)
       
    def load_data_drop(self,event):
        self.progress_load.value = 20
        self.progress_load_text.value = 'Clearing variables'
        self.data = pd.DataFrame()
        self.progress_load.value = 30
        self.progress_load_text.value = 'Loading data'
        with s3fs.S3FileSystem().open(
            creds_file["credentials"]["dashboard"]["eda_input"].rsplit('/',1)[0]
            + '/'
            + self.file_selection_drop.value, "rb"
        ) as f:
            Masked_data = pd.read_csv(f)
        self.progress_load.value = 60
        self.progress_load_text.value = 'Initialising variables'
        self.initialise_data(Masked_data)
        self.progress_load.value = 100
        self.progress_load_text.value = 'Data loaded'

def generate_dashboard():

    with s3fs.S3FileSystem().open(
            creds_file["credentials"]["dashboard"]["eda_input"], "rb",
        ) as f:
        Masked_data = pd.read_csv(f)

    
    # Temporary conversion to reduce memory usage
    # Change if data changes
    dict_cols = {
        "labels": [
            "organic_label",
            "new_product_label",
            "special_pack_label",
            "converted_item_label",
        ],
        "weights": [
            "weight",
            "price_per_weight",
            "price_per_weight_per_packamt",
            "price_per_packamt",
        ],
        "holidays": ["has_holiday", "has_holiday_saturday", "has_holiday_sunday"],
    }

    Masked_data[dict_cols["labels"]] = Masked_data[dict_cols["labels"]].astype("int8")
    Masked_data[dict_cols["weights"]] = Masked_data[dict_cols["weights"]].astype(
        "float64"
    )
    Masked_data[dict_cols["holidays"]] = Masked_data[dict_cols["holidays"]].astype(
        "int8"
    )

    ds = data_interaction(Masked_data)
    dashboard = ds.return_dash()
    return dashboard.servable()



generate_dashboard()
