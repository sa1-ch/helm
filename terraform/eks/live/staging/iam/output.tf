output "eks_role_arn" {
  value = module.iam_role.eks_role_arn
  description = "eks role arn"
}

output "s3_role_arn" {
  value = module.iam_role.s3_role_arn
  description = "eks role arn"
}

output "worker_role_arn" {
  value = module.iam_role.worker_role_arn
  description = "worker role arn"
}

output "worker_instance_profile_id" {
  value = module.iam_role.worker_instance_profile_id
  description = "instance profile id"
}

output "worker_instance_profile_name" {
  value = module.iam_role.worker_instance_profile_name
  description = "instance profile name"
}

output "worker_instance_profile_arn" {
  value = module.iam_role.worker_instance_profile_arn
  description = "instance profile arn"
}


