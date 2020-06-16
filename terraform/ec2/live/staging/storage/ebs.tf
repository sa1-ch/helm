module "dev_ebs" {
  source = "../../../modules/storage"
  state_bucket = var.state_bucket
  compute_state_key = var.compute_state_key
  aws_region = var.aws_region
  ebs_volume_size = var.ebs_volume_size
  storage_tag = var.storage_tag
  ebs_device_name = var.ebs_device_name
}
