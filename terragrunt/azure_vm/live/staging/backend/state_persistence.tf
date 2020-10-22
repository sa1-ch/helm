resource "azurerm_resource_group" "terraformterragruntbackend" {
    name     = "tg_BackendResourceGroup"
    location = "eastus"

    tags = {
        environment = "Terraform Demo"
    }
}

resource "azurerm_storage_account" "terraform_state" {
    name                        = "tatgazterraformstate"
    resource_group_name         = azurerm_resource_group.terraformterragruntbackend.name
    location                    = azurerm_resource_group.terraformterragruntbackend.location 
    account_tier                = "Standard"
    account_replication_type    = "LRS"

    tags = {
        environment = "Terraform Demo"
    }
}

resource "azurerm_storage_container" "terraform_state_container" {
  name                  = "tftgstate"
  storage_account_name  = azurerm_storage_account.terraform_state.name
  container_access_type = "private"
}