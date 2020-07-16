variable "name" {
  description = "bastion security group name"
  type = string
  default = "bastion-sg"
}

variable "vpc_id" {
  description = "bastion host vpc id"
  type = string
  default = ""

}

variable "name_tag" {
  description = "name tag for bastion sg"
  type = string
  default = ""
}

variable "sg_rules" {
  description = "inbound/outbound list"
  type = list
  default = []
}

variable "instance_ami" {
  description = "instance ami"
  type = string
  default = "ami-0323c3dd2da7fb37d"

}


variable "ec2_instance_type" {
  description = "instance type for ec2 instance"
  default = "t2.medium"
  type = string
}

variable "subnet_id" {
  description = "subnet id"
  default = ""
  type = string
}


variable "key_pair_name" {
  description = "key pair name for ssh connection"
  default = "tiger-mle-ec2-keys"
  type = string
}

variable "associate_public_ip_address" {
  description = "public ip"
  default = true
  type = bool
}
variable "aws_region" {
  description = "aws region"
  default = "us-east-1"
  type = string
}

variable "compute_tag" {

  description = "tag for compute"

  default = "tiger-mle-compute"

  type = string

}

variable "bastion_from_port" {
  description = "from port"
  default = 0
  type = number
}

variable "cluster_sg" {
  description = "eks cluster sg"
  default = ""
  type = string
}

variable "bastion_to_port" {
  description = "ingress to port"
  default = 0
  type = number
}

variable "bastion_protocol" {
  description = "from port"
  default = "-1"
  type = string
}


