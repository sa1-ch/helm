resource "azurerm_storage_account" "terraform_state" {
    name                        = "terraform-up-and-running-state"
    resource_group_name         = var.resource_group_name
    location                    = var.location
    account_tier                = var.account_tier
    account_replication_type    = var.account_replication_type

    tags = {
        environment = "Terraform Demo"
    }
}

