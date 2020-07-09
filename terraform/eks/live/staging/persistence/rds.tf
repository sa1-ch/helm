module "dev_rds" {
  source = "../../../modules/persistence"
  engine = var.engine
  engine_version = var.engine_version
  instance_class = var.instance_class
  name = var.name
  username = var.username
  password = var.password
  port = var.port
  vpc_security_group_ids = [data.terraform_remote_state.eks_cluster.outputs.vpc_config[0].cluster_security_group_id]
  #db_subnet_group_name = var.db_subnet_group_name
  backup_window = var.backup_window
  maintenance_window = var.maintenance_window
  allocated_storage = var.allocated_storage
  identifier = var.identifier
  name_prefix = var.name_prefix
  subnet_ids = data.terraform_remote_state.vpc.outputs.persistence_private_subnet_id

}
