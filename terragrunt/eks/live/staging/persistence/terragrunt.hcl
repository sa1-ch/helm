terraform {
  source = "${get_terragrunt_dir()}/../../../modules//persistence"
}

dependencies {
  paths = ["../networking","../services/cluster"]
}

dependency "vpc" {
  config_path = "../networking"

  mock_outputs = {
    persistence_private_subnet_id = ["dummy-1","dummy-2"]
  }
  mock_outputs_allowed_terraform_commands = ["validate"]
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
  mock_outputs_allowed_terraform_commands = ["validate"]
}

include  {
  path = find_in_parent_folders()
}

inputs = {
  engine = "postgres"
  engine_version = "11.6"
  instance_class = "db.t2.micro"
  name           = "shippinginstance"
  port           = "5432"
  username       = "postgres"
  password       = "Tiger123!"
  vpc_security_group_ids = [dependency.eks_cluster.outputs.vpc_config[0].cluster_security_group_id]
  backup_window          = "09:46-10:16"
  maintenance_window     = "Mon:00:00-Mon:03:00"
  allocated_storage      = 20
  identifier             = "shipment"
  name_prefix            = "shipping"
  subnet_ids             = dependency.vpc.outputs.persistence_private_subnet_id
}
