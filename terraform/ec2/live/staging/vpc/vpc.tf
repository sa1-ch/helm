module "dev_vpc" {
  #evnetually, this will git versioned
  source = "../../../modules/vpc"
  # setting vpc inputs
  vpc_cidr_block = var.vpc_cidr_block
  resource_tag = var.resource_tag

  # setting subnet inputs
  subnet_cidr_block = var.subnet_cidr_block
  

  #setting routing inputs
  route_table_dest_cidr = var.route_table_dest_cidr

  #setting security groups inputs
  sg_name = var.sg_name
  sg_tcp_from_port = var.sg_tcp_from_port
  sg_tcp_to_port = var.sg_tcp_to_port
  ingress_ip = var.ingress_ip
  ssh_port = var.ssh_port
  
}
