remote_state {
  backend = "azurerm" 
  config = {
    resource_group_name  = "tg_BackendResourceGroup"
    storage_account_name = "tatgazterraformstate"
    container_name       = "tftgstate"
    key                  = "terragrunt/${path_relative_to_include()}/terraform.tfstate"
  }
}