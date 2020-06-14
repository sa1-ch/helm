output "vpc_id" {
  value = module.dev_vpc.vpc_id
  description = "vpc id created"
}

output "subnet_id" {
  value = module.dev_vpc.subnet_id
  description = "subnet id created"
}

output "sg_id" {
  value = module.dev_vpc.sg_id
  description = "security group"
}
