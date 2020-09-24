variable "state_bucket" {
  description = "state bucket for terraform state"
  default = "mle-terraform-state"
  type = string
}

variable "vpc_state_key" {
  description = "path for vpc state"
  default = "staging/eks/vpc/terraform.tfstate"
  type = string
}

variable "eks_cluster_state_key" {
  description = "path for vpc state"
  default = "staging/eks/services/eks/terraform.tfstate"
  type = string
}


variable "aws_region" {
  description = "aws region"
  default = "us-east-1"
  type = string

}

variable "eks_cluster_name" {
  description = "eks cluster name"
  default = "tiger-mle-eks"
  type = string
}

variable "eks_ng_role" {
  description = "role for eks"
  default = "tiger-mle-ng-role"
  type = string
}

variable "eks_ng_name" {
  description = "node group name"
  default = "tiger-mle-eks-ng"
  type = string
}

variable "eks_ng_desired_size" {
  description = "node group desired size"
  default = 1
  type = number
}

variable "eks_ng_max_size" {
  description = "node group max size"
  default = 2
  type = number
}

variable "eks_ng_min_size" {
  description = "node group min size"
  default = 1
  type = number
}

variable "eks_ng_ami_type" {
  description = "node group ami type"
  default = "AL2_x86_64"
  type = string
}

variable "eks_ng_disk_size" {
  description = "node group disk size"
  default = 20
  type = number
}

variable "eks_ng_instance_type" {
  description = "node group instance type"
  default = ["t3.medium"]
  type = list
}

variable "node_groups" {
  description = "node group"
  default = []
  type = list
}

variable "eks_autoscale_policy" {
  description = "policy for worker node for autoscale"
  default = "eks_autoscale_policy"
  type = string
}

variable "cluster_name" {
  description = "cluster name"
  default = ""
  type = string
}

variable "cluster_version" {
  description = "cluster version"
  default = ""
  type = string
}

variable "subnet_ids" {
  description = "private  subnet for nodegroup"
  default = []
  type = list
}

