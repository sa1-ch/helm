resource "azurerm_resource_group" "terraformbackend" {
    name     = "BackendResourceGroup"
    location = "eastus"

    tags = {
        environment = "Terraform Demo"
    }
}