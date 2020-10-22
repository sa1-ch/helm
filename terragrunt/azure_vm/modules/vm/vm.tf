resource "tls_private_key" "example_ssh" {
  algorithm =  var.algorithm 
  rsa_bits = var.rsa_bits
}
output "tls_private_key" { value = tls_private_key.example_ssh.private_key_pem }

# Create virtual machine
resource "azurerm_linux_virtual_machine" "myterraformvm" {
    name                  =  var.vm_name 
    location                     =  data.terraform_remote_state.resource_group.outputs.location
    resource_group_name          =  data.terraform_remote_state.resource_group.outputs.resource_group_name 
    network_interface_ids                    =  [data.terraform_remote_state.vpc.outputs.nic_id]

    size                  =  var.size 

    os_disk {
        name              =  var.disk_name 
        caching           =  var.caching 
        storage_account_type =  var.storage_account_type 
    }

    source_image_reference {
        publisher =  var.publisher 
        offer     =  var.offer 
        sku       =  var.sku 
        version   =  "latest" 
    }

    computer_name  =  var.computer_name 
    admin_username =  var.user_name 
    disable_password_authentication = var.disable_password_authentication

    admin_ssh_key {
        username       =  var.user_name 
        public_key     = tls_private_key.example_ssh.public_key_openssh
    }

    boot_diagnostics {
        storage_account_uri =  data.terraform_remote_state.storage.outputs.blob_endpoint
    }

    tags = {
        environment = "Terraform Demo"
    }
}