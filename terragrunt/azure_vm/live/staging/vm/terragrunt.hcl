# built-in function get_terragrunt_dir() returns the path of parent terragrunt.hcl file
# double slash (//) indicates the location of modules & terragrunt copies them as is to temp cache location & ensures the relative paths between modules work correctly
terraform {
  source = "${get_terragrunt_dir()}/../../../modules//vm"
}

# includes all settings from the root terragrunt.hcl file
# built-in function find_in_parent_folders() returns the absolute path of the parent terragrunt.hcl file
include {
  path = find_in_parent_folders()
}


inputs = {
  algorithm =   "RSA"   
  rsa_bits =   4096  
  size                  =   "Standard_DS1_v2"      
  caching           =   "ReadWrite"   
  storage_account_type =   "Premium_LRS"   
  publisher =   "Canonical"   
  offer     =   "UbuntuServer"   
  sku       =   "18.04-LTS" 
  computer_name  =   "myvm"      
  disable_password_authentication = true
}