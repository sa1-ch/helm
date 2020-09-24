output "eks_asg_id" {
  value = aws_autoscaling_group.mle-eks-asg.*.id
  description = "asg workers id"
}


output "eks_asg_arn" {
  value = aws_autoscaling_group.mle-eks-asg.*.arn
  description = "asg arn"
}

