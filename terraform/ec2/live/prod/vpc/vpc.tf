module "dev_vpc" {
  source = "../../modules/vpc"
  # setting vpc inputs
  vpc_cidr_block = "10.0.0.0/16"
  resource_tag = "tiger-mle"

  # setting subnet inputs
  subnet_cidr_block = "10.0.1.0/24"
  

  #setting routing inputs
  route_table_dest_cidr = "0.0.0.0/0"

  #setting security groups inputs
  sg_name = "tiger-mle-sg"
  sg_tcp_from_port = 8080
  sg_tcp_to_port = 8085
  ingress_ip = ["182.75.175.34/32","1.22.172.58/32"]
  ssh_port = 22
  
}
