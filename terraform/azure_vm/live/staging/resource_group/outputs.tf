
output "location" {
  value     = module.resource_group.location
  description = "location for the resource group"
}

output "resource_group_name" {
  value = module.resource_group.resource_group_name 
  description = "name of the resource group"
}