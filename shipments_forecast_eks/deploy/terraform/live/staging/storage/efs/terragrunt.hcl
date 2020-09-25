terraform {
  source = "${get_terragrunt_dir()}/../../../../modules/storage//efs"
}

dependencies {
  paths = ["../../networking","../../services/cluster"]
}

dependency "vpc" {
  config_path = "../../networking"
  mock_outputs = {
    private_subnet_id = ["dummy-1","dummy-2"]
  }
  mock_outputs_allowed_terraform_commands = ["validate","plan"]
}

dependency "eks_cluster" {
  config_path = "../../services/cluster"

  mock_outputs = {
    vpc_config = [
      {
        cluster_security_group_id = "dummy"
      }
    ]
  }
  
  mock_outputs_allowed_terraform_commands = ["validate"]
}

include  {
  path = find_in_parent_folders()
}


inputs = {
  tags = {}
  security_groups = [dependency.eks_cluster.outputs.vpc_config[0].cluster_security_group_id]
  subnets         = dependency.vpc.outputs.private_subnet_id
  
}
