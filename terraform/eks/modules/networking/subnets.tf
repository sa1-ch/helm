# Private Subnet
resource "aws_subnet" "tiger-mle-eks-private-subnet" {
  vpc_id = "${aws_vpc.tiger-mle-vpc.id}"
  # read from variable
  count = 2
  cidr_block = element(concat(var.private_subnets, [""]), count.index)
  availability_zone = element(var.azs, count.index)

  tags = {
    Name = var.private_subnet_tag
  }

}


# Public Subnet
resource "aws_subnet" "tiger-mle-eks-public-subnet" {
  vpc_id = "${aws_vpc.tiger-mle-vpc.id}"
  # read from variable
  count = 2
  cidr_block = element(concat(var.public_subnets, [""]), count.index)
  availability_zone = element(var.azs, count.index)
  map_public_ip_on_launch = true
  #assign_ipv6_address_on_creation = true
  
  tags = {
    Name = var.public_subnet_tag
    "kubernetes.io/cluster/${var.eks_cluster_name}" = "shared"
    "kubernetes.io/role/elb" = "1"
  }
}

resource "aws_subnet" "tiger-mle-eks-private-persistence-subnet" {
  vpc_id = "${aws_vpc.tiger-mle-vpc.id}"
  # read from variable
  count = 2
  cidr_block = element(concat(var.private_persistence_subnets, [""]), count.index)
  availability_zone = element(var.azs, count.index)

  tags = {
    Name = var.private_persistence_subnet_tag
  }

}
