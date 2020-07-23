resource "aws_eks_node_group" "tiger-mle-eks-ng" {
  count = local.node_group_count
  cluster_name = var.cluster_name  
  node_group_name = lookup(var.node_groups[count.index], "name", local.node_group_defaults["name"])
  node_role_arn = aws_iam_role.eks_ng_role.arn
  subnet_ids = var.subnet_ids

  scaling_config {
    desired_size = lookup(var.node_groups[count.index], "desired_size", local.node_group_defaults["desired_size"])
    max_size =  lookup(var.node_groups[count.index], "max_size", local.node_group_defaults["max_size"])
    min_size = lookup(var.node_groups[count.index], "min_size", local.node_group_defaults["min_size"])

  }

  #lifecycle {
  #  ignore_changes = [scaling_config[0].desired_size]
  #}

  # declare more specific instance
  ami_type = lookup(var.node_groups[count.index], "ami_type", local.node_group_defaults["ami_type"])
  disk_size = lookup(var.node_groups[count.index], "disk_size", local.node_group_defaults["disk_size"])
  instance_types = lookup(var.node_groups[count.index], "instance_types", local.node_group_defaults["instance_types"])
  labels = lookup(var.node_groups[count.index], "labels", local.node_group_defaults["labels"])
  version = var.cluster_version
  tags = lookup(var.node_groups[count.index], "tags", local.node_group_defaults["tags"])

  remote_access {
    ec2_ssh_key = lookup(var.node_groups[count.index], "ec2_ssh_key", local.node_group_defaults["ec2_ssh_key"])
    source_security_group_ids = lookup(var.node_groups[count.index], "source_security_group_ids", local.node_group_defaults["source_security_group_ids"])
  }
}
