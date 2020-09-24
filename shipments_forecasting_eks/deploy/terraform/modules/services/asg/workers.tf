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


resource "aws_autoscaling_group" "mle-eks-asg" {
  count = var.create_eks ? local.worker_group_count : 0
  name = var.mle_eks_asg_name
  desired_capacity = var.asg_desired_size
  max_size = var.asg_max_size
  min_size = var.asg_min_size
  launch_configuration = aws_launch_configuration.mle-eks-asg-launch.*.id[count.index]
  vpc_zone_identifier = data.terraform_remote_state.eks_cluster.outputs.vpc_config[0].subnet_ids
  tags = concat(
    [
      {
        "key"                 = "Name"
        "value"               = "${var.mle_eks_asg_name}"
        "propagate_at_launch" = true
      },
      {
        "key"                 = "kubernetes.io/cluster/${data.terraform_remote_state.eks_cluster.outputs.cluster_id}"
        "value"               = "owned"
        "propagate_at_launch" = true
      },
      {
        "key"                 = "k8s.io/cluster/${data.terraform_remote_state.eks_cluster.outputs.cluster_id}"
        "value"               = "owned"
        "propagate_at_launch" = true
      },
    ],
    local.asg_tags,
    lookup(
      var.worker_groups[count.index],
      "tags",
      local.workers_group_defaults["tags"]
    )
  )
}

resource "aws_launch_configuration" "mle-eks-asg-launch" {
  count       = var.create_eks ? local.worker_group_count : 0
  name_prefix = "${data.terraform_remote_state.eks_cluster.outputs.cluster_id}-${lookup(var.worker_groups[count.index], "name", count.index)}"
  #security_groups = [data.terraform_remote_state.eks_cluster.outputs.vpc_config[0].cluster_security_group_id]
  security_groups = flatten([
    local.worker_security_group_id,
    var.worker_additional_security_group_ids,
    lookup(
      var.worker_groups[count.index],
      "additional_security_group_ids",
      local.workers_group_defaults["additional_security_group_ids"]
    )
  ])
  iam_instance_profile = coalescelist(
    aws_iam_instance_profile.workers.*.id,
    data.aws_iam_instance_profile.custom_worker_group_iam_instance_profile.*.name,
  )[count.index]
  image_id = var.asg_image_id
  instance_type = var.asg_instance_type
  key_name = "tiger-mle-ec2-keys"
  
}

resource "aws_iam_role" "workers" {
  count                 = var.manage_worker_iam_resources && var.create_eks ? 1 : 0
  name_prefix           = var.workers_role_name != "" ? null : data.terraform_remote_state.eks_cluster.outputs.cluster_id
  name                  = var.workers_role_name != "" ? var.workers_role_name : null
  assume_role_policy    = data.aws_iam_policy_document.workers_assume_role_policy.json
  permissions_boundary  = var.permissions_boundary
  path                  = var.iam_path
  force_detach_policies = true
  tags                  = var.tags
}

resource "aws_iam_instance_profile" "workers" {
  count       = var.manage_worker_iam_resources && var.create_eks ? local.worker_group_count : 0
  name_prefix = data.terraform_remote_state.eks_cluster.outputs.cluster_id
  role = lookup(
    var.worker_groups[count.index],
    "iam_role_id",
    local.default_iam_role_id,
  )

  path = var.iam_path
}

resource "aws_iam_role_policy_attachment" "workers_AmazonEKSWorkerNodePolicy" {
  count      = var.manage_worker_iam_resources && var.create_eks ? 1 : 0
  policy_arn = "${local.policy_arn_prefix}/AmazonEKSWorkerNodePolicy"
  role       = aws_iam_role.workers[0].name
}

resource "aws_iam_role_policy_attachment" "workers_AmazonEKS_CNI_Policy" {
  count      = var.manage_worker_iam_resources && var.attach_worker_cni_policy && var.create_eks ? 1 : 0
  policy_arn = "${local.policy_arn_prefix}/AmazonEKS_CNI_Policy"
  role       = aws_iam_role.workers[0].name
}

resource "aws_iam_role_policy_attachment" "workers_AmazonEC2ContainerRegistryReadOnly" {
  count      = var.manage_worker_iam_resources && var.create_eks ? 1 : 0
  policy_arn = "${local.policy_arn_prefix}/AmazonEC2ContainerRegistryReadOnly"
  role       = aws_iam_role.workers[0].name
}

resource "aws_iam_role_policy_attachment" "workers_additional_policies" {
  count      = var.manage_worker_iam_resources && var.create_eks ? length(var.workers_additional_policies) : 0
  role       = aws_iam_role.workers[0].name
  policy_arn = var.workers_additional_policies[count.index]
}

