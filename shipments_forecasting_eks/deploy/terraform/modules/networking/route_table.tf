# Private routes
resource "aws_route_table" "private-subnet-rt" {
  count = length(var.private_subnets) > 0 ? 1 : 0
  vpc_id = aws_vpc.vpc.id
   
  tags = {
    Name = var.route_table_private_tag
  }

}

# Public routes
resource "aws_route_table" "public-subnet-rt" {
   count = length(var.public_subnets) > 0 ? 1 : 0
   vpc_id = aws_vpc.vpc.id
   

  tags = {
    Name = var.route_table_public_tag
  }


}

resource "aws_route" "public-subnet-route" {
  count = length(var.public_subnets) > 0 ? 1 : 0

  route_table_id = aws_route_table.public-subnet-rt[0].id
  destination_cidr_block = var.all_traffic
  gateway_id = aws_internet_gateway.ig[0].id
}

resource "aws_route" "private-subnet-route" {
  count = length(var.private_subnets) > 0 ? 1 : 0

  route_table_id = aws_route_table.private-subnet-rt[0].id
  destination_cidr_block = var.all_traffic
  gateway_id = aws_nat_gateway.nat-gtwy[0].id
}


