module "dev_nodegroup" {
  source = "../../../../modules/services/nodegroup"

  state_bucket = var.state_bucket
  eks_cluster_state_key = var.eks_cluster_state_key
  aws_region = var.aws_region
  vpc_state_key = var.vpc_state_key
  node_groups = [
    {
      name    =  "mle-shipping-forecast-ng-1"
      desired_size = 1
      max_size =  5
      min_size = 1
      ami_type = var.eks_ng_ami_type
      disk_size = 20
      instance_types = ["t2.2xlarge"]
      labels = {
        "nodegroup-type" = "stateful-workload"
        "instance-type"  = "onDemand"
        "nodegroup-name" = "app-demand"
      }

      tags = {
        "k8s.io/cluster-autoscaler/${data.terraform_remote_state.eks_cluster.outputs.cluster_id}" = "owned"
        "k8s.io/cluster-autoscaler/enabled" = "true"
        "Name" = "mle-shipping-on-demand"
      }

      ec2_ssh_key = "tiger-mle-ec2-keys"
      #source_security_group_ids = ["sg-0abec7954d9dc5f3e"]
    },
     {
      name    =  "mle-shipping-forecast-ng-2"
      desired_size = 1
      max_size =  100
      min_size = 1
      ami_type = var.eks_ng_ami_type
      disk_size = 20
      instance_types = ["c5.4xlarge"]
      labels = {
        "nodegroup-type" = "stateful-workload"
        "instance-type"  = "onDemand"
        "nodegroup-name" = "c5-4x-large-demand"
      }

      tags = {
        "k8s.io/cluster-autoscaler/${data.terraform_remote_state.eks_cluster.outputs.cluster_id}" = "owned"
        "k8s.io/cluster-autoscaler/enabled" = "true"
        "Name" = "mle-shipping-on-demand-c5"
      }
      ec2_ssh_key = "tiger-mle-ec2-keys"
      #source_security_group_ids = ["sg-0abec7954d9dc5f3e"]
    }


  ]
  eks_ng_role = var.eks_ng_role

}
