resource "aws_instance" "tiger-mle-ec2" {

  ami = var.instance_ami

  instance_type = var.ec2_instance_type

 # vpc_security_group_ids = var.vpc_security_group_ids

  subnet_id = var.subnet_id
  vpc_security_group_ids = aws_security_group.bastion_sg[*].id
  key_name = var.key_pair_name
  associate_public_ip_address = var.associate_public_ip_address
  iam_instance_profile = aws_iam_instance_profile.bation.id  

  tags = {

    Name = var.compute_tag

  }



}
