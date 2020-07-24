terraform {
  source = "${get_terragrunt_dir()}/../../../modules//storage"
}

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

