# built-in function get_terragrunt_dir() returns the path of parent terragrunt.hcl file
# double slash (//) indicates the location of modules & terragrunt copies them as is to temp cache location & ensures the relative paths between modules work correctly
terraform {
  source = "${get_terragrunt_dir()}/../../../modules//storage"
}

# includes all settings from the root terragrunt.hcl file
# built-in function find_in_parent_folders() returns the absolute path of the parent terragrunt.hcl file
include {
  path = find_in_parent_folders()
}

dependencies {
  paths = ["../vpc", "../compute"]
}

dependency "vpc" {
  config_path = "../vpc"
  mock_outputs = {
    sg_id     = "vpc-sg-dummy-id"
    subnet_id = "subnet-dummy-id"
  }
  mock_outputs_allowed_terraform_commands = ["validate","plan"]
}

dependency "compute" {
  config_path = "../compute"
  mock_outputs = {
    ec2_availability_zone = "dummy-az"
    ec2_instance_id       = "dummy-instance-id"
  }
  mock_outputs_allowed_terraform_commands = ["validate","plan"]
}

inputs = {
  ebs_volume_size       = 8
  storage_tag           = "tiger-mle-storage"
  ebs_device_name       = "/dev/sdh"
  ec2_availability_zone = dependency.compute.outputs.ec2_availability_zone
  ec2_instance_id       = dependency.compute.outputs.ec2_instance_id
}

