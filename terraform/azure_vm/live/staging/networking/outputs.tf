output "vn_name" {
  value = module.dev_vpc.vn_name
  description = "name of the virtual network"
}

output nic_id {
  value       = module.dev_vpc.nic_id
  description = "nic id"
}
