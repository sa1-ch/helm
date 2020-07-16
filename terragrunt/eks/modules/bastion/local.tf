locals {
  sg_defaults = {
    type = "ingress"
    from_port = 22
    to_port   = 22
    protocol  = "ssh"
    cidr_blocks = "182.75.175.34"
  }
}
