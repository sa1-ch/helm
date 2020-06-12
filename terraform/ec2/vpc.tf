resource "aws_vpc" "tiger-mle-vpc" {
  cidr_block = var.vpc_cidr_block
  enable_dns_hostnames = true

  tags = {
    Name = var.resource_tag
  }
}

