output "eks_asg_id" {
  value = aws_autoscaling_group.smn.*.id
  description = "asg workers id"
}


output "eks_asg_arn" {
  value = aws_autoscaling_group.smn.*.arn
  description = "asg arn"
}

