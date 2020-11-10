module "dev_vm"{
    source = "../../../modules/vm"
    algorithm =   var.algorithm   
    rsa_bits =   var.rsa_bits  
    size                  =   var.size      
    caching           =   var.caching   
    storage_account_type =   var.storage_account_type   
    publisher =   var.publisher   
    offer     =   var.offer   
    sku       =   var.sku 
    computer_name  =   var.computer_name      
    disable_password_authentication =   var.disable_password_authentication   
}