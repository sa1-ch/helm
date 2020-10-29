resource "azurerm_resource_group" "myterraformgroup" {
    name     = var.rg_name
    location = var.location

    tags = {
        environment = var.environment_tag
    }
}