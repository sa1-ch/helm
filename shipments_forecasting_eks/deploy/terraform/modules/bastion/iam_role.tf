resource "aws_iam_role" "bastion" {
  name          = var.role_name
  assume_role_policy    = data.aws_iam_policy_document.workers_assume_role_policy.json
  permissions_boundary  = var.permissions_boundary
  path                  = var.iam_role_path
  force_detach_policies = true
  tags                  = var.iam_role_tags
}

resource "aws_iam_instance_profile" "bation" {
  name_prefix = var.instance_profile_name_prefix
  role = aws_iam_role.bastion.name
  path = var.instance_profile_path
}

resource "aws_iam_role_policy_attachment" "bastion_policy_attachement" {
  count      = length(var.policies)
  policy_arn = "${local.policy_arn_prefix}/${var.policies[count.index]}"
  role       = aws_iam_role.bastion.name
}
