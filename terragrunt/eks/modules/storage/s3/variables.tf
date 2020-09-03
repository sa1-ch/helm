variable "aws_region" {
  description = "aws region"
  default = "us-east-1"
  type = string
}

variable "bucket_name" {
  description = "S3 bucket to persist terraform state"
  default = ""
  type = string
}

variable "sse_algorithm" {
  description = "server side encryption for s3 bucket"
  default = "AES256"
  type = string
}

variable "prevent_destroy" {
  description = "prevent accedental destroy"
  default = true
  type = bool
}

variable "versioned" {
  description = "enable version"
  default = true
  type = bool
}

variable "block_public_acls" {
  description = "block public access"
  default = true
  type = bool
}

variable "block_public_policy" {
  description = "block public access"
  default = true
  type = bool
}

variable "named_folders" {
  description = "S3 bucket object"
  default = []
  type = list(string)
}

variable "ignore_public_acls" {
  description = "block public access"
  default = true
  type = bool
}

variable "restrict_public_buckets" {
  description = "block public access"
  default = true
  type = bool
}

