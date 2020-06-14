output "ec2_instance_id" {
  value = aws_instance.tiger-mle-ec2.id
  description = "ec2 instance id"
}

output "ec2_availabity_zone" {
  value = aws_instance.tiger-mle-ec2.availability_zone
  description = "availability zone where ec2 instance created"
}
