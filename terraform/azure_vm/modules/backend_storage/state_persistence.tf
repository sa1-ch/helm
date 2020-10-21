resource "azurerm_storage_account" "terraform_state" {
    name                        = "taazterraformstate"
    resource_group_name         = azurerm_resource_group.terraformbackend.name
    location                    = azurerm_resource_group.terraformbackend.location 
    account_tier                = "Standard"
    account_replication_type    = "LRS"

    tags = {
        environment = "Terraform Demo"
    }
}

resource "azurerm_storage_container" "terraform_state_container" {
  name                  = "tfstate"
  storage_account_name  = azurerm_storage_account.terraform_state.name
  container_access_type = "private"
}