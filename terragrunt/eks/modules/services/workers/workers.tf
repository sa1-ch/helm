resource "aws_launch_template" "asg_instance_template"{
  image_id = var.image_id
  instance_type = local.workers_group_defaults["instance_type"]
  key_name = local.workers_group_defaults["key_name"]
  iam_instance_profile {
    name = var.worker_instance_profile_id
  }
  vpc_security_group_ids  = [var.cluster_security_group_id]
  name_prefix = local.aws_launch_template_name
  user_data = base64encode(data.template_file.userdata.rendered)
}

resource "aws_autoscaling_group" "smn" {
  count = local.worker_group_count
  name =  lookup(var.worker_groups[count.index],"name",local.workers_group_defaults["name"])
  desired_capacity = lookup(var.worker_groups[count.index],"desired_capacity",local.workers_group_defaults["asg_desired_capacity"])
  max_size = lookup(var.worker_groups[count.index],"max_size",local.workers_group_defaults["asg_max_size"])
  min_size = lookup(var.worker_groups[count.index],"min_size",local.workers_group_defaults["asg_min_size"])
  default_cooldown = lookup(var.worker_groups[count.index],"default_cooldown",local.workers_group_defaults["default_cooldown"])
  force_delete = lookup(var.worker_groups[count.index],"force_delete",local.workers_group_defaults["asg_force_delete"])
  target_group_arns = lookup(var.worker_groups[count.index],"target_group_arns",local.workers_group_defaults["target_group_arns"])
  vpc_zone_identifier = var.subnet_ids
  termination_policies = lookup(var.worker_groups[count.index],"termination_policies",local.workers_group_defaults["termination_policies"])
  suspended_processes = lookup(var.worker_groups[count.index],"suspended_processes",local.workers_group_defaults["suspended_processes"])
  service_linked_role_arn = lookup(var.worker_groups[count.index],"service_linked_role_arn",local.workers_group_defaults["service_linked_role_arn"])
  protect_from_scale_in = lookup(var.worker_groups[count.index],"protect_from_scale_in",local.workers_group_defaults["protect_from_scale_in"])
  enabled_metrics = lookup(var.worker_groups[count.index],"enabled_metrics",local.workers_group_defaults["enabled_metrics"])
  placement_group = lookup(var.worker_groups[count.index],"placement_group",local.workers_group_defaults["placement_group"])
  max_instance_lifetime = lookup(var.worker_groups[count.index],"max_instance_lifetime",local.workers_group_defaults["max_instance_lifetime"])
  health_check_grace_period = lookup(var.worker_groups[count.index],"health_check_grace_period",local.workers_group_defaults["health_check_grace_period"])

  mixed_instances_policy {
    launch_template {
          launch_template_specification {
            launch_template_id = aws_launch_template.asg_instance_template.id
            version = "$Latest"
          }

          override {
                #name_prefix = "${var.cluster_id}-${lookup(var.worker_groups[count.index], "name", count.index)}"
                #image_id = lookup(var.worker_groups[count.index],"image_id",local.workers_group_defaults["image_id"])
                instance_type = lookup(var.worker_groups[count.index],"instance_type",local.workers_group_defaults["instance_type"])
                #user_data = base64encode(data.template_file.userdata.*.rendered[count.index])
                #key_name = lookup(var.worker_groups[count.index],"key_name",local.workers_group_defaults["key_name"])
                #iam_instance_profile = coalescelist(aws_iam_instance_profile.workers.*.id,data.aws_iam_instance_profile.custom_worker_group_iam_instance_profile.*.name,)[count.index]
                #security_group_names = [var.cluster_security_group_id]
          }
        }

        instances_distribution {
          on_demand_allocation_strategy = lookup(var.worker_groups[count.index],"on_demand_allocation_strategy",local.workers_group_defaults["on_demand_allocation_strategy"])
          spot_allocation_strategy = lookup(var.worker_groups[count.index],"spot_allocation_strategy",local.workers_group_defaults["spot_allocation_strategy"])
          spot_instance_pools = lookup(var.worker_groups[count.index],"spot_instance_pools",local.workers_group_defaults["spot_instance_pools"])
          on_demand_base_capacity = lookup(var.worker_groups[count.index],"on_demand_base_capacity",local.workers_group_defaults["on_demand_base_capacity"])
          on_demand_percentage_above_base_capacity = lookup(var.worker_groups[count.index],"on_demand_percentage_above_base_capacity",local.workers_group_defaults["on_demand_percentage_above_base_capacity"])
          spot_max_price = lookup(var.worker_groups[count.index],"spot_max_price",local.workers_group_defaults["spot_max_price"])
        }
  }

  tags = concat(
    [
      {
        "key"                 = "Name"
        "value"               = lookup(var.worker_groups[count.index],"instance_name",local.workers_group_defaults["instance_name"])
        "propagate_at_launch" = true
      },
      {
        "key"                 = "kubernetes.io/cluster/${var.cluster_id}"
        "value"               = "owned"
        "propagate_at_launch" = true
      },
      {
        "key"                 = "k8s.io/cluster/${var.cluster_id}"
        "value"               = "owned"
        "propagate_at_launch" = true
      },
      {
        "key"                 = "k8s.io/cluster-autoscaler/enabled"
        "value"               = "true"
        "propagate_at_launch" = true
      },
      {
        "key"                 = "k8s.io/cluster-autoscaler/${var.cluster_id}"
        "value"               = "owned"
        "propagate_at_launch" = true
      }
    ],
    local.asg_tags,
    lookup(
      var.worker_groups[count.index],
      "tags",
      local.workers_group_defaults["tags"]
    )
  )


}

resource "aws_iam_role" "workers" {
  count                 = var.manage_worker_iam_resources && var.create_eks ? 1 : 0
  name_prefix           = var.workers_role_name != "" ? null : var.cluster_id
  name                  = var.workers_role_name != "" ? var.workers_role_name : null
  assume_role_policy    = data.aws_iam_policy_document.workers_assume_role_policy.json
  permissions_boundary  = var.permissions_boundary
  path                  = var.iam_path
  force_detach_policies = true
  tags                  = var.tags
}


resource "aws_iam_instance_profile" "workers" {
  count       = var.manage_worker_iam_resources && var.create_eks ? local.worker_group_count : 0
  name_prefix = var.cluster_id
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
