resource "aws_ebs_volume" "tiger-mle-ebs" {
  availability_zone = "${aws_instance.tiger-mle-ec2.availability_zone}"
  size = var.ebs_volume_size

  tags = {
    Name = var.storage_tag
  }
}
