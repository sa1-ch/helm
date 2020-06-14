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

variable "instance_ami" {
  description = "ami image for ec2 insatnce"
  default = "ami-0323c3dd2da7fb37d"
  type = string
}

variable "ec2_instance_type" {
  description = "instance type for ec2 instance"
  default = "t2.medium"
  type = string
}

variable "key_pair_name" {
  description = "key pair name for ssh connection"
  default = "tiger-mle"
  type = string
}

variable "compute_tag" {
  description = "tag for compute"
  default = "tiger-mle-compute"
  type = string
}
