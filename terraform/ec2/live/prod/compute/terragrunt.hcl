# built-in function get_terragrunt_dir() returns the path of parent terragrunt.hcl file
# double slash (//) indicates the location of modules & terragrunt copies them as is to temp cache location & ensures the relative paths between modules work correctly
terraform {
  source = "${get_terragrunt_dir()}/../../../modules//compute"
}

# includes all settings from the root terragrunt.hcl file
# built-in function find_in_parent_folders() returns the absolute path of the parent terragrunt.hcl file
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

