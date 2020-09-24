resource "aws_eks_cluster" "tiger-mle-eks" {
  count                     = var.create_eks ? 1 : 0
  name = var.eks_cluster_name
  role_arn = var.role_arn
  version = 1.15
  vpc_config {
    subnet_ids = var.subnet_ids
    security_group_ids      = compact([local.cluster_security_group_id])
    endpoint_private_access = var.endpoint_private_access
    endpoint_public_access  = var.endpoint_public_access

  }  
}

