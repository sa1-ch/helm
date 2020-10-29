output "vn_name" {
  value = azurerm_virtual_network.myterraformnetwork.name
  description = "name of the virtual network"
}

output nic_id {
  value       = azurerm_network_interface.terraformnic.id
  description = "nic id"
}

