data "aws_caller_identity" "current" {
}

locals {
  auth_launch_template_worker_roles = var.worker_template_roles_arn
  auth_worker_roles                 = var.worker_role_arn
  bastion_role_arn                  = var.bastion_role_arn

  # Convert to format needed by aws-auth ConfigMap
  configmap_roles = concat([
    for role in concat(
      local.auth_launch_template_worker_roles,
      local.auth_worker_roles,
	  
    ) :
    {
      rolearn  = role
      username = "system:node:{{EC2PrivateDNSName}}"
      groups = [
          "system:bootstrappers",
          "system:nodes",
        ]
	
    }
  ],
  [
    for role in local.bastion_role_arn:
    {
      rolearn  = role
      username = "system:node:{{EC2PrivateDNSName}}"
      groups = [
          "system:masters",
      ]
    }
])
    
}

resource "kubernetes_config_map" "aws_auth" {
  count      = var.manage_aws_auth ? 1 : 0

  metadata {
    name      = "aws-auth"
    namespace = "kube-system"
  }

  data = {
    mapRoles = yamlencode(
      distinct(concat(
        local.configmap_roles,
        var.map_roles,
      ))
    )
    mapUsers    = yamlencode(var.map_users)
    mapAccounts = yamlencode(var.map_accounts)
  }
}
