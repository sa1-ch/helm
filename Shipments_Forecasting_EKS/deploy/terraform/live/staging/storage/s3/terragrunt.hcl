terraform {
  source = "${get_terragrunt_dir()}/../../../../modules/storage//s3"
}

include  {
  path = find_in_parent_folders()
}

inputs = {
  aws_region = "us-east-1"
  bucket_name = "tiger-mle-tg"
  prevent_destroy =  false
  versioned       = true
  sse_algorithm   = "AES256"
  block_public_acls = true
  block_public_policy = true
  named_folders        = ["airflow/dags","airflow/logs","mlflow/mlflow-artifacts"]
  ignore_public_acls   = true
  restrict_public_buckets = true
}
