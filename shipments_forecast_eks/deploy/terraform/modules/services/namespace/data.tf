data "terraform_remote_state" "eks_cluster" {
  backend = "s3"

  config = {
    bucket = var.state_bucket
    key    = var.eks_cluster_state_key
    region = "us-east-1"
  }
}

data "aws_eks_cluster" "cluster" {
  name = data.terraform_remote_state.eks_cluster.outputs.cluster_id
}

data "aws_eks_cluster_auth" "cluster" {
  name = data.terraform_remote_state.eks_cluster.outputs.cluster_id
}

