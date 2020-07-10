output "eks_asg_id" {
  value = module.workers.eks_asg_id
  description = "asg workers id"
}


output "eks_asg_arn" {
  value = module.workers.eks_asg_arn
  description = "asg arn"
}

