# built-in function get_terragrunt_dir() returns the path of parent terragrunt.hcl file
# double slash (//) indicates the location of modules & terragrunt copies them as is to temp cache location & ensures the relative paths between modules work correctly
terraform {
  source = "${get_terragrunt_dir()}/../../../modules//vpc"
}

# includes all settings from the root terragrunt.hcl file
# built-in function find_in_parent_folders() returns the absolute path of the parent terragrunt.hcl file
include {
  path = find_in_parent_folders()
}

inputs = {
  vpc_cidr_block        = "10.0.0.0/16"
  resource_tag          = "tiger-mle-prod"
  route_table_dest_cidr = "0.0.0.0/0"
  sg_name               = "vpc-sg"
  sg_tcp_from_port      = 8080
  sg_tcp_to_port        = 8085
  ingress_ip            = ["182.75.175.34/32", "1.22.172.58/32"]
  ssh_port              = 22
}

