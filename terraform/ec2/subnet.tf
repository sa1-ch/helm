# Create a subnet to launch our instances into
resource "aws_subnet" "tiger-mle-subnet" {
  vpc_id = "${aws_vpc.tiger-mle-vpc.id}"
  cidr_block = var.subnet_cidr_block
  map_public_ip_on_launch = true

}

