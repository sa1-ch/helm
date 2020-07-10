module "mle_sa" {
  source = "../../../../modules/services/sa"
  mle_sa = var.mle_sa
  mle_sa_secret = var.mle_sa_secret
  

}
