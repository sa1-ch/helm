output "enhanced_monitoring_iam_role_name" {
  description = "The name of the monitoring role"
  value       = module.dev_rds.enhanced_monitoring_iam_role_name
}

output "enhanced_monitoring_iam_role_arn" {
  description = "The Amazon Resource Name (ARN) specifying the monitoring role"
  value       = module.dev_rds.enhanced_monitoring_iam_role_arn
}

output "this_db_instance_address" {
  description = "The address of the RDS instance"
  value       = module.dev_rds.this_db_instance_address
}

output "this_db_instance_arn" {
  description = "The ARN of the RDS instance"
  value       = module.dev_rds.this_db_instance_arn
}

output "this_db_instance_availability_zone" {
  description = "The availability zone of the RDS instance"
  value       = module.dev_rds.this_db_instance_availability_zone
}

output "this_db_instance_endpoint" {
  description = "The connection endpoint"
  value       = module.dev_rds.this_db_instance_endpoint
}

output "this_db_instance_hosted_zone_id" {
  description = "The canonical hosted zone ID of the DB instance (to be used in a Route 53 Alias record)"
  value       = module.dev_rds.this_db_instance_hosted_zone_id
}

output "this_db_instance_id" {
  description = "The RDS instance ID"
  value       = module.dev_rds.this_db_instance_id
}

output "this_db_instance_resource_id" {
  description = "The RDS Resource ID of this instance"
  value       = module.dev_rds.this_db_instance_resource_id
}

output "this_db_instance_status" {
  description = "The RDS instance status"
  value       = module.dev_rds.this_db_instance_status
}

output "this_db_instance_name" {
  description = "The database name"
  value       = module.dev_rds.this_db_instance_name
}

output "this_db_instance_username" {
  description = "The master username for the database"
  value       = module.dev_rds.this_db_instance_username
}

output "this_db_instance_port" {
  description = "The database port"
  value       = module.dev_rds.this_db_instance_port
}

output "this_db_instance_ca_cert_identifier" {
  description = "Specifies the identifier of the CA certificate for the DB instance"
  value       = module.dev_rds.this_db_instance_ca_cert_identifier
}
