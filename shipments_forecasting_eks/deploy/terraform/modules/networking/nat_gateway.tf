resource "aws_nat_gateway" "nat-gtwy" {
  count = length(var.public_subnets) > 0 ? 1 : 0
  allocation_id = aws_eip.nat.id
  subnet_id     = element(aws_subnet.public-subnet.*.id,count.index)

  tags = {
    Name = "eks-nat"
  }
}
