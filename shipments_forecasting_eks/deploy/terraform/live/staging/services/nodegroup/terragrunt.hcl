terraform {
  source = "${get_terragrunt_dir()}/../../../../modules/services//nodegroup"
}

dependencies {
  paths = ["../../networking","../cluster"]
}

dependency "vpc" {
  config_path = "../../networking"

  mock_outputs = {
    private_subnet_id = ["dummy-1","dummy-2"]
  }
}

dependency "eks_cluster" {
  config_path = "../cluster"
  
  mock_outputs = {
    cluster_version = "1.15"
    cluster_id      = "dummy-cluster-id"
  }
}

include  {
  path = find_in_parent_folders()
}

inputs = {
  aws_region = "us-east-1"
  cluster_name = dependency.eks_cluster.outputs.cluster_id
  cluster_version = dependency.eks_cluster.outputs.cluster_version
  subnet_ids      = dependency.vpc.outputs.private_subnet_id
  node_groups = [
    {
      name    =  "tiger-mle-t2-demand"
      desired_size = 1
      max_size =  5
      min_size = 1
      ami_type = "AL2_x86_64"
      disk_size = 20
      instance_types = ["t2.2xlarge"]
      labels = {
        "nodegroup-type" = "stateful-workload"
        "instance-type"  = "onDemand"
        "nodegroup-name" = "app-demand"
      }

      tags = {
        "k8s.io/cluster-autoscaler/${dependency.eks_cluster.outputs.cluster_id}" = "owned"
        "k8s.io/cluster-autoscaler/enabled" = "true"
        "Name" = "tiger-mle-on-demand"
      }

      ec2_ssh_key = "tiger-mle-ec2-keys"
      #source_security_group_ids = ["sg-0abec7954d9dc5f3e"]
    }


  ]
  eks_ng_role = "tiger-mle-tg-ng-role"
}
