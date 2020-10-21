resource "azurerm_virtual_network" "myterraformnetwork" {
    name                =  var.vn_name 
    address_space       = [var.address_space]
    location                     =  data.terraform_remote_state.resource_group.outputs.location
    resource_group_name          =  data.terraform_remote_state.resource_group.outputs.resource_group_name

    tags = {
        environment = "Terraform Demo"
    }
}











