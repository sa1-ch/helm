terraform {
  backend "s3" {
    # Replace this with your bucket name!
    bucket         = "mle-terraform-state"
    key            = "dev/terraform.tfstate"
    region         = "us-east-1"

    # Replace this with your DynamoDB table name!
    dynamodb_table = "tf_state_lock_table"
    encrypt        = true
  }
}
