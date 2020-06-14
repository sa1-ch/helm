data "terraform_remote_state" "vpc" {
  backend = "s3"

  config = {
    bucket = var.state_bucket  
    key    = var.vpc_state_key
    region = var.aws_region
  }
}

resource "aws_instance" "tiger-mle-ec2" {
  ami = var.instance_ami
  instance_type = var.ec2_instance_type
  vpc_security_group_ids = [data.terraform_remote_state.vpc.outputs.sg_id]
  subnet_id = data.terraform_remote_state.vpc.outputs.subnet_id
  key_name = var.key_pair_name

  tags = {
    Name = var.compute_tag
  }

}
