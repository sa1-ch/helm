
output "location" {
  value     = azurerm_resource_group.myterraformgroup.location
  description = "location for the resource group"
}

output "resource_group_name" {
  value = azurerm_resource_group.myterraformgroup.name 
  description = "name of the resource group"
}