resource "aws_internet_gateway" "ig" {
  count = length(var.public_subnets) > 0 ? 1 : 0
  vpc_id = aws_vpc.vpc.id

  tags = {
    Name = var.ig_resource_tag
  }

}
