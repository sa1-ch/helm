output "cluster_id" {
  value = aws_eks_cluster.tiger-mle-eks[0].id
  description = "created cluster id"
}

output "cluster_arn" {
  value = aws_eks_cluster.tiger-mle-eks[0].arn
  description = "created cluster arn"
}

output "certificate_authority" {
  value = aws_eks_cluster.tiger-mle-eks[0].certificate_authority
  description = "certificate authority"
}

output "eks_endpoint" {
  value =  aws_eks_cluster.tiger-mle-eks[0].endpoint
  description = "eks cluster endpoint"
}

output "vpc_config" {
  value = aws_eks_cluster.tiger-mle-eks[0].vpc_config
  description = "cluster vpc config"
}

output "cluster_version" {
  value = aws_eks_cluster.tiger-mle-eks[0].version
  description = "cluster vpc config"
}

output "sa_policy_arn" {
  value = aws_iam_role.sa_iam_role.arn
  description = "service account policy arn"
}
