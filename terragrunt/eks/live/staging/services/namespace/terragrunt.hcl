terraform {
  source = "${get_terragrunt_dir()}/../../../../modules/services//namespace"
}

dependencies {
  paths = ["../cluster"]
}

dependency "eks_cluster" {
  config_path = "../cluster"
  
  mock_outputs = {
    cluster_id = "eks-cluster-dummy-id"
  }
  mock_outputs_allowed_terraform_commands = ["validate"]
}

include  {
  path = find_in_parent_folders()
}

inputs = {
  mle_ns = "ts-eks-ns"
  cluster_id = dependency.eks_cluster.outputs.cluster_id
}
