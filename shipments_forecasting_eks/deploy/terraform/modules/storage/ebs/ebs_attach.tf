resource "aws_volume_attachment" "tiger-mle-att" {
  device_name = var.ebs_device_name
  volume_id   = "${aws_ebs_volume.tiger-mle-ebs.id}"
  instance_id = data.terraform_remote_state.instance.outputs.ec2_instance_id
}
 
