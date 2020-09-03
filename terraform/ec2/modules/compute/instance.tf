resource "aws_instance" "tiger-mle-ec2" {
  ami = var.instance_ami
  instance_type = var.ec2_instance_type
  vpc_security_group_ids = var.sg_id
  subnet_id = var.subnet_id
  key_name = var.key_pair_name

  tags = {
    Name = var.compute_tag
  }

}
