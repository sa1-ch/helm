output "dns_name" {
  value = module.dev_efs.dns_name
  description = "dns name"
}

output "arn" {
  value = module.dev_efs.arn
  description = " efs arn"
}

output "mount_target_dns_name" {
  value = module.dev_efs.mount_target_dns_name
  description = "The DNS name for the given subnet"
}

output "availability_zone_name" {
  value = module.dev_efs.availability_zone_name
  description = "The name of the Availability Zone (AZ) that the mount target resides in"
}
