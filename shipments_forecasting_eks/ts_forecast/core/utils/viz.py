import copy
import datetime
import logging
import os

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from ts_forecast.core.dependencies.containers import Gateways
from ts_forecast.core.utils.mlflow import get_run_details, init_mlflow

_LOGGER = logging.getLogger(__name__)


def get_csv_from_s3(path):
    with Gateways.tld_s3().open(path, "rb") as f:
        return pd.read_csv(f).drop(columns=["Unnamed: 0"], errors="ignore")


def get_metrics_for_given_exp(job_cfg, model_filter=False):
    client, exp_id = init_mlflow(job_cfg["exp_name"])

    if model_filter:
        model_filter = (
            lambda x: pd.to_datetime(x.data.params["model_date"])
            == pd.to_datetime(job_cfg["model_date"])
            and x.data.tags["mlflow.runName"] == job_cfg["run_name"]
            and x.data.tags["dag_id"] == job_cfg["dag_id"]
            and x.data.tags.get("mlflow.parentRunId") is not None
        )
        reg_model_name = job_cfg["run_name"]
    else:
        model_filter = None
        reg_model_name = None
        model_filter = (
            lambda x: x.data.tags["dag_id"] == job_cfg["dag_id"]
            and x.data.tags.get("mlflow.parentRunId") is not None
        )

    # Get run details
    run_details = get_run_details(
        client,
        exp_name=job_cfg["exp_name"],
        reg_model_name=reg_model_name,
        model_filter=model_filter,
        finished_runs=False,
    )
    df_list = pd.DataFrame(
        columns=[
            "exp_name",
            "run_name",
            "dag_id",
            "last_train_date",
            "model_date",
            "prediction_length",
            "avg_mad",
            "avg_mean_dev",
            "avg_wmape",
            "model_uri",
            "score_artifact_uri",
            "metrics_uri",
            "error_ts_uri",
        ]
    )
    for iter_run_details in run_details:
        try:
            temp_df = pd.DataFrame(
                columns=[
                    "exp_name",
                    "run_name",
                    "dag_id",
                    "last_train_date",
                    "model_date",
                    "prediction_length",
                    "avg_mad",
                    "avg_mean_dev",
                    "avg_wmape",
                    "model_uri",
                    "score_artifact_uri",
                    "metrics_uri",
                    "error_ts_uri",
                ],
                data=[
                    [
                        job_cfg["exp_name"],
                        iter_run_details.data.tags["mlflow.runName"],
                        job_cfg["dag_id"],
                        iter_run_details.data.params["last_train_date"],
                        iter_run_details.data.params["model_date"],
                        iter_run_details.data.params["prediction_length"],
                        iter_run_details.data.metrics["avg_mad"],
                        iter_run_details.data.metrics["avg_mean_dev"],
                        iter_run_details.data.metrics["avg_wmape"],
                        iter_run_details.data.tags["model_uri"],
                        iter_run_details.data.tags["score_out_path"],
                        os.path.join(
                            iter_run_details.data.tags["score_artifact_uri"],
                            "metrics",
                            "item_level_metrics.csv",
                        ),
                        os.path.join(
                            iter_run_details.data.tags["score_artifact_uri"],
                            "error",
                            "score_ts_error_list.csv",
                        ),
                    ]
                ],
            )

            df_list = df_list.append(temp_df)
        except Exception as e:
            print(e)

    df_list["forecast_end_date"] = pd.to_datetime(
        df_list["model_date"]
    ) + datetime.timedelta(days=int(df_list["prediction_length"].unique()[0]))
    df_list["model_date"] = pd.to_datetime(df_list["model_date"])
    df_list.sort_values(by=["model_date"], inplace=True)
    df_list = df_list.drop_duplicates(keep="first").reset_index(drop=True)

    return df_list


def get_run_details_with_exp_name(exp_dag_list):
    run_details_df = None
    for exp_name, dag_id_list in exp_dag_list.items():
        for dag_id in dag_id_list:
            temp = get_metrics_for_given_exp({"exp_name": exp_name, "dag_id": dag_id})
            if run_details_df is None:
                run_details_df = copy.deepcopy(temp)
            else:
                run_details_df = run_details_df.append(temp)

    return run_details_df.sort_values(
        by=["last_train_date", "model_date", "dag_id", "exp_name"]
    )


