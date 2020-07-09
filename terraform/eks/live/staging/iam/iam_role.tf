module "iam_role" {
  source = "../../../modules/iam"
  eks_role = var.eks_role
  worker_role = var.worker_role
  s3_role = var.s3_role
  worker_instance_profile = var.worker_instance_profile
}

