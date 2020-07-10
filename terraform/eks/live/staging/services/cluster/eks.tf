module "dev_eks" {
  source = "../../../../modules/services/cluster"

  state_bucket = var.state_bucket
  vpc_state_key = var.vpc_state_key
  aws_region = var.aws_region
  eks_cluster_name = var.eks_cluster_name
  eks_role = var.eks_role
  role_policy_arns = var.role_policy_arns

    
}
