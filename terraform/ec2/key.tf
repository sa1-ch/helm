resource "aws_key_pair" "tiger-mle-key" {
  key_name   = "tiger-mle-ec2-key"
  public_key = "<public_key>"
}
