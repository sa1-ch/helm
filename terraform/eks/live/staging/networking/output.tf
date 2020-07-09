output "vpc_id" {
  value = module.dev_vpc.vpc_id
  description = "vpc id created"
}

output "private_subnet_id" {
  value = module.dev_vpc.private_subnet_id
  description = "subnet id created"
}

output "persistence_private_subnet_id" {
  value = module.dev_vpc.persistence_private_subnet_id
  description = "subnet id created"
}

output "public_subnet_id" {
  value = module.dev_vpc.public_subnet_id
  description = "subnet id created"
}

output "sg_id" {
  value = module.dev_vpc.sg_id
  description = "security group"
}
