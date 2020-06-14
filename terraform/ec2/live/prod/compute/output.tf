output "ec2_instance_id" {
  value = module.dev_compute.ec2_instance_id
  description = "ec2 instance id"
}

output "ec2_availabity_zone" {
  value = module.dev_compute.ec2_availabity_zone
  description = "availability zone where ec2 instance created"
}
