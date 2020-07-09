output "eks_role_arn" {
  value = aws_iam_role.tiger-mle-eks-role.arn
  description = "eks role arn"
}

output "worker_role_arn" {
  value = aws_iam_role.tiger-mle-worker-role.arn
  description = "worker role arn"
}

output "worker_instance_profile_id" {
  value = aws_iam_instance_profile.worker_instance_profile.id
  description = "instance profile id"
}

output "worker_instance_profile_name" {
  value = aws_iam_instance_profile.worker_instance_profile.name
  description = "instance profile name"
}

output "worker_instance_profile_arn" {
  value = aws_iam_instance_profile.worker_instance_profile.arn
  description = "instance profile arn"
