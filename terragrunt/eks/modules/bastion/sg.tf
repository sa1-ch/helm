resource "aws_security_group" "bastion_sg" {
  name = var.name
  vpc_id = var.vpc_id

  tags = {
    Name = var.name_tag
  }
}

resource "aws_security_group_rule" "bastion_sg_rule" {
  count = length(var.sg_rules)
  type              = lookup(var.sg_rules[count.index], "type", local.sg_defaults["type"])
  from_port         = lookup(var.sg_rules[count.index], "from_port", local.sg_defaults["from_port"])
  to_port           = lookup(var.sg_rules[count.index], "to_port", local.sg_defaults["to_port"])
  protocol          = lookup(var.sg_rules[count.index], "protocol", local.sg_defaults["protocol"])
  cidr_blocks       = [lookup(var.sg_rules[count.index], "cidr_blocks", local.sg_defaults["cidr_blocks"])]
  security_group_id = aws_security_group.bastion_sg.id
}

resource "aws_security_group_rule" "cluster_bastion_sg_rule" {
  type                     = "ingress"
  from_port                = var.bastion_from_port
  to_port                  = var.bastion_to_port
  protocol                 = var.bastion_protocol
  source_security_group_id = aws_security_group.bastion_sg.id
  security_group_id = var.cluster_sg
}
