output "cluster_id" {
  value = module.dev_eks.cluster_id
  description = "created cluster id"
}

output "cluster_arn" {
  value = module.dev_eks.cluster_arn
  description = "created cluster arn"
}

output "certificate_authority" {
  value = module.dev_eks.certificate_authority
  description = "certificate authority"
}

output "eks_endpoint" {
  value = module.dev_eks.eks_endpoint
  description = "eks cluster endpoint"
}

output "vpc_config" {
  value = module.dev_eks.vpc_config
  description = "cluster vpc config"
}

output "cluster_version" {
  value =  module.dev_eks.cluster_version
  description = "cluster version"
}

output "sa_iam_role_arn" {
  value = module.dev_eks.sa_policy_arn
  description = "service account iam role arn"
}
