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

variable "tags" {
  description = "efs tags"
  default = {}
  type = map(string)
}

variable "encrypted" {
  type        = bool
  description = "If true, the file system will be encrypted"
  default     = false
}

variable "kms_key_id" {
  type        = string
  description = "If set, use a specific KMS key"
  default     = null
}

variable "performance_mode" {
  type        = string
  description = "The file system performance mode. Can be either `generalPurpose` or `maxIO`"
  default     = "generalPurpose"
}

variable "provisioned_throughput_in_mibps" {
  default     = 0
  description = "The throughput, measured in MiB/s, that you want to provision for the file system. Only applicable with `throughput_mode` set to provisioned"
}

variable "throughput_mode" {
  type        = string
  description = "Throughput mode for the file system. Defaults to bursting. Valid values: `bursting`, `provisioned`. When using `provisioned`, also set `provisioned_throughput_in_mibps`"
  default     = "bursting"
}

variable "transition_to_ia" {
  type        = string
  description = "Indicates how long it takes to transition files to the IA storage class. Valid values: AFTER_7_DAYS, AFTER_14_DAYS, AFTER_30_DAYS, AFTER_60_DAYS and AFTER_90_DAYS"
  default     = ""
}

variable "subnets" {
  type        = list(string)
  description = "Subnet IDs"
  default = []
}

variable "mount_target_ip_address" {
  type        = string
  description = "The address (within the address range of the specified subnet) at which the file system may be mounted via the mount target"
  default     = ""
}

variable "security_groups" {
  type        = list(string)
  description = "Security group IDs to allow access to the EFS"
  default = []
}

