data "terraform_remote_state" "vpc" {
  backend = "s3"

  config = {
    bucket = var.state_bucket
    key    = var.vpc_state_key
    region = var.aws_region
  }
}

data "terraform_remote_state" "iam_role" {
  backend = "s3"

  config = {
    bucket = var.state_bucket
    key    = var.iamrole_state_key
    region = var.aws_region
  }
}

