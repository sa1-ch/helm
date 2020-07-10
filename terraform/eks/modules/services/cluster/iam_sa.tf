resource "aws_iam_openid_connect_provider" "eks_cluster_oidc" {
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [data.external.thumb.result.thumbprint]
  url             = "${aws_eks_cluster.tiger-mle-eks[0].identity.0.oidc.0.issuer}"
}

data "aws_caller_identity" "current" {}

data "external" "thumb" {
  program = ["${path.module}/get_thumbprint.sh",var.aws_region]
}

data "aws_iam_policy_document" "assume_role_policy" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    effect  = "Allow"

    condition {
      test     = "StringEquals"
      variable = "${replace(aws_iam_openid_connect_provider.eks_cluster_oidc.url, "https://", "")}:sub"
      values   = ["system:serviceaccount:${var.namespace}:${var.service_account_name}"]
    }

    principals {
      identifiers = ["${aws_iam_openid_connect_provider.eks_cluster_oidc.arn}"]
      type        = "Federated"
    }
  }
}

resource "aws_iam_role" "sa_iam_role" {
  assume_role_policy = "${data.aws_iam_policy_document.assume_role_policy.json}"
  name               = "sa_iam_role"
}

resource "aws_iam_role_policy_attachment" "sa_iam_policy_attach" {
  count = length(var.role_policy_arns) > 0 ? length(var.role_policy_arns) : 0

  role       = join("", aws_iam_role.sa_iam_role.*.name)
  policy_arn = var.role_policy_arns[count.index]
}
