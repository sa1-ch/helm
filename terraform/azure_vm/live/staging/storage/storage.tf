module "dev_storage" { 
    source = "../../../modules/storage"
    account_tier                =   var.account_tier  
    account_replication_type    =   var.account_replication_type  
}