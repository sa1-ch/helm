variable "aws_region" {
  description = "aws region"
  default = "us-east-1"
  type = string
}

variable "vpc_cidr_block" {
  description = "cidr block for vpc"
  default = "10.0.0.0/16"
  type = string
}

variable "resource_tag" {
  description = "tags to idemtify resources"
  default = "tiger-mle"
  type = string
}

variable "subnet_cidr_block" {
  description = "ip address range for subnet"
  default = "10.0.1.0/24"
  type = string
}

variable "route_table_dest_cidr" {
  description = "destination ip address for vpc route table"
  default = "0.0.0.0/0"
  type = string
}

variable "sg_name" {
  description = "secuirty group name"
  default = "tiger-mle-sg"
  type = string
}

variable "ingress_ip" {
  description = "ips for ingress"
  default = ["182.75.175.34/32","1.22.172.58/32"]
  type = list(string)
}

variable "sg_tcp_from_port" {
  description = "security group inbound port"
  default = 8080
  type = number
}

variable "sg_tcp_to_port" {
  description = "security group inbound port"
  default = 8085
  type = number
}

variable "ssh_port" {
  description = "port for ssh connection"
  default = 22
  type = number
}
