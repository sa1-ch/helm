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

variable "iamrole_state_key" {
  description = "path for vpc state"
  default = "staging/iam/terraform.tfstate"
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

variable "eks_role" {
  description = "role for eks"
  default = "tiger-mle-eks-role"
  type = string
}

variable "worker_create_security_group" {
  description = "Whether to create a security group for the workers or attach the workers to `worker_security_group_id`."
  type        = bool
  default     = true
}

variable "create_eks" {
  description = "Controls if EKS resources should be created (it affects almost all resources)"
  type        = bool
  default     = true
}

variable "cluster_create_security_group" {
  description = "Whether to create a security group for the cluster or attach the cluster to `cluster_security_group_id`."
  type        = bool
  default     = true
}

variable "cluster_security_group_id" {
  description = "If provided, the EKS cluster will be attached to this security group. If not given, a security group will be created with necessary ingress/egress to work with the workers"
  type        = string
  default     = ""
}

variable "worker_security_group_id" {
  description = "If provided, all workers will be attached to this security group. If not given, a security group will be created with necessary ingress/egress to work with the EKS cluster."
  type        = string
  default     = ""
}

variable "worker_sg_ingress_from_port" {
  description = "Minimum port number from which pods will accept communication. Must be changed to a lower value if some pods in your cluster will expose a port lower than 1025 (e.g. 22, 80, or 443)."
  type        = number
  default     = 1025
}

variable "worker_create_cluster_primary_security_group_rules" {
  description = "Whether to create security group rules to allow communication between pods on workers and pods using the primary cluster security group."
  type        = bool
  default     = false
}

variable "cluster_version" {
  description = "Kubernetes version to use for the EKS cluster."
  type        = string
  default     = "1.15"
}

variable "tags" {
  description = "A map of tags to add to all resources."
  type        = map(string)
  default     = {}
}

variable "namespace" {
  description = "namespace for service account"
  type = string
  default = "ts-eks-ns"
  
}

variable "service_account_name" {
  description = "service account name to create"
  type = string
  default = "s3-service-account"
}

variable "role_policy_arns" {
  description = "policy to attach"
  type = list
  default = ["arn:aws:iam::aws:policy/AmazonS3FullAccess"]
}

variable "role_arn" {
  description = "role arn for cluster"
  type = string
  default = ""
}

variable "subnet_ids" {
  description = "private subnets for cluster"
  type = list
  default = []
}

variable "vpc_id" {
  description = "vpc for cluster"
  type = string
  default = ""
}

variable "endpoint_public_access" {
  description = "Enable cluster end point public access"
  type        = bool
  default     = false
}

variable "endpoint_private_access" {
  description = "Enable cluster end point private access"
  type        = bool
  default     = true
}

variable "sa_iam_role" {
  description = "service account iam role"
  type = string
  default = ""

}
