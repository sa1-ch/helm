terraform {
  backend "azurerm" {
    resource_group_name  = "BackendResourceGroup"
    storage_account_name = "taazterraformstate"
    container_name       = "tfstate"
    key                  = "staging/storage/prod.terraform.tfstate"
  }
}