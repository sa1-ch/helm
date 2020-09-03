data "terraform_remote_state" "iam_role" {
  backend = "s3"

  config = {
    bucket = var.state_bucket
    key    = var.iamrole_state_key
    region = var.aws_region
  }
}

data "terraform_remote_state" "eks_cluster" {
  backend = "s3"

  config = {
    bucket = var.state_bucket
    key    = var.eks_cluster_state_key
    region = var.aws_region
  }
}

data "aws_eks_cluster" "cluster" {
  name = data.terraform_remote_state.eks_cluster.outputs.cluster_id
}

data "aws_eks_cluster_auth" "cluster" {
  name = data.terraform_remote_state.eks_cluster.outputs.cluster_id
}

