resource "azurerm_public_ip" "myterraformpublicip" {
    name                         =  var.ip_name 
    location                     =  data.terraform_remote_state.resource_group.outputs.location
    resource_group_name          =  data.terraform_remote_state.resource_group.outputs.resource_group_name
    allocation_method            =  var.allocation_method 

    tags = {
        environment = "Terraform Demo"
    }
}