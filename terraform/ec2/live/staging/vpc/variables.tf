variable "aws_region" {
  description = "aws region"
  default = "us-east-1"
  type = string
}

variable "aws_provider_version" {
  description = "provider version"
  default = "~> 2.8"
  type = string
}

variable "state_bucket" {
  description = "S3 bucket to persist terraform state"
  default = "mle-terraform-state"
  type = string
}

variable "sse_algorithm" {
  description = "server side encryption for s3 bucket"
  default = "AES256"
  type = string
}

variable "tf_state_lock_table" {
  description = "dynamodb table for terraform state lock"
  default = "tf_state_lock"
  type = string
}

variable "instance_ami" {
  description = "ami image for ec2 insatnce"
  default = "ami-0323c3dd2da7fb37d"
  type = string
}

variable "vpc_cidr_block" {
  description = "cidr block for vpc"
  default = "10.0.0.0/16"
  type = string
}

variable "ebs_availabiltiy_zone" {
  description = "ebe availability zone"
  default = "us-east-1a"
  type = string
}

variable "resource_tag" {
  description = "tags to idemtify resources"
  default = "tiger-mle"
  type = string
}

variable "subnet_cidr_block" {
  description = "ip address range for subnet"
  default = "10.0.1.0/24"
  type = string
}

variable "route_table_dest_cidr" {
  description = "destination ip address for vpc route table"
  default = "0.0.0.0/0"
  type = string
}

variable "sg_name" {
  description = "secuirty group name"
  default = "tiger-mle-sg"
  type = string
}

variable "ingress_ip" {
  description = "ips for ingress"
  default = ["182.75.175.34/32","1.22.172.58/32"]
  type = list(string)
}

variable "sg_tcp_from_port" {
  description = "security group inbound port"
  default = 8080
  type = number
}

variable "sg_tcp_to_port" {
  description = "security group inbound port"
  default = 8085
  type = number
}

variable "ssh_port" {
  description = "port for ssh connection"
  default = 22
  type = number
}

variable "storage_tag" {
  description = "tags for storage"
  default = "tiger-mle-storage"
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

