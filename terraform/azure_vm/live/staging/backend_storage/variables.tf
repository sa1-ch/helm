variable backend_rg_name {
  type        = string
  default     = "BackendResourceGroup_dup"
  description = "name of the backend resource group"
}

variable location {
  type        = string
  default     = "eastus"
  description = "location of the backend resource group"
}

variable account_tier {
  type        = string
  default     = "Standard"
  description = "account tier type for storage account"
}

variable account_replication_type {
  type        = string
  default     = "LRS"
  description = "account replication type for storage account"
}

variable backend_storage_accont_name {
  type = string
  default = "taazterraformstate"
  description = "storage account name for the backend"
}

variable environment_tag {
  type        = string
  default     = "Terraform Demo"
  description = "tag for the storage account"
}

variable container_access_type {
  type        = string
  default     = "private"
  description = "container config"
}

variable container_name {
  type        = string
  default     = "tfstate"
  description = "name of the container"
}

