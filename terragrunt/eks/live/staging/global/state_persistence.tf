resource "aws_s3_bucket" "terraform_state" {
  bucket = var.state_bucket
  
  #Prevent accidental deletion of this S3 bucket
  lifecycle {
    prevent_destroy = true
  }
  
  # Enable versioning so we can see the full revision history of our
  # state files
  
  versioning {
    enabled = true
  }

  # Enable server-side encryption by default
  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = var.sse_algorithm
      }
    }
  }
  
  
}

resource "aws_s3_bucket_public_access_block" "public_block" {
  bucket = "${aws_s3_bucket.terraform_state.id}"

  block_public_acls   = true
  block_public_policy = true
  ignore_public_acls  = true
  restrict_public_buckets = true
}

resource "aws_dynamodb_table" "mle_terraform_locks" {
  name         = var.tf_state_lock_table
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = var.lock_hask_key

  attribute {
    name = var.lock_hask_key
    type = "S"
  }
}
