data "terraform_remote_state" "eks_cluster" {
  backend = "s3"

  config = {
    bucket = var.state_bucket
    key    = var.eks_cluster_state_key
    region = var.aws_region
  }
}

data "terraform_remote_state" "vpc" {
  backend = "s3"

  config = {
    bucket = var.state_bucket
    key    = var.vpc_state_key
    region = var.aws_region
  }
}

data "terraform_remote_state" "iam_role" {
  backend = "s3"

  config = {
    bucket = var.state_bucket
    key    = var.iamrole_state_key
    region = var.aws_region
  }
}

data "aws_iam_policy_document" "workers_assume_role_policy" {
  statement {
    sid = "EKSWorkerAssumeRole"

    actions = [
      "sts:AssumeRole",
    ]

    principals {
      type        = "Service"
      identifiers = [local.ec2_principal]
    }
  }
}

data "aws_partition" "current" {}

data "aws_ami" "eks_worker" {
  filter {
    name   = "name"
    values = [local.worker_ami_name_filter]
  }

  most_recent = true

  owners = [var.worker_ami_owner_id]
}

data "aws_iam_instance_profile" "custom_worker_group_iam_instance_profile" {
  count = var.manage_worker_iam_resources ? 0 : local.worker_group_count
  name = lookup(
    var.worker_groups[count.index],
    "iam_instance_profile_name",
    local.workers_group_defaults["iam_instance_profile_name"],
  )
}

data "template_file" "userdata" {
  #count = local.worker_group_count
  template = file("${path.module}/templates/userdata.sh.tpl")
  vars = merge({
    platform = local.workers_group_defaults["platform"]
    cluster_name = "${data.terraform_remote_state.eks_cluster.outputs.cluster_id}"
    endpoint = "${data.terraform_remote_state.eks_cluster.outputs.eks_endpoint}"
    cluster_auth_base64 = coalescelist([data.terraform_remote_state.eks_cluster.outputs.certificate_authority[0].data],[""])[0]
    pre_userdata = local.workers_group_defaults["pre_userdata"]
    additional_userdata = local.workers_group_defaults["additional_userdata"]
    bootstrap_extra_args = local.workers_group_defaults["bootstrap_extra_args"]
    kubelet_extra_args = local.workers_group_defaults["kubelet_extra_args"]
  },
  local.workers_group_defaults["userdata_template_extra_args"]
 )
  
}
