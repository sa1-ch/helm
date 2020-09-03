module "dev_ebs" {
  source = "../../../modules/storage"
  state_bucket = "mle-terraform-state"
  compute_state_key = "staging/compute/terraform.tfstate"
  aws_region = "us-east-1"
  ebs_volume_size = 8
  storage_tag = "tiger-mle-storage"
  ebs_device_name = "/dev/sdh"
}
