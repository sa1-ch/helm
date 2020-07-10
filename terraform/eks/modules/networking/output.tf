output "vpc_id" {
  value = aws_vpc.tiger-mle-vpc.id
  description = "vpc id created"
}

output "private_subnet_id" {
  value = aws_subnet.tiger-mle-eks-private-subnet[*].id
  description = "subnet id created"
}

output "persistence_private_subnet_id" {
  value = aws_subnet.tiger-mle-eks-private-persistence-subnet[*].id
  description = "persistence subnet id"
}

output "public_subnet_id" {
  value = aws_subnet.tiger-mle-eks-public-subnet[*].id
  description = "subnet id created"
}

output "sg_id" {
  value = aws_security_group.tiger-mle-sg.id
  description = "security group"
}
