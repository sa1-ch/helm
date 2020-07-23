remote_state {
  backend = "s3" 
  config = {
    # Replace this with your bucket name!
    # Cant use variables in terraform config since hardcoded
    bucket         = "mle-terraform-state"
    key            = "terragrunt/${path_relative_to_include()}/terraform.tfstate"
    region         = "us-east-1"

    # Replace this with your DynamoDB table name!
    dynamodb_table = "tf_state_lock_table"
    encrypt        = true
  }
}
