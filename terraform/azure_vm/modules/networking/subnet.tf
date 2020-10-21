resource "azurerm_subnet" "myterraformsubnet" {
    name  =  var.subnet_name 
    resource_group_name          =  data.terraform_remote_state.resource_group.outputs.resource_group_name
    virtual_network_name = azurerm_virtual_network.myterraformnetwork.name
    address_prefixes  = [var.subnet_ip]
}