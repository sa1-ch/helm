variable "aws_region" {
  description = "aws region"
  default = "us-east-1"
  type = string
}

variable "state_bucket" {
  description = "S3 bucket to persist terraform state"
  default = "mle-terraform-state"
  type = string
}

variable "ebs_availability_zone" {
  description = "ebs availability zone"
  default = "us-east-1a"
  type = string
}

variable "storage_tag" {
  description = "tags for storage"
  default = "tiger-mle-storage"
  type = string
}

variable "ebs_device_name" {
  description = "device name for ebs volume"
  default = "/dev/sdh"
  type = string
}

variable "ebs_volume_size" {
  description = "ebs volume size"
  default = 8
  type = number
}

variable "ec2_availability_zone" {
  description = "ec2 availability zone"
  type = string
}

variable "ec2_instance_id" {
  description = "ec2 instance id"
  type = string
}

