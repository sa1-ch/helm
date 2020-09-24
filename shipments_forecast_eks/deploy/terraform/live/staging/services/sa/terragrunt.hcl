terraform {
  source = "${get_terragrunt_dir()}/../../../../modules/services//sa"
}

dependencies {
  paths = ["../cluster"]
}
include  {
  path = find_in_parent_folders()
}

dependency "eks_cluster" {
  config_path = "../cluster"

  mock_outputs = {
    sa_policy_arn = "arn:aws:iam::171774164293:policy/tiger-mle-eks-role"
  }

  mock_outputs_allowed_terraform_commands = ["validate","state"]
}

inputs = {
  region = "us-east-1" 
  mle_sa = "s3-service-account"
  mle_sa_secret = "mle-sa-secret"
  sa_iam_role = dependency.eks_cluster.outputs.sa_policy_arn
}
