from fabric import Connection, task

_DEC_START_STRING = "******** Executing: {} ******** \n\n"


def bastion(ctx):
    return Connection(
        host=ctx["bastion_host_ip"],
        user=ctx["bastion_host_user"],
        connect_kwargs={"key_filename": ctx["bastion_ssh_keypath"],},
    )


def intercept(func):
    def wrapper(*args, **kwargs):
        print(_DEC_START_STRING.format(kwargs["ctx"]["msg"]))
        return func(*args, **kwargs)

    return wrapper


def iterdict(ctx, dict_obj, filter_key_word):
    for k, v in dict_obj.items():
        if isinstance(v, dict):
            yield from iterdict(ctx, v, filter_key_word)
        else:
            if ("create configmap" in v):
                v = v.format(
                    rds_db_endpoint=ctx["rds_db_endpoint"],
                    docker_image_id=ctx["docker_image_id"],
                    alb_endpoint=ctx["alb_endpoint"],
                    efs_id=ctx["efs_id"],
                    mlflow_artifacts=ctx["mlflow_artifacts"],
                    airflow_dags=ctx["airflow_dags"],
                    airflow_logs=ctx["airflow_logs"],
                )
            if filter_key_word == "create":
                if (
                    ("delete" not in v)
                    and ("uninstall" not in v)
                    and ("path" not in k)
                    and ("update_kube_config" not in k)
                ):
                    yield v
            elif filter_key_word == "delete":
                if (
                    (("delete" in v) or ("uninstall" in v))
                    and ("update_kube_config" not in k)
                    and ("cluster_role" not in k)
                ):
                    yield v


def list_cmd_from_dict(ctx, parent_dict, create_destroy):
    with ctx.cd(parent_dict["path"]):
        result = iterdict(ctx=ctx, dict_obj=parent_dict, filter_key_word=create_destroy)
        result = list(result) if create_destroy == "create" else list(result)[::-1]
        update_kube_config = parent_dict["update_kube_config"]
        ctx.run(update_kube_config, replace_env=False)
        for i in result:
            print(_DEC_START_STRING.format(i))
            ctx.run(i, replace_env=False)
            print("\n\n-----------------------------------------------------")


@intercept
def install_pip(ctx):
    install_pip = ctx["install_pip"]

    for k, v in install_pip.items():
        print(f"\n~~~~~~~~~ {k} : {v} ~~~~~~~~~")
        ctx.run(v, replace_env=False)


@intercept
def install_terraform(ctx):
    install_terraform = ctx["install_terraform"]

    with ctx.cd("../.."):
        for k, v in install_terraform.items():
            if "{local_bin_variable}" in v:
                v = v.format(local_bin_variable=ctx["local_bin_variable"])
            print(f"\n~~~~~~~~~ {k} : {v} ~~~~~~~~~")
            ctx.run(v, replace_env=False)


@intercept
def install_terragrunt(ctx):
    install_terragrunt = ctx["install_terragrunt"]

    with ctx.cd("../.."):
        for k, v in install_terragrunt.items():
            if "{local_bin_variable}" in v:
                v = v.format(local_bin_variable=ctx["local_bin_variable"])
            print(f"\n~~~~~~~~~ {k} : {v} ~~~~~~~~~")
            ctx.run(v, replace_env=False)


@intercept
def install_docker(ctx):
    install_docker_dict = ctx["install_docker"]

    with ctx.cd(".."):
        for k, v in install_docker_dict.items():
            print(f"\n~~~~~~~~~ {k} : {v} ~~~~~~~~~")
            ctx.run(v, replace_env=False)


@intercept
def install_kubectl(ctx):
    install_kubectl_dict = ctx["install_kubectl"]

    with ctx.cd(".."):
        for k, v in install_kubectl_dict.items():
            if "{local_bin_variable}" in v:
                v = v.format(local_bin_variable=ctx["local_bin_variable"])
            print(f"\n~~~~~~~~~ {k} : {v} ~~~~~~~~~")
            ctx.run(v, replace_env=False)


@intercept
def eks(ctx, create_destroy):
    list_cmd_from_dict(
        ctx=ctx, parent_dict=ctx["eks_deploy"], create_destroy=create_destroy,
    )


@intercept
def eks_alb(ctx, create_destroy):
    list_cmd_from_dict(
        ctx=ctx, parent_dict=ctx["eks_alb_deploy"], create_destroy=create_destroy,
    )


@intercept
def ecr_docker_deploy(ctx):
    ecr_deploy_dict = ctx["ecr_deploy"]
    docker_image_id = ctx["docker_image_id"]

    with ctx.cd(".."):
        for k, v in ecr_deploy_dict.items():
            if "path" not in k:
                v = (
                    v.format(docker_image_id=docker_image_id)
                    if "{docker_image_id}" in v
                    else v
                )
                print(f"\n~~~~~~~~~ {k} : {v} ~~~~~~~~~")
                ctx.run(v, replace_env=False)


@intercept
def terragrunt_state_create(ctx):
    terragrunt_state_dict = ctx["terragrunt_deploy"]["global"]

    with ctx.cd(terragrunt_state_dict["path"]):
        for k, v in terragrunt_state_dict.items():
            if "path" != k:
                print(f'\n~~~~~~~~~ {terragrunt_state_dict["path"]} : {v} ~~~~~~~~~')
                ctx.run(v, replace_env=False)


