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

variable "state_bucket" {

  description = "S3 bucket to persist terraform state"

  default = "mle-terraform-state"

  type = string

}



variable "ebs_availabiltiy_zone" {

  description = "ebe availability zone"

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

variable "role_name_prefix" {
  description = "name prefix for iam role"
  default = "bastion_iam_role"
  type = string 

}

variable "role_name" {
  description = "name for iam role"
  default = "bastion_iam_role"
  type = string

}

variable "iam_role_path" {
  description = "If provided, all IAM roles will be created on this path."
  type        = string
  default     = "/"
}

variable "permissions_boundary" {
  description = "If provided, all IAM roles will be created with this permissions boundary attached."
  type        = string
  default     = null
}

variable "iam_role_tags" {
  description = "A map of tags to add to all resources."
  type        = map(string)
  default     = {}
}

variable "instance_profile_name_prefix" {
  description = "name prefix for iam role"
  default = "bastion_instance_profile"
  type = string

}

variable "instance_profile_path" {
  description = "If provided, all IAM roles will be created on this path."
  type        = string
  default     = "/"
}

variable "policies" {
  description = "name for iam role"
  default = ["AmazonEKSWorkerNodePolicy","AmazonEKS_CNI_Policy","AmazonEC2ContainerRegistryReadOnly"]
  type = list(string)

}

variable "policy_arn_prefix" {
  description = "arn prefix"
  type = string
  default = ""
}



