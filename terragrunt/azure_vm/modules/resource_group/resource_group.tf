resource "azurerm_resource_group" "myterraformgroup" {
    name     = "myTerraformTerragruntResourceGroup"
    location = "eastus"

    tags = {
        environment = "Terraform Demo"
    }
}