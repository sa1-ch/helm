data "terraform_remote_state" "eks_cluster" {
  backend = "s3"

  config = {
    bucket = var.state_bucket
    key    = var.eks_cluster_state_key
    region = var.aws_region
  }
}

