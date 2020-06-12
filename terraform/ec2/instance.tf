resource "aws_instance" "tiger-mle-ec2" {
  ami = var.instance_ami
  instance_type = var.ec2_instance_type
  vpc_security_group_ids = [aws_security_group.tiger-mle-sg.id]
  subnet_id = "${aws_subnet.tiger-mle-subnet.id}"
  key_name = var.key_pair_name

  tags = {
    Name = var.compute_tag
  }

}
