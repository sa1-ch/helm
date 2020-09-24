locals {
node_group_count = length(var.node_groups)
node_group_defaults = {
  name = "eks-node-group"
  desired_size = "1"
  max_size     = "2"
  min_size     = "1"
  ami_type     = "AL2_x86_64"
  disk_size    = "20"
  instance_types = ["t3.medium"]
  labels = {}
  tags = {}
  ec2_ssh_key = ""
  source_security_group_ids = []
}
}
