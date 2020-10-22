terraform {
  source = "${get_terragrunt_dir()}/../../../modules//networking"
}

include  {
  path = find_in_parent_folders()
}

inputs = {
allocation_method =  "Dynamic" 
  address_space =  "10.0.0.0/16"
  priority =  1000 
  direction =  "Inbound" 
  access =  "Allow" 
  protocol =  "Tcp" 
  destination_port_range =  "22"
  }