def get_metric_analysis_df(run_params_dict):
    df_1 = get_metrics_for_given_exp(run_params_dict, model_filter=True)
    df_melt_1 = df_1.melt(
        id_vars=[
            "exp_name",
            "run_name",
            "dag_id",
            "last_train_date",
            "model_date",
            "prediction_length",
            "forecast_end_date",
            "model_uri",
            "score_artifact_uri",
            "error_ts_uri",
        ],
        value_vars=["avg_mad", "avg_mean_dev", "avg_wmape"],
        var_name="metrics_name",
        value_name="metrics_value",
        col_level=None,
    )

    return df_1, df_melt_1


def prepare_run_metrics_dict(run_details_df):
    run_params_dict = dict()
    for index, row in run_details_df.reset_index(drop=True).iterrows():
        run_params_dict[index] = dict(
            exp_name=row["exp_name"],
            dag_id=row["dag_id"],
            run_name=row["run_name"],
            model_date=row["model_date"],
        )

    return run_params_dict


def get_merged_df_from_list(list_df):
    merged_df = None
    for i in list_df:
        if merged_df is None:
            merged_df = copy.deepcopy(i)
        else:
            merged_df = merged_df.append(i)

    merged_df["exp_name_dag_id"] = merged_df["exp_name"] + ",\n" + merged_df["dag_id"]
    return merged_df


def get_final_run_level_merged_df(run_details_df):
    run_params_dict = prepare_run_metrics_dict(run_details_df)

    df_list = []
    melt_list = []
    for i in run_params_dict.values():
        temp_df, temp_melt_df = get_metric_analysis_df(i)

        df_list.append(temp_df)
        melt_list.append(temp_melt_df)

    final_df_list = get_merged_df_from_list(df_list).drop_duplicates(keep="first")
    final_melted_df = get_merged_df_from_list(melt_list).drop_duplicates(keep="first")

    return final_df_list, final_melted_df


def get_final_item_level_merged_df(exp_dag_list, final_df_list):
    item_level_metrics_df = None
    for exp_name, dag_id in exp_dag_list.items():
        path = final_df_list[
            (final_df_list["exp_name"] == exp_name)
            & (final_df_list["dag_id"] == dag_id)
        ].iloc[0]["metrics_uri"]
        _LOGGER.info(f"Reading: {path}")
        with Gateways.tld_s3().open(path, "rb") as f:
            metrics_df = pd.read_csv(f).drop(columns=["Unnamed: 0"])
            metrics_df["exp_name"] = final_df_list[
                final_df_list["exp_name"] == exp_name
            ].iloc[0]["exp_name"]
            metrics_df["dag_id"] = final_df_list[
                final_df_list["dag_id"] == dag_id
            ].iloc[0]["dag_id"]

            if item_level_metrics_df is None:
                item_level_metrics_df = copy.deepcopy(metrics_df)
            else:
                item_level_metrics_df = item_level_metrics_df.append(metrics_df)

    item_level_metrics_df = item_level_metrics_df[
        ["exp_name", "dag_id", "item_id", "avg_mad", "avg_mean_dev", "avg_wmape"]
    ]
    item_level_metrics_df = item_level_metrics_df.sort_values(
        by=["item_id", "dag_id", "exp_name"]
    ).reset_index(drop=True)

    return item_level_metrics_df


def get_final_date_item_merged_df(exp_dag_list, ts_ids, final_df_list):
    date_item_level_metrics_df = None
    for exp_name, dag_id in exp_dag_list.items():
        for j in ts_ids:
            with Gateways.tld_s3().open(
                os.path.join(
                    final_df_list[
                        (final_df_list["exp_name"] == exp_name)
                        & (final_df_list["dag_id"] == dag_id)
                    ]["score_artifact_uri"][0],
                    "{}".format(j) + ".csv",
                ),
                "rb",
            ) as f:
                metrics_df = pd.read_csv(f)
                metrics_df["exp_name"] = final_df_list[
                    final_df_list["exp_name"] == exp_name
                ]["exp_name"].unique()[0]
                metrics_df["dag_id"] = final_df_list[final_df_list["dag_id"] == dag_id][
                    "dag_id"
                ].unique()[0]

                if date_item_level_metrics_df is None:
                    date_item_level_metrics_df = copy.deepcopy(metrics_df)
                else:
                    date_item_level_metrics_df = date_item_level_metrics_df.append(
                        metrics_df
                    )

    return date_item_level_metrics_df


def get_final_date_item_merged_melted_df(date_item_level_metrics_df):
    date_item_level_metrics_melt_df = date_item_level_metrics_df.melt(
        id_vars=["exp_name", "dag_id", "item_id", "busidaydt"],
        value_vars=["actual_values", "yhat"],
        var_name="values_type",
        value_name="values",
        col_level=None,
    )
    return date_item_level_metrics_melt_df


