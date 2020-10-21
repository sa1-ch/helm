module "dev_vpc" {
  #evnetually, this will git versioned
  source = "../../../modules/networking"
  # setting vpc inputs 
  allocation_method =  var.allocation_method 
  address_space =  var.address_space
  priority =  var.priority 
  direction =  var.direction 
  access =  var.access 
  protocol =  var.protocol 
  destination_port_range =  var.destination_port_range
}