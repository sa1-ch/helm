terraform {
  backend "s3" {
    # Replace this with your bucket name
    #hardcoded since variables not allowed in terraform configurations. can use terragrunt
    bucket         = "mle-terraform-state"
    key            = "staging/eks/persistence/terraform.tfstate"
    region         = "us-east-1"

    # Replace this with your DynamoDB table name!
    dynamodb_table = "tf_state_lock_table"
    encrypt        = true
  }
}
