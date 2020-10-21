resource "azurerm_resource_group" "myterraformgroup" {
    name     = "myTerraformResourceGroup"
    location = "eastus"

    tags = {
        environment = "Terraform Demo"
    }
}