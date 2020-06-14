terraform {
  backend "s3" {
    # Replace this with your bucket name!
    # Cant use variables in terraform config since hardcoded
    bucket         = "mle-terraform-state"
    key            = "prod/compute/terraform.tfstate"
    region         = "us-east-1"

    # Replace this with your DynamoDB table name!
    dynamodb_table = "tf_state_lock_table"
    encrypt        = true
  }
}
