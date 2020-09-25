output "eks_asg_id" {
  value = aws_autoscaling_group.workers_launch_template.*.id
  description = "asg workers id"
}


output "eks_asg_arn" {
  value = aws_autoscaling_group.workers_launch_template.*.arn
  description = "asg arn"
}

