data "terraform_remote_state" "instance" {
  backend = "s3"

  config = {
    bucket = var.state_bucket
    key    = var.compute_state_key
    region = var.aws_region
  }
}

resource "aws_ebs_volume" "tiger-mle-ebs" {
  availability_zone = data.terraform_remote_state.instance.outputs.ec2_availabity_zone
  size = var.ebs_volume_size

  tags = {
    Name = var.storage_tag
  }
}
