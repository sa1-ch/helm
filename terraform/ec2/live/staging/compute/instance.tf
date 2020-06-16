module "dev_compute" {
  # eventually, this will be versioned url from git
  source = "../../../modules/compute"

  state_bucket = var.state_bucket
  vpc_state_key = var.vpc_state_key
  aws_region = var.aws_region
  instance_ami = var.instance_ami
  ec2_instance_type = var.ec2_instance_type
  key_pair_name = var.key_pair_name
  compute_tag = var.compute_tag
  
}
