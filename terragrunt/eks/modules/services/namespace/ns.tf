resource "kubernetes_namespace" "mle-ns" {
  count = length(var.mle_ns)
  metadata {
    name = element(var.mle_ns, count.index)
  }
}

