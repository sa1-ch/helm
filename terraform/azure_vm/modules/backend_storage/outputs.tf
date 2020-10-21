output "backend_rg_name"{
    value = azurerm_resource_group.terraformbackend.name 
    description = "name of the backend resource group"
}

output "backend_rg_location"{
    value = azurerm_resource_group.terraformbackend.location 
    description = "location of the backend resource group"
}
