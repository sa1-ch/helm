resource "aws_security_group" "tiger-mle-sg" {
  name = var.sg_name
  vpc_id = aws_vpc.tiger-mle-vpc.id
 ingress {
   from_port = var.sg_tcp_from_port
   to_port = var.sg_tcp_to_port
   protocol = var.sg_protocol
   cidr_blocks = var.ingress_ip

 }
 ingress {
   from_port = var.ssh_port
   to_port = var.ssh_port
   protocol = var.sg_protocol
   cidr_blocks = var.ingress_ip

 }

}
