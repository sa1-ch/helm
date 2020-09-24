resource "aws_route_table_association" "private-subnet-association" {
  count = length(var.private_subnets) > 0 ? length(var.private_subnets) : 0
  subnet_id = element(aws_subnet.private-subnet.*.id,count.index)
  route_table_id = aws_route_table.private-subnet-rt[0].id
}

resource "aws_route_table_association" "public-subnet-association" {
  count = length(var.public_subnets) > 0 ? length(var.public_subnets) : 0
  subnet_id      = element(aws_subnet.public-subnet.*.id,count.index)
  route_table_id = aws_route_table.public-subnet-rt[0].id
}

resource "aws_route_table_association" "persistence-private-subnet-association" {
  count = length(var.private_persistence_subnets) > 0 ? length(var.private_persistence_subnets) : 0
  subnet_id = element(aws_subnet.private-persistence-subnet.*.id,count.index)
  route_table_id = aws_route_table.private-subnet-rt[0].id
}
