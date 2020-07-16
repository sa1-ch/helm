output "public_ip" {
  value = aws_instance.tiger-mle-ec2.public_ip
  description = "public ip for bastion host"
}
