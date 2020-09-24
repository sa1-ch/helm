resource "aws_iam_role" "eks_ng_role" {
  name = var.eks_ng_role
  assume_role_policy = <<POLICY
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
POLICY
}


resource "aws_iam_role_policy_attachment" "eks_autoscale_policy" {
  policy_arn = "arn:aws:iam::171774164293:policy/eks-cluster-autoscale"
  role = aws_iam_role.eks_ng_role.name
}

resource "aws_iam_role_policy_attachment" "eks_wn_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
  role = aws_iam_role.eks_ng_role.name
}

resource "aws_iam_role_policy_attachment" "eks_cni_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
  role = aws_iam_role.eks_ng_role.name
}

resource "aws_iam_role_policy_attachment" "eks_ec2_ecs_readonly" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
  role = aws_iam_role.eks_ng_role.name
}
