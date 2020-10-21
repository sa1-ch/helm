output resource_group_name {
  value =  azurerm_resource_group.myterraformgroup.name
  description = "name of the resource group"
}

output location {
  value = azurerm_resource_group.myterraformgroup.location
  description = "location of the resource group"
}