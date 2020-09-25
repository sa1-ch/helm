resource "kubernetes_namespace" "mle-ns" {
  metadata {
    name = var.mle_ns
  }
}
