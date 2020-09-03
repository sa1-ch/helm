resource "aws_iam_role" "tiger-mle-eks-role" {
  name = var.eks_role
  assume_role_policy = <<POLICY
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "eks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
POLICY
}

resource "aws_iam_role" "tiger-mle-s3-role" {
  name = var.s3_role
  assume_role_policy = <<POLICY
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "s3.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    },
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "s3.amazonaws.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity"
    }

  ]

}
POLICY
}

resource "aws_iam_instance_profile" "worker_instance_profile" {
  name = var.worker_instance_profile
  role = "${aws_iam_role.tiger-mle-worker-role.name}"
}

resource "aws_iam_role" "tiger-mle-worker-role" {
  name = var.worker_role
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

resource "aws_iam_policy" "eks_autoscale_policy" {
  name = var.eks_autoscale_policy
  description = "iam ploicy for worker node to autoscale"
  policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "autoscaling:DescribeAutoScalingGroups",
                "autoscaling:DescribeAutoScalingInstances",
                "autoscaling:DescribeLaunchConfigurations",
                "autoscaling:DescribeTags",
                "autoscaling:SetDesiredCapacity",
                "autoscaling:TerminateInstanceInAutoScalingGroup"
            ],
            "Resource": "*"
        }
    ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "eks_autoscale_policy" {
  policy_arn = aws_iam_policy.eks_autoscale_policy.arn
  role = aws_iam_role.tiger-mle-worker-role.name
}
resource "aws_iam_role_policy_attachment" "s3_policy" {
  policy_arn = "arn:aws:iam::171774164293:policy/read-write-playground-s3-bucket"
  role = aws_iam_role.tiger-mle-s3-role.name
}

resource "aws_iam_role_policy_attachment" "eks_cluster_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
  role = aws_iam_role.tiger-mle-eks-role.name
}

resource "aws_iam_role_policy_attachment" "eks_service_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSServicePolicy"
  role = aws_iam_role.tiger-mle-eks-role.name
}
resource "aws_iam_role_policy_attachment" "workers_AmazonEKSWorkerNodePolicy" {
  #count      = var.manage_worker_iam_resources && var.create_eks ? 1 : 0
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
  role       = aws_iam_role.tiger-mle-worker-role.name
}

resource "aws_iam_role_policy_attachment" "workers_AmazonEKS_CNI_Policy" {
  #count      = var.manage_worker_iam_resources && var.attach_worker_cni_policy && var.create_eks ? 1 : 0
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
  role       = aws_iam_role.tiger-mle-worker-role.name
}

resource "aws_iam_role_policy_attachment" "workers_AmazonEC2ContainerRegistryReadOnly" {
  #count      = var.manage_worker_iam_resources && var.create_eks ? 1 : 0
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
  role       = aws_iam_role.tiger-mle-worker-role.name
}
