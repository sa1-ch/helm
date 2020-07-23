output "public_ip" {
  value = aws_instance.tiger-mle-ec2.public_ip
  description = "public ip for bastion host"
}

output "bastion_role_arn" {
  value = aws_iam_role.bastion.arn
  description = "bastion role arn"
}
