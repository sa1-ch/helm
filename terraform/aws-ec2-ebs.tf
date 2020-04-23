provider "aws" {
  profile    = "default"
  region     = "us-east-1"
}

resource "aws_key_pair" "tiger_tf_kp" {
  key_name   = "tiger-mle-tf-key"
  public_key = "ssh-rsa AAAAB3NzaC1yc2EAAAABJQAAAQEAmnD30IFt/NEv0f33PZ+xklkuaE0ZWt8uEyeAkJ+tOYbpkDBPNMsBp5FwGzsKQvmZLAn4vGrrawVkWyeugT35R5KVrCbmlenhicehA67MZtucgre80Wj4070Z2MlI+tljD57HRabJNuxoFUcL/qbGVMldy1go4VQASmVXB9M4M0Op5MLij2I7LCFdCFrBC71c7+0k/Y0bCwh894gpL6t9P7Qg7cXw/XcANGxPD/Du4i6WZPdMfQ65Cxgp8pS1xeAYfqBH0HPTfTtIMnafFsSS0oJpx1C0Yb8xsISzDfEAUVkzq8qp1nO6MePFCEbjpGG59V3O6HbFMrMJqqXY4T3Viw== rsa-key-20200423"
}

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





