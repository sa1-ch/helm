variable "vn_name" {
    description = "name for the virtual network"
    default = "myVnet"
    type = string
}

variable "address_space" {
  description = "IP for virtual network"
  default = "10.0.0.0/16"
  type = string
}

variable "subnet_name" {
  description = " name for the subnet"
  default = "mySubnet"
  type = string
}

variable "subnet_ip" {
  description = " IP for the subnet"
  default = "10.0.2.0/24"
  type = string
}

variable "ip_name"{
   description = "IP address"
   type = string
   default = "myPublicIP"
} 

variable "allocation_method" {
  description = "allocation_method for IP"
  type = string
  default = "Dynamic"
}

variable "nsg_name" {
  description = "name for Network Security Group"
  type = string
  default = "myNetworkSecurityGroup"
}

variable "security_rule_name" {
  description = "security_rule_name for Network Security Group"
  type = string
  default = "SSH"
}

variable "priority" {
  description = "priority for NSG"
  type = number
  default = 1000
}

variable "direction" {
  description = "direction for NSG"
  type = string
  default = "Inbound"
}

variable "protocol" {
  description = "protocol for NSG"
  type = string
  default = "Tcp"
}

variable "destination_port_range" {
  description = "destination_port_range for NSG"
  type = string
  default = "22"
}

variable "access" {
  description = "access for NSG"
  type = string
  default = "Allow"
}

variable nic_ip_config_name {
  type        = string
  default     = "myNicConfiguration"
  description = "name for IP config"
}

variable nic_name {
  type        = string
  default     = "myNIC"
  description = "name for NIC"
}

