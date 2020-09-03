resource "kubernetes_service_account" "mle-sa" {
  metadata {
    name = var.mle_sa
    annotations = {
      "eks.amazonaws.com/role-arn" = "${var.sa_iam_role}"
    }
    namespace = var.mle_ns
  }

  secret {
    name = "${kubernetes_secret.mle-sa-secret.metadata.0.name}"
  }
  automount_service_account_token = var.automount_service_account_token
}

resource "kubernetes_secret" "mle-sa-secret" {
  metadata {
    name = var.mle_sa_secret
  }
}
