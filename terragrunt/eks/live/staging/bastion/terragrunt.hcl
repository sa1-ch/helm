terraform {
  source = "${get_terragrunt_dir()}/../../../modules//bastion"
}

dependencies {
  paths = ["../networking","../services/cluster"]
}

dependency "vpc" {
  config_path = "../networking"
  mock_outputs = {
    vpc_id = "vpc-dummy-id"
  }
}

dependency "eks_cluster" {
  config_path = "../services/cluster"
  mock_outputs = {
    vpc_config = [
                   {
                     cluster_security_group_id = "dummy"
                   }
    ]
  }  
}

include  {
  path = find_in_parent_folders()
}

inputs = {
  name = "bastion-sg"
  aws_region = "us-east-1"
  ec2_instance_type = "t3.medium"
  vpc_id  = dependency.vpc.outputs.vpc_id
  name_tag = "mle-bastion-host-sg"
  subnet_id = dependency.vpc.outputs.public_subnet_id[0]
  bastion_from_port = 0
  bastion_to_port   = 65543
  bastion_protocol  = "-1"
  cluster_sg        = dependency.eks_cluster.outputs.vpc_config[0].cluster_security_group_id
  ebs_volume_size = 50
  storage_tag     = "tiger-mle"
  ebs_device_name = "/dev/sdh"
  role_name_prefix = "bastion-role-"
  role_name        = "bastion-iam-role"
  instance_profile_name_prefix = "bastion-instance-profile"
  policies = ["AmazonEKSWorkerNodePolicy","AmazonEKS_CNI_Policy","AmazonEC2ContainerRegistryReadOnly","AmazonS3FullAccess"]
  sg_rules = [
               {
                 type = "ingress"
                 from_port = 22
                 to_port   = 22
                 protocol  = "tcp"
                 cidr_blocks = "182.75.175.34/32"
               },
               {
                 type = "ingress"
                 from_port = 22
                 to_port   = 22
                 protocol  = "tcp"
                 cidr_blocks = "1.22.172.58/32"
               },
               {
                 type = "egress"
                 from_port = 0
                 to_port   = 65535
                 protocol  = "TCP"
                 cidr_blocks = "0.0.0.0/0"
               },
               {
                 type = "egress"
                 from_port = 0
                 to_port   = 65535
                 protocol  = "-1"
                 cidr_blocks = dependency.vpc.outputs.cidr_block
               }
             ]
}
