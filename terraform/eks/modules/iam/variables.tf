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

variable "eks_autoscale_policy" {
  description = "policy for worker node for autoscale"
  default = "eks_autoscale_policy"
  type = string
}

variable "create_oidc_role" {
  description = "Whether to create a role"
  type        = bool
  default     = true
}

variable "aws_account_id" {
  description = "The AWS account ID where the OIDC provider lives, leave empty to use the account fo the AWS provider"
  type        = string
  default     = ""
}


variable "oidc_fully_qualified_subjects" {
  description = "The fully qualified OIDC subjects to be added to the role policy"
  type        = set(string)
  default     = []
}

variable "role_name" {
  description = "IAM role name"
  type        = string
  default     = ""
}

variable "role_path" {
  description = "Path of IAM role"
  type        = string
  default     = "/"
}

variable "max_session_duration" {
  description = "Maximum CLI/API session duration in seconds between 3600 and 43200"
  type        = number
  default     = 3600
}

variable "force_detach_policies" {
  description = "Whether policies should be detached from this role when destroying"
  type        = bool
  default     = false
}

variable "role_permissions_boundary_arn" {
  description = "Permissions boundary ARN to use for IAM role"
  type        = string
  default     = ""
}

variable "tags" {
  description = "A map of tags to add to IAM role resources"
  type        = map(string)
  default     = {}
}

variable "role_policy_arns" {
  description = "List of ARNs of IAM policies to attach to IAM role"
  type        = list(string)
  default     = []
}

