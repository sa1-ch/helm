module "dev_compute" {
  source = "../../modules/compute"

  state_bucket = "mle-terraform-state"
  vpc_state_key = "staging/vpc/terraform.tfstate"
  aws_region = "us-east-1"
  instance_ami = "ami-0323c3dd2da7fb37d"
  ec2_instance_type = "t2.micro"
  key_pair_name = "tiger-mle"
  compute_tag = "tiger-mle-compute"
  
}
