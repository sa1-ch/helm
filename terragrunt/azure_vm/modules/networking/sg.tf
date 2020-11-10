resource "azurerm_network_security_group" "myterraformnsg" {
    name                =  var.nsg_name
    location                     =  data.terraform_remote_state.resource_group.outputs.location
    resource_group_name          =  data.terraform_remote_state.resource_group.outputs.resource_group_name


    security_rule {
        name                       =  var.security_rule_name 
        priority                   =  var.priority 
        direction                  =  var.direction 
        access                     =  var.access 
        protocol                   =  var.protocol 
        source_port_range          = "*"
        destination_port_range     =  var.destination_port_range 
        source_address_prefix      = "*"
        destination_address_prefix = "*"
    }

    tags = {
        environment = "Terraform Demo"
    }
}

resource "azurerm_network_interface_security_group_association" "example" {
    network_interface_id      = azurerm_network_interface.myterraformnic.id
    network_security_group_id = azurerm_network_security_group.myterraformnsg.id
}
