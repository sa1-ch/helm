module "dev_efs" {
  source = "../../../../modules/storage/efs/"
  tags = var.tags
  subnets = data.terraform_remote_state.vpc.outputs.private_subnet_id
  security_groups = [data.terraform_remote_state.eks_cluster.outputs.vpc_config[0].cluster_security_group_id]
}
