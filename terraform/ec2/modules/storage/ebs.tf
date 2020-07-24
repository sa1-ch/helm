resource "aws_ebs_volume" "tiger-mle-ebs" {
  availability_zone = var.ec2_availability_zone
  size = var.ebs_volume_size

  tags = {
    Name = var.storage_tag
  }
}
