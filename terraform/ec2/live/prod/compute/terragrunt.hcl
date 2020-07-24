terraform {
  source = "${get_terragrunt_dir()}/../../../modules//compute"
}

include {
  path = find_in_parent_folders()
}

dependencies {
  paths = ["../vpc"]
}

dependency "vpc" {
  config_path = "../vpc"
  mock_outputs = {
    sg_id     = "vpc-sg-dummy-id"
    subnet_id = "subnet-dummy-id"
  }
  mock_outputs_allowed_terraform_commands = ["validate","plan"]
}

inputs = {
  instance_ami      = "ami-0323c3dd2da7fb37d"
  ec2_instance_type = "t2.medium"
  key_pair_name     = "tiger-mle"
  compute_tag       = "tiger-mle-compute"
  sg_id             = [dependency.vpc.outputs.sg_id]
  subnet_id         = dependency.vpc.outputs.subnet_id
}