def print_final_df_with_grad(final_df_list):
    cm = sns.light_palette("Red", as_cmap=True, reverse=False)
    return final_df_list.reset_index(drop=True).style.background_gradient(cmap=cm)


def get_error_ts_df(exp_dag, final_df_list):
    return get_csv_from_s3(
        final_df_list[
            (final_df_list["exp_name"] == list(exp_dag.keys())[0])
            & (final_df_list["dag_id"] == list(exp_dag.values())[0])
        ]["error_ts_uri"][0]
    )


def compare_across_runs(final_melted_df, figsize=(20, 10)):
    f, axes = plt.subplots(3, figsize=figsize)

    sns.barplot(
        x="exp_name_dag_id",
        y="metrics_value",
        data=final_melted_df[final_melted_df["metrics_name"] == "avg_mad"],
        ax=axes[0],
    ).set_title("avg_mad")

    sns.barplot(
        x="exp_name_dag_id",
        y="metrics_value",
        data=final_melted_df[final_melted_df["metrics_name"] == "avg_mean_dev"],
        ax=axes[1],
    ).set_title("avg_mean_dev")

    sns.barplot(
        x="exp_name_dag_id",
        y="metrics_value",
        data=final_melted_df[final_melted_df["metrics_name"] == "avg_wmape"],
        ax=axes[2],
    ).set_title("avg_wmape")

    # axes[1,1].set_axis_off()
    f.tight_layout(pad=3.0)


def compare_across_ts_pie(
    error_metric_name, item_level_metrics_df, bins, figsize=(20, 10), fontsize=12,
):
    temp_avg_error = item_level_metrics_df[error_metric_name].value_counts(
        bins=bins, normalize=True
    )

    f, axes = plt.subplots(1, 1, figsize=figsize)
    temp_avg_error.plot(
        kind="pie",
        autopct="%1.1f%%",
        labels=temp_avg_error.index,
        legend=False,
        fontsize=fontsize,
        ax=axes,
    )

    cm = sns.light_palette("Green", as_cmap=True, reverse=False)
    return pd.DataFrame(temp_avg_error).style.background_gradient(cmap=cm)


def compare_across_ts_bar(
    error_metric_name, item_level_metrics_df, error_metric_threshold, figsize=(20, 10),
):
    f, axes = plt.subplots(1, 1, figsize=figsize)
    sns.barplot(
        x="item_id",
        y=error_metric_name,
        hue="exp_name",
        ax=axes,
        data=item_level_metrics_df.loc[
            item_level_metrics_df[error_metric_name] >= error_metric_threshold,
            ["item_id", error_metric_name, "exp_name"],
        ],
    )


def compare_actual_forecast_time_period(
    date_item_level_metrics_melt_df, item_id, figsize=(20, 10), x_rotation=30
):
    date_item_level_metrics_melt_df["exp_name_dag_id"] = (
        date_item_level_metrics_melt_df["exp_name"]
        + ",\n"
        + date_item_level_metrics_melt_df["dag_id"]
    )
    f, axes = plt.subplots(1, 1, figsize=(20, 10))
    temp_dt = copy.deepcopy(
        date_item_level_metrics_melt_df[
            date_item_level_metrics_melt_df.item_id == item_id
        ]
    )
    p = sns.lineplot(
        x="busidaydt",
        y="values",
        hue="values_type",
        estimator=None,
        lw=1,
        data=temp_dt,
    )
    p.set_xticklabels(size=12, rotation=x_rotation, labels=temp_dt["busidaydt"])


def filter_print_ts_for_items(date_item_level_metrics_df, item_id, date_value):
    return date_item_level_metrics_df[
        (date_item_level_metrics_df.item_id == item_id)
        & (date_item_level_metrics_df.busidaydt >= date_value)
    ]


def get_all_run_details(exp_name, dag_id):
    client, exp_id = init_mlflow(exp_name)

    model_filter = (
        lambda x: x.data.tags["dag_id"] == dag_id
        and x.data.tags.get("mlflow.parentRunId") is not None
    )

    client, exp_id = init_mlflow(exp_name)
    run_details = get_run_details(
        client=client,
        exp_name=exp_name,
        model_filter=model_filter,
        reg_model_name=None,
        finished_runs=False,
    )

    return run_details


def convert_millisec_strdate(mill_sec):
    return datetime.datetime.fromtimestamp(mill_sec / 1000.0).strftime(
        "%Y-%m-%d %H:%M:%S"
    )
