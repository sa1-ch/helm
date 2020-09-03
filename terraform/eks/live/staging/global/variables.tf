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

variable "sse_algorithm" {
  description = "server side encryption for s3 bucket"
  default = "AES256"
  type = string
}

variable "tf_state_lock_table" {
  description = "dynamodb table for terraform state lock"
  default = "tf_state_lock_table"
  type = string
}

variable "lock_hask_key" {
  description = "column for state lock"
  default = "LockID"
  type = string
}

