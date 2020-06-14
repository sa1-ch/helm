output "vpc_id" {
  value = aws_vpc.tiger-mle-vpc.id
  description = "vpc id created"
}

output "subnet_id" {
  value = aws_subnet.tiger-mle-subnet.id
  description = "subnet id created"
}

output "sg_id" {
  value = aws_security_group.tiger-mle-sg.id
  description = "security group"
}
