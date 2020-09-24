terraform {
  backend "s3" {}
}

provider "aws" {
  region = "us-east-1"
  version = "~> 2.8"
}

