resource "aws_route" "tiger-mle-ia" {
  route_table_id = aws_vpc.tiger-mle-vpc.main_route_table_id
  destination_cidr_block = var.route_table_dest_cidr
  gateway_id = aws_internet_gateway.tiger-mle-ig.id
}

