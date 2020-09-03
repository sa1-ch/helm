data "terraform_remote_state" "iam_role" {
  backend = "s3"

  config = {
    bucket = "mle-terragrunt-state"
    key    = "terragrunt/iam/terraform.tfstate"
    region = "us-east-1"
  }
}

data "terraform_remote_state" "eks_cluster" {
  backend = "s3"

  config = {
    bucket = "mle-terragrunt-state"
    key    = "terragrunt/services/cluster/terraform.tfstate"
    region = "us-east-1"
  }
}

data "aws_eks_cluster" "cluster" {
  name = data.terraform_remote_state.eks_cluster.outputs.cluster_id
}

data "aws_eks_cluster_auth" "cluster" {
  name = data.terraform_remote_state.eks_cluster.outputs.cluster_id
}

