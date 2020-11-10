resource "azurerm_resource_group" "terraformbackend" {
    name     = var.backend_rg_name
    location = var.location

    tags = {
        environment = var.environment_tag
    }
}

resource "azurerm_storage_account" "terraform_state" {
    name                        = var.backend_storage_accont_name
    resource_group_name         = azurerm_resource_group.terraformbackend.name
    location                    = azurerm_resource_group.terraformbackend.location 
    account_tier                = var.account_tier
    account_replication_type    = var.account_replication_type

    tags = {
        environment = var.environment_tag
    }
}

resource "azurerm_storage_container" "terraform_state_container" {
  name                  = var.container_name
  storage_account_name  = azurerm_storage_account.terraform_state.name
  container_access_type = var.container_access_type
}

