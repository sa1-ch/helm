variable algorithm {
  type        = string
  default     = "RSA"
}


variable rsa_bits {
  type        = number
  default     = 4096
}

variable size {
  type        = string
  default     = "Standard_DS1_v2"
  description = "size of the VM"
}

variable vm_name {
  type        = string
  default     = "myVM"
  description = "name of the VM"
}

variable disk_name {
  type        = string
  default     = "myOsDisk"
  description = "disk name of the VM"
}

variable caching {
  type        = string
  default     = "ReadWrite"
  description = "caching of the disk"
}

variable storage_account_type {
  type        = string
  default     = "Premium_LRS"
  description = "storage of the disk"
}

variable publisher {
  type        = string
  default     = "Canonical"
}

variable offer {
  type        = string
  default     = "UbuntuServer"
}

variable sku {
  type        = string
  default     = "18.04-LTS"
}

variable computer_name {
  type        = string
  default     = "myvm"
}

variable user_name {
  type        = string
  default     = "azureuser"
}

variable disable_password_authentication {
  type        = bool
  default     = true
}













