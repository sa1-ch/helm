 output "blob_endpoint" {
    value = azurerm_storage_account.mystorageaccount.primary_blob_endpoint
    description = "blob endpoint"
    }