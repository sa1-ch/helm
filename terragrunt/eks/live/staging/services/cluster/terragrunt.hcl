terraform {
  source = "${get_terragrunt_dir()}/../../../../modules/services//cluster"
}

dependencies {
  paths= ["../../networking","../../iam"]
}

dependency "vpc" {
  config_path = "../../networking"
  mock_outputs = {
    vpc_id = "vpc-dummy-id"
    private_subnet_id = ["dummy-1","dummy-2"]
  }

  mock_outputs_allowed_terraform_commands = ["validate","plan"]

}

dependency "iam_role" {
  config_path = "../../iam"

  mock_outputs = {
    eks_role_arn = "arn:aws:iam::171774164293:role/tiger-mle-eks-role"
  }

  mock_outputs_allowed_terraform_commands = ["validate","plan"]
}

include  {
  path = find_in_parent_folders()
}

inputs = {
  aws_region = "us-east-1"  
  eks_role = "eks-role"
  eks_cluster_name = "tiger-mle-eks-tg"
  role_policy_arns = ["arn:aws:iam::aws:policy/AmazonS3FullAccess"]
  role_arn         = dependency.iam_role.outputs.eks_role_arn
  subnet_ids       = dependency.vpc.outputs.private_subnet_id
  vpc_id           = dependency.vpc.outputs.vpc_id
  endpoint_private_access = false
  endpoint_public_access  = true
  sa_iam_role = "sa_iam_role_tg"
}
