locals {
  sg_defaults = {
    type = "ingress"
    from_port = 22
    to_port   = 22
    protocol  = "ssh"
    cidr_blocks = "182.75.175.34"
  }
  ec2_principal = "ec2.${data.aws_partition.current.dns_suffix}"
  policy_arn_prefix = "arn:${data.aws_partition.current.partition}:iam::aws:policy"

}
