resource "aws_internet_gateway" "tiger-mle-ig" {
  vpc_id = "${aws_vpc.tiger-mle-vpc.id}"

  tags = {
    Name = "tiger-mle"
  }

}
