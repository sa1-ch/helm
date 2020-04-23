provider "aws" {
  profile    = "default"
  region     = "us-east-1"
}

resource "aws_key_pair" "tiger_tf_kp" {
  key_name   = "tiger-mle-tf-key"
  public_key = "<ssh key>"}

resource "aws_instance" "tiger_mle_tf_ec2" {
  ami           = "ami-0323c3dd2da7fb37d"
  instance_type = "t2.micro"
  key_name = "${aws_key_pair.tiger_tf_kp.key_name}"
  
  tags = {
    Name = "tiger-mle-tf-ec2"
  }
}

resource "aws_ebs_volume" "tiger_mle_tf_ebs" {
  availability_zone = "us-east-1a"
  size              = 8
  type              = "standard"
  tags = {
    Name = "mle-terraform-ebs"
  }
}

resource "aws_volume_attachment" "ec2_ebs_att" {
  device_name = "/dev/sdh"
  volume_id   = "${aws_ebs_volume.tiger_mle_tf_ebs.id}"
  instance_id = "${aws_instance.tiger_mle_tf_ec2.id}"
}





