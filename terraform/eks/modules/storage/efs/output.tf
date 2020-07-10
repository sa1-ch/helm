output "dns_name" {
  value = aws_efs_file_system.efs.dns_name
  description = "dns name"
}

output "arn" {
  value = aws_efs_file_system.efs.arn
  description = " efs arn"
}

output "mount_target_dns_name" {
  value = aws_efs_mount_target.mount[*].mount_target_dns_name
  description = "The DNS name for the given subnet"
}

output "availability_zone_name" {
  value = aws_efs_mount_target.mount[*].availability_zone_name
  description = "The name of the Availability Zone (AZ) that the mount target resides in"
}
