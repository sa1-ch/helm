terraform {
  source = "${get_terragrunt_dir()}/../../../modules//networking"
}

include  {
  path = find_in_parent_folders()
}

inputs = {
aws_region = "us-east-1"
vpc_cidr_block         = "10.0.0.0/16"
resource_tag           = "tiger-mle-tg"
azs                    = ["us-east-1a","us-east-1b"]
private_subnets        = ["10.0.0.0/20", "10.0.16.0/20"]
public_subnets         = ["10.0.64.0/20", "10.0.80.0/20"]
eks_cluster_name       = "tiger-mle-eks"
route_table_dest_cidr  = "0.0.0.0/0"
sg_name                = "vpc-sg"
sg_tcp_from_port       = 8080
sg_tcp_to_port         = 8085
ingress_ip             = ["182.75.175.34/32","1.22.172.58/32"]
ssh_port               = 22
}
