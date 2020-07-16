resource "aws_s3_bucket" "bucket" {
  bucket = var.bucket_name

  #Prevent accidental deletion of this S3 bucket
  lifecycle {
    prevent_destroy = false
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
  bucket = "${aws_s3_bucket.bucket.id}"

  block_public_acls   = var.block_public_acls
  block_public_policy = var.block_public_policy
  ignore_public_acls  = var.ignore_public_acls
  restrict_public_buckets = var.restrict_public_buckets
}

resource "aws_s3_bucket_object" "base_folder" {
    count   = length(var.named_folders)
    bucket  = aws_s3_bucket.bucket.id
    acl     = "private"
    key     =  "${var.named_folders[count.index]}/"
    content_type = "application/x-directory"
}
