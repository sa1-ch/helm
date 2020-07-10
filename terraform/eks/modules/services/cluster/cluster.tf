resource "aws_eks_cluster" "tiger-mle-eks" {
  count                     = var.create_eks ? 1 : 0
  name = var.eks_cluster_name
  role_arn = data.terraform_remote_state.iam_role.outputs.eks_role_arn
  vpc_config {
    subnet_ids = data.terraform_remote_state.vpc.outputs.private_subnet_id
    security_group_ids      = compact([local.cluster_security_group_id])
  }  
}

