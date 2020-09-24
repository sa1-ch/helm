terraform {
  source = "${get_terragrunt_dir()}/../../../modules//iam"
}


include {
  path = find_in_parent_folders()
}

inputs = {
  aws_region              = "us-east-1"
  eks_role                = "eks_role"
  worker_role             = "eks_worker_role"
  s3_role                 = "eks_s3_role"
  worker_instance_profile = "worker_instance_profile"
  eks_autoscale_policy    = "eks_autoscale_policy_tg"
  

}
