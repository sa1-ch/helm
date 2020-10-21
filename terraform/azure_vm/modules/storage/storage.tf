resource "random_id" "randomId" {
    keepers = {
        # Generate a new ID only when a new resource group is defined
        resource_group_name          =  data.terraform_remote_state.resource_group.outputs.resource_group_name 
    }

    byte_length = 8
}

# Create storage account for boot diagnostics
resource "azurerm_storage_account" "mystorageaccount" {
    name                        = "diag${random_id.randomId.hex}" 
    location                     =  data.terraform_remote_state.resource_group.outputs.location
    resource_group_name          =  data.terraform_remote_state.resource_group.outputs.resource_group_name 
    account_tier                =  var.account_tier 
    account_replication_type    =  var.account_replication_type 

    tags = {
        environment = "Terraform Demo"
    }
}
