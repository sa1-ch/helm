terraform {
  backend "azurerm" {
    resource_group_name  = "BackendResourceGroup_dup"
    storage_account_name = "taazterraformstate"
    container_name       = "tfstate"
    key                  = "staging/resource_group/prod.terraform.tfstate"
  }
}