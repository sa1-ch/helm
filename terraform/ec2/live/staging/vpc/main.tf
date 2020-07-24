provider "aws" {
  region = var.aws_region
  version = "~> 2.8"
}

terraform {
  backend "s3" {}
}
