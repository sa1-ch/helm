module "dev_vpc" {
  #evnetually, this will git versioned
  source = "../../../modules/networking"
  # setting vpc inputs
  vpc_cidr_block = var.vpc_cidr_block
  resource_tag = var.resource_tag
  azs = var.azs
  private_subnets = var.private_subnets
  public_subnets = var.public_subnets
  # setting subnet inputs
  eks_cluster_name = var.eks_cluster_name  

  #setting routing inputs
  route_table_dest_cidr = var.route_table_dest_cidr

  #setting security groups inputs
  sg_name = var.sg_name
  sg_tcp_from_port = var.sg_tcp_from_port
  sg_tcp_to_port = var.sg_tcp_to_port
  ingress_ip = var.ingress_ip
  ssh_port = var.ssh_port
  
}
