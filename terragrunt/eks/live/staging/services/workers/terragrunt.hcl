terraform {
  source = "${get_terragrunt_dir()}/../../../../modules/services//workers"
}

dependencies {
  paths = ["../../networking","../../iam","../cluster"]
}
dependency "vpc" {
  config_path = "../../networking"
  
}

dependency "iam_role" {
  config_path = "../../iam"
  
  mock_outputs = {
    worker_instance_profile_id = "worker_instance_profile_id"
  }

  mock_outputs_allowed_terraform_commands = ["validate","plan"]
}

dependency "eks_cluster" {
  config_path = "../cluster"

  mock_outputs = {
    cluster_id = "cluster_id"
    vpc_config = [
                   {
                     cluster_security_group_id = "dummy"
                     subnet_ids = ["dummy-1","dummy-2"]
                   }
    ]
  }
  mock_outputs_allowed_terraform_commands = ["validate"]

}

include  {
  path = find_in_parent_folders()
}


inputs = {
  worker_instance_profile_id = dependency.iam_role.outputs.worker_instance_profile_id
  cluster_security_group_id  = dependency.eks_cluster.outputs.vpc_config[0].cluster_security_group_id
  subnet_ids                 = dependency.eks_cluster.outputs.vpc_config[0].subnet_ids
  cluster_id                 = dependency.eks_cluster.outputs.cluster_id
  image_id = "ami-088bf1d873ea44a51"
  worker_groups = [
    {
      name                                     = "mle-shipping-forecast-asg-1"
      instance_name                            = "mle-shipping-forecast-ondemand-instances"
      instance_type                            = "c5.4xlarge"
      desired_capacity                         = 1
      min_size                                 = 0
      max_size                                 = 120
      on_demand_base_capacity                  = 0
      on_demand_percentage_above_base_capacity = 100
    }

  ]

}
