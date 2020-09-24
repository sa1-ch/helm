import json
import os.path as op

import click
import yaml

from ts_forecast.scripts.hyper_cli import run_hyper_cli
from ts_forecast.scripts.mlflow_cli import merge_train_score_cli, parent_run_task_cli
from ts_forecast.scripts.score_cli import (
    merge_scoring_jobs_cli,
    run_scoring_cli,
    run_scoring_job,
)
from ts_forecast.scripts.train_cli import run_training_cli, run_training_job


def load_yaml(file):
    with open(file, "r") as fp:
        config = yaml.load(fp, Loader=yaml.SafeLoader)

    return config


def read_input_config(config_str):
    return json.loads(config_str)


def load_file_json(data_type, obj, print_message=None):
    print(f"Parsing {print_message}: config={obj}: data_type={data_type}\n")

    if data_type == "file":
        obj = op.abspath(obj)
        config = load_yaml(obj)
    elif data_type == "json":
        config = read_input_config(obj)

    return config


@click.group()
@click.option("-c", "--cfg", required=True)
@click.option(
    "-cd",
    "--data-type",
    default="json",
    type=click.Choice(["file", "json"], case_sensitive=False),
)
@click.pass_context
def cli(ctx, cfg, data_type):
    from ts_forecast.core.dependencies.containers import Core

    ctx.ensure_object(dict)
    config = load_file_json(data_type=data_type, obj=cfg, print_message="Creds-Config")
    ctx.obj["cfg_file"] = cfg
    ctx.obj["config"] = config

    Core.config.override(config)
    Core.logger()


@cli.command()
@click.option("-i", "--input-file", required=True)
@click.option(
    "-id",
    "--data-type",
    default="json",
    type=click.Choice(["file", "json"], case_sensitive=False),
)
@click.option("-dg", "--dag-id", required=True)
@click.pass_context
def train(ctx, input_file, data_type, dag_id):
    input_config = load_file_json(
        data_type=data_type, obj=input_file, print_message="Train-Spec-Config"
    )
    run_training_cli(creds=ctx.obj["config"], cfg=input_config, dag_id=dag_id)
    print("Train script completed successfuly !")


@cli.command()
@click.option("-i", "--input-file", required=True)
@click.option(
    "-id",
    "--data-type",
    default="json",
    type=click.Choice(["file", "json"], case_sensitive=False),
)
@click.option("-dg", "--dag-id", required=True)
@click.pass_context
def score(ctx, input_file, data_type, dag_id):
    input_config = load_file_json(
        data_type=data_type, obj=input_file, print_message="Score-Spec-Config"
    )
    run_scoring_cli(creds=ctx.obj["config"], cfg=input_config, dag_id=dag_id)
    print("Scoring script completed successfuly !")


@cli.command()
@click.option("-i", "--input-file", required=True)
@click.option(
    "-id",
    "--data-type",
    default="json",
    type=click.Choice(["file", "json"], case_sensitive=False),
)
@click.option("-dg", "--dag-id", required=True)
@click.pass_context
def train_job(ctx, input_file, data_type, dag_id):
    job = load_file_json(
        data_type=data_type, obj=input_file, print_message="Train-Task-Spec-Config",
    )
    run_training_job(job=job, creds=ctx.obj["config"], dag_id=dag_id)
    print("Training task script completed successfuly !")


@cli.command()
@click.option("-i", "--input-file", required=True)
@click.option(
    "-id",
    "--data-type",
    default="json",
    type=click.Choice(["file", "json"], case_sensitive=False),
)
@click.option("-dg", "--dag-id", required=True)
@click.pass_context
def score_job(ctx, input_file, data_type, dag_id):
    job = load_file_json(
        data_type=data_type, obj=input_file, print_message="Score-Task-Spec-Config",
    )
    run_scoring_job(job=job, creds=ctx.obj["config"], dag_id=dag_id)
    print("Scoring task script completed successfuly !")


@cli.command()
@click.option("-i", "--input-file", required=True)
@click.option(
    "-id",
    "--data-type",
    default="json",
    type=click.Choice(["file", "json"], case_sensitive=False),
)
@click.option("-dg", "--dag-id", required=True)
@click.pass_context
def parent_run(ctx, input_file, data_type, dag_id):
    job = load_file_json(
        data_type=data_type, obj=input_file, print_message="Parent-Task-Spec-Config",
    )
    parent_run_task_cli(job=job, creds=ctx.obj["config"], dag_id=dag_id)
    print("Parent task script completed successfuly !")


@cli.command()
@click.option("-i", "--input-file", required=True)
@click.option(
    "-id",
    "--data-type",
    default="json",
    type=click.Choice(["file", "json"], case_sensitive=False),
)
@click.option("-dg", "--dag-id", required=True)
@click.pass_context
def merge_score_run(ctx, input_file, data_type, dag_id):
    job = load_file_json(
        data_type=data_type, obj=input_file, print_message="Merge-Task-Spec-Config",
    )
    merge_scoring_jobs_cli(cfg=job, dag_id=dag_id)
    print("Merging score task script completed successfuly !")


@cli.command()
@click.option("-i", "--input-file", required=True)
@click.option(
    "-id",
    "--data-type",
    default="json",
    type=click.Choice(["file", "json"], case_sensitive=False),
)
@click.option("-dg", "--dag-id", required=True)
@click.pass_context
def merge_run(ctx, input_file, data_type, dag_id):
    job = load_file_json(
        data_type=data_type, obj=input_file, print_message="Merge-Task-Spec-Config",
    )
    merge_train_score_cli(job=job, dag_id=dag_id)
    print("Merging task script completed successfuly !")


@cli.command()
@click.option("-i", "--input-file", required=True)
@click.option(
    "-id",
    "--data-type",
    default="json",
    type=click.Choice(["file", "json"], case_sensitive=False),
)
@click.option("-dg", "--dag-id", required=True)
@click.pass_context
def hyper_run(ctx, input_file, data_type, dag_id):
    input_config = load_file_json(
        data_type=data_type, obj=input_file, print_message="Train-Spec-Config"
    )
    run_hyper_cli(creds=ctx.obj["config"], cfg=input_config, dag_id=dag_id)
    print("Hyper-parameter job triggered successfuly !")


def main(ctxt=None):
    ctxt = ctxt or {}
    cli(obj=ctxt)


if __name__ == "__main__":
    main({})
