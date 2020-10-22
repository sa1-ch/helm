resource "azurerm_network_interface" "myterraformnic" {
    name                      =  var.nic_name 
    location                     =  data.terraform_remote_state.resource_group.outputs.location
    resource_group_name          =  data.terraform_remote_state.resource_group.outputs.resource_group_name

    ip_configuration {
        name                          =  var.nic_ip_config_name 
        subnet_id                     = azurerm_subnet.myterraformsubnet.id
        private_ip_address_allocation =  var.allocation_method 
        public_ip_address_id          = azurerm_public_ip.myterraformpublicip.id
    }

    tags = {
        environment = "Terraform Demo"
    }
}
