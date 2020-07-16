resource "aws_eks_cluster" "tiger-mle-eks" {
  count                     = var.create_eks ? 1 : 0
  name = var.eks_cluster_name
  role_arn = var.role_arn
  vpc_config {
    subnet_ids = var.subnet_ids
    security_group_ids      = compact([local.cluster_security_group_id])
  }  
}

