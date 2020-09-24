output "vpc_id" {
  value = aws_vpc.vpc.id
  description = "vpc id created"
}

output "private_subnet_id" {
  value = aws_subnet.private-subnet[*].id
  description = "subnet id created"
}

output "persistence_private_subnet_id" {
  value = aws_subnet.private-persistence-subnet[*].id
  description = "persistence subnet id"
}

output "public_subnet_id" {
  value = aws_subnet.public-subnet[*].id
  description = "subnet id created"
}

output "sg_id" {
  value = aws_security_group.sg.id
  description = "security group"
}

output "cidr_block" {
  value = aws_vpc.vpc.cidr_block
  description = "cidr block"
}
