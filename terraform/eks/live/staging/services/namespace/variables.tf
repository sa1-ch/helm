variable "iamrole_state_key" {
  description = "path for vpc state"
  default = "staging/iam/terraform.tfstate"
  type = string
}

variable "state_bucket" {
  description = "state bucket for terraform state"
  default = "mle-terraform-state"
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

variable "mle_sa" {
  description = "service account name"
  default = "mle-sa"
  type = string
}

variable "mle_sa_secret" {
  description = "service account name"
  default = "mle-sa-secret"
  type = string
}

variable "automount_service_account_token" {
  description = "automount service account token"
  default = "true"
  type = string
}

variable "mle-sa-ns" {
  description = "namespace of service account"
  default = "ts-eks-ns"
  type = string
}

variable "mle_ns" {
  description = "namespace of service account"
  default = "ts-eks-ns"
  type = string
}

