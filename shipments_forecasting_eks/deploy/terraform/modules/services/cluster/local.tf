locals {
  cluster_security_group_id         = var.cluster_create_security_group ? join("", aws_security_group.cluster.*.id) : var.cluster_security_group_id
  cluster_primary_security_group_id = var.cluster_version >= 1.14 ? element(concat(aws_eks_cluster.tiger-mle-eks[*].vpc_config[0].cluster_security_group_id, list("")), 0) : null
  worker_security_group_id          = var.worker_create_security_group ? join("", aws_security_group.workers.*.id) : var.worker_security_group_id
}
