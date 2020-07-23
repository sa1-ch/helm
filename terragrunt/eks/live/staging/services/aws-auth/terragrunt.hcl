terraform {
  source = "${get_terragrunt_dir()}/../../../../modules/services//aws-auth"
}

dependencies {
  paths= ["../../bastion","../../iam"]
}

dependency "iam_role" {
  config_path = "../../iam"
}

dependency "bastion" {
  config_path = "../../bastion"
}

include  {
  path = find_in_parent_folders()
}


inputs = {
  aws_region = "us-east-1"
  worker_template_roles_arn = [dependency.iam_role.outputs.worker_role_arn]
  bastion_role_arn                  = [dependency.bastion.outputs.bastion_role_arn]

}
