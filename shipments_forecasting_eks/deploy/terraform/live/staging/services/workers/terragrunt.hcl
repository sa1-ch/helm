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
  aws_region = "us-east-1"
  worker_instance_profile_id = dependency.iam_role.outputs.worker_instance_profile_id
  worker_role_arn            = dependency.iam_role.outputs.worker_role_arn
  cluster_security_group_id  = dependency.eks_cluster.outputs.vpc_config[0].cluster_security_group_id
  subnets                    = dependency.eks_cluster.outputs.vpc_config[0].subnet_ids
  cluster_id                 = dependency.eks_cluster.outputs.cluster_id
  image_id                   = "ami-088bf1d873ea44a51"
  eks_cluster_name           = dependency.eks_cluster.outputs.cluster_id
  eks_cluster_endpoint       = dependency.eks_cluster.outputs.eks_endpoint
  eks_cluster_certificate    = dependency.eks_cluster.outputs.certificate_authority[0].data
  worker_groups_launch_template = [
    {
      name                    = "c5-4x-large-demand"
      override_instance_types = ["c5.4xlarge"]
      on_demand_base_capacity = 0
      on_demand_percentage_above_base_capacity = 100
      asg_max_size            = 20
      asg_desired_capacity    = 1
      asg_min_size            = 0
      kubelet_extra_args      = "--node-labels=nodegroup-name=c5-4x-large-demand,instance-type=onDemand,nodegroup-type=stateful-workload"
      public_ip               = false
      default_cooldown        = 60
    },
    {
      name                    = "c5-4x-large-spot"
      override_instance_types = ["c5.4xlarge"]
      on_demand_base_capacity = 0
      on_demand_percentage_above_base_capacity = 0
      asg_max_size            = 100
      asg_desired_capacity    = 1
      asg_min_size            = 0
      kubelet_extra_args      = "--node-labels=nodegroup-name=c5-4x-large-spot,instance-type=spot,nodegroup-type=stateless-workload"
      public_ip               = false
      default_cooldown        = 60
   },
   {
      name                    = "t3-2x-large-demand"
      override_instance_types = ["t3.2xlarge"]
      on_demand_base_capacity = 0
      on_demand_percentage_above_base_capacity = 100
      asg_max_size            = 5
      asg_desired_capacity    = 1
      asg_min_size            = 0
      kubelet_extra_args      = "--node-labels=nodegroup-name=app-demand,instance-type=onDemand,nodegroup-type=stateful-workload"
      public_ip               = false
      default_cooldown        = 60
    }
  ]

}
