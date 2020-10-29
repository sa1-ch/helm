variable rg_name {
  type        = string
  default     = "myTerraformResourceGroup_dup;"
  description = "name of the resource group"
}

variable location {
  type        = string
  default     = "eastus"
  description = "location of the resource group"
}

variable environment_tag {
  type        = string
  default     = "Terraform Demo"
  description = "tag for the resource group"
}


