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

variable "private_subnet_cidr_block" {
  description = "ip address range for subnet"
  default = "10.0.0.0/17"
  type = string
}

variable "public_subnet_cidr_block" {
  description = "ip address range for subnet"
  default = "10.0.128.0/17"
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

variable "azs" {
  description = "availability zone in aws region"
  default     = ["us-east-1a","us-east-1b"]
  type = list
}

variable "private_subnet_tag" {
  description = "name tag for private subnet"
  default = "mle-eks-private-subnet"
  type = string
}

variable "private_persistence_subnet_tag" {
  description = "name tag for private subnet"
  default = "persistence private subnet"
  type = string
}


variable "public_subnet_tag" {
  description = "name tag for public subnet"
  default = "mle-eks-public-subnet"
  type = string
}

variable "route_table_private_tag" {
  description = "name for private subnet route table"
  default = "mle-eks-private-subnet-rt"
  type =  string
}

variable "route_table_public_tag" {
  description = "name for private subnet route table"
  default = "mle-eks-public-subnet-rt"
  type =  string
}

variable "ig_resource_tag" {
  description = "name for internet gateway"
  default = "mle-eks-ig"
  type = string
}

variable "nat_resource_tag" {
  description = "name for nat gateway"
  default = "mle-eks-nat"
  type = string
}

variable "private_subnets" {
  description = "private cidr"
  default = ["10.0.0.0/20", "10.0.16.0/20"]
  type = list
}

variable "private_persistence_subnets" {
  description = "private cidr"
  default = ["10.0.32.0/20","10.0.48.0/20"]
  type = list
}

variable "public_subnets" {
  description = "public cidr"
  default = ["10.0.64.0/20", "10.0.80.0/20"]
  type = list

}

variable "eks_cluster_name" {
  description = "cluster name"
  default = "tiger-mle-eks"
  type = string
}

