data "terraform_remote_state" "resource_group" {
  backend = "azurerm"

  config = {
    resource_group_name  = "tg_BackendResourceGroup"
    storage_account_name = "tatgazterraformstate"
    container_name       = "tftgstate"
    key                  = "terragrunt/resource_group/terraform.tfstate"
  }
}

data "terraform_remote_state" "vpc" {
  backend = "azurerm"

  config = {
    resource_group_name  = "tg_BackendResourceGroup"
    storage_account_name = "tatgazterraformstate"
    container_name       = "tftgstate"
    key                  = "terragrunt/networking/terraform.tfstate"
  }
}

data "terraform_remote_state" "storage" {
  backend = "azurerm"

  config = {
    resource_group_name  = "tg_BackendResourceGroup"
    storage_account_name = "tatgazterraformstate"
    container_name       = "tftgstate"
    key                  = "terragrunt/storage/terraform.tfstate"
  }
}