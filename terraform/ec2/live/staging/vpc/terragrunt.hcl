terraform {
  source = "${get_terragrunt_dir()}/../../../modules//vpc"
}

include {
  path = find_in_parent_folders()
}

inputs = {
  vpc_cidr_block        = "10.0.0.0/16"
  resource_tag          = "kathir-test"
  route_table_dest_cidr = "0.0.0.0/0"
  sg_name               = "vpc-sg"
  sg_tcp_from_port      = 8080
  sg_tcp_to_port        = 8085
  ingress_ip            = ["182.75.175.34/32", "1.22.172.58/32"]
  ssh_port              = 22
}