def terragrunt(ctx, create_delete):
    terragrunt_deploy_dict = ctx["terragrunt_deploy"]
    ctx["deploy_folder"]
    dict_items = (
        terragrunt_deploy_dict.items()
        if (create_delete == "create")
        else list(terragrunt_deploy_dict.items())[::-1]
    )

    for k, v in dict_items:
        with ctx.cd(v["path"]):
            for k_1, v_1 in v.items():
                if (k_1 != "path") and (
                    (k_1 != "destroy")
                    if create_delete == "create"
                    else (k_1 == "destroy")
                ):
                    print(f'---------- {v["path"]} : {v_1} ----------')
                    ctx.run(v_1, replace_env=False)


@intercept
def terragrunt_deploy(ctx):
    terragrunt(ctx=ctx, create_delete="create")


@intercept
def terragrunt_destroy(ctx):
    terragrunt(ctx=ctx, create_delete="delete")


@intercept
def rds_deploy(ctx):
    rds_dict = ctx["rds_deploy"]
    airflow_execution_cmd = rds_dict["connection_string"].format(
        rds_db_endpoint=ctx["rds_db_endpoint"], command=rds_dict["create_airflow_db"]
    )
    mlflow_execution_cmd = rds_dict["connection_string"].format(
        rds_db_endpoint=ctx["rds_db_endpoint"], command=rds_dict["create_mlflow_db"]
    )

    ctx.run(rds_dict["psql_install"])
    ctx.run(airflow_execution_cmd)
    ctx.run(mlflow_execution_cmd)


@intercept
def dashboard_deployment(ctx, dash_type, create_destroy):
    eks_dash_cmd = ctx["eks_deploy"]["dashboard"][dash_type]["deploy"][create_destroy]
    path = ctx["eks_deploy"]["path"]

    with ctx.cd(path):
        print(f"~~~~~~~ {path}, {eks_dash_cmd} ~~~~~~~")
        ctx.run(eks_dash_cmd, replace_env=False)


@intercept
def eks_scale_nodes(ctx):
    nodes_dict = ctx["terragrunt_deploy"]["workers"]
    path = nodes_dict["path"]

    with ctx.cd(path):
        for k, v in nodes_dict.items():
            if (k != "path") and (k != "destroy"):
                print(f"~~~~~~~ {k}, {v} ~~~~~~~")
                ctx.run(v, replace_env=False)


@task
def install_pip_cli(ctx):
    ctx["msg"] = "Installing Python & Pip"
    install_pip(ctx=ctx)


@task
def install_terraform_cli(ctx):
    ctx["msg"] = "Installing Terraform"
    install_terraform(ctx=ctx)


@task
def install_terragrunt_cli(ctx):
    ctx["msg"] = "Installing Terragrunt"
    install_terragrunt(ctx=ctx)


@task
def install_terragrunt_cli(ctx):
    ctx["msg"] = "Installing Terragrunt"
    install_terragrunt(ctx=ctx)


@task
def install_docker_cli(ctx):
    ctx["msg"] = "Installing Docker"
    install_docker(ctx=ctx)


@task
def install_kubectl_cli(ctx):
    ctx["msg"] = "Installing Kubectl"
    install_kubectl(ctx=ctx)


@task
def terragrunt_state_create_cli(ctx):
    ctx["msg"] = "Creating State Lock table and S3 Bucket"
    terragrunt_state_create(ctx=ctx)


@task
def terragrunt_deploy_cli(ctx):
    ctx["msg"] = "Creating AWS Infrastructure"
    terragrunt_deploy(ctx=ctx)


@task
def terragrunt_destroy_cli(ctx):
    ctx["msg"] = "Destryoing AWS Infrastructure"
    terragrunt_destroy(ctx=ctx)


@task
def rds_deploy_cli(ctx):
    ctx["msg"] = "Deploying RDS Databases"
    rds_deploy(ctx=ctx)


@task
def ecr_docker_deploy_cli(ctx):
    ctx["msg"] = "Building & Pushing Docker-Image to ECR"
    ecr_docker_deploy(ctx=ctx)


@task
def eks_deploy_cli(ctx):
    ctx["msg"] = "Creating EKS ALB Object"
    eks(ctx=ctx, create_destroy="create")


@task
def eks_destroy_cli(ctx):
    ctx["msg"] = "Destroying EKS ALB Object"
    eks(ctx=ctx, create_destroy="delete")


@task
def eks_alb_deploy_cli(ctx):
    ctx["msg"] = "Creating EKS Objects"
    eks_alb(ctx=ctx, create_destroy="create")


@task
def eks_alb_destroy_cli(ctx):
    ctx["msg"] = "Destroying EKS Objects"
    eks_alb(ctx=ctx, create_destroy="delete")


@task
def eks_eda_dash_deploy_cli(ctx):
    ctx["msg"] = "Deploy EDA Dashboard"
    dashboard_deployment(ctx=ctx, dash_type="eda", create_destroy="create")


@task
def eks_eda_dash_destroy_cli(ctx):
    ctx["msg"] = "Destroy EDA Dashboard"
    dashboard_deployment(ctx=ctx, dash_type="eda", create_destroy="delete")


@task
def eks_eval_dash_deploy_cli(ctx):
    ctx["msg"] = "Deploy EVAL Dashboard"
    dashboard_deployment(ctx=ctx, dash_type="eval", create_destroy="create")


@task
def eks_eval_dash_destroy_cli(ctx):
    ctx["msg"] = "Destroy EVAL Dashboard"
    dashboard_deployment(ctx=ctx, dash_type="eval", create_destroy="delete")


@task
def eks_scale_nodes_cli(ctx):
    ctx["msg"] = "Scaling Nodes"
    eks_scale_nodes(ctx=ctx)
