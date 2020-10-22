# built-in function get_terragrunt_dir() returns the path of parent terragrunt.hcl file
# double slash (//) indicates the location of modules terragrunt copies them as is to temp cache location & ensures the relative paths between modules work correctly
terraform {
  source = "${get_terragrunt_dir()}/../../../modules//resource_group"
}

include {
  path = find_in_parent_folders()
}
