
### Pre-requisites to run the dashboards
Open Anaconda Prompt, Create a new conda environment and install the required packages using the command
```bash
conda env create -f env/cpu/py3-master-windows.yml -n ts-dev
```
Activate the environment 
```bash
conda activate ts-dev (or) activate ts-dev
```

### Run the dashboard in local
```bash
panel serve --show --num-procs 1 --port 8083 --address localhost --allow-websocket-origin=54.91.175.3:8083 eda_dashboard.py
```

### Run the dashboard on EKS, Open a browser and go to below link
```bash
http://a873a4dfe9b2249c493389badc950b1-1549006211.us-east-1.elb.amazonaws.com/ts/eda/eda_dashboard 
```

#### EDA Dashboard
It has 4 tabs Univariate, Data Exploration, Data Interaction and Model Activation tab.
A time series dataset in long format is required to run the eda.
Dataset to be placed in S3 and associate location and name of the dataset to be updated in configs/dev.yml file.

#### Univariate tab
Data loader to load the data. Get univariate statistics button gives the summary of the data.

#### Data Exploration tab
Data, DV and Granularity columns are mandatory. These selections will be used for analysis.
The exploration charts on sparsity, active, low value, new series are static and the sliders on the side are linked with the text displayed below.
On clicking the accept button, a flagged table is generated. Filters are enabled on the side to filter for any specific time series. These flags will be used to create the dataset to be used for modelling.
Clicking on any row on the table displays the time series chart below.

#### Interaction tab
Update plot updates the plot with X and Y axis.
In the hierarchy dropdown, multiple variables can be selected to view the plot at any granularity.
Get granular dropdown button is to be clicked to generate dropdowns for variables selected in granularity dropdown.
To remove a variable from granularity selection, remove the variable and click the get granular button.
Plot will be updated only after update plot is clicked.
On clicking any data point from the plot, a textbox and a dropdown will appear to write a comment for the data point.
Saving comment will save it in the database and will be used for modelling purposes.

#### Model Activation tab
Prediction length slider value will be used as the forecast window.
Experiment name is mandatory. Input and the necessary information from the EDA will be saved into an S3 folder under this experiment name.
On Clicking create data button, gluonts data is created and stored in S3 bucket.
Accept button in the exploration tab is to be clicked for saving the thresholds on sparsity etc. before generating model ready data.

### Model evaluation Dashboard in local

```bash
panel serve --show --num-procs 1 --port 8084 --address localhost --allow-websocket-origin=54.91.175.3:8084 eval_dashboard.py
```

### Run the dashboard on EKS, Open a browser and go to below link
```bash
http://a873a4dfe9b2249c493389badc950b1-1549006211.us-east-1.elb.amazonaws.com/ts/eval/eval_dashboard 
```

Contains a module to load data by inputting the experiment name. Dashboard works for only pickle file format. 

The dashboard has 2 tabs, the first tab shows the metrics and charts at time series level, whereas the 2nd tab displays the same metrics and charts as in 1st tab but with data aggregated at a given level.

##### Time Series Level Tab:
This tab has 4 views, 
1st view shows a table with median metrics across time series for each model.
2nd view shows metrics distribution plot for all the metrics categorized into buckets.
3rd view shows a crosstable between two selected metric buckets for a given model.
4th view shows the forecast plot and the feature importance plot for a selection of time series.

##### Aggregated Level Tab:
This tab has the same 4 views as the time series level tab, but the data in this tab is aggregated to a selected hierarchy. To aggregate data at the highest level with all the time series aggregated into 1 time-series, select nothing in the `Select Hierarchy Aggregation` widget and click on the `Get` button. 
