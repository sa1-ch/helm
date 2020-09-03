variable "eks_role" {
  description = "role for eks"
  default = "tiger-mle-eks-role"
  type = string
}

variable "worker_role" {
  description = "role for eks"
  default = "tiger-mle-worker-role"
  type = string
}

variable "worker_instance_profile" {
  description = "insatnce profile for worker"
  default = "worker_instance_profile"
  type = string
}

variable "s3_role" {
  description = "role for eks"
  default = "tiger-mle-s3-role"
  type = string
}

variable "aws_region" {
  description = "aws region"
  default = "us-east-1"
  type = string

}

variable "eks_autoscale_policy" {
  description = "policy for worker node for autoscale"
  default = "eks_autoscale_policy"
  type = string
}
