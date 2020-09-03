resource "aws_internet_gateway" "tiger-mle-ig" {
  count = length(var.public_subnets) > 0 ? 1 : 0
  vpc_id = "${aws_vpc.tiger-mle-vpc.id}"

  tags = {
    Name = var.ig_resource_tag
  }

}
