data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  filter {
    name   = "root-device-type"
    values = ["ebs"]
  }
}

resource "aws_instance" "k3s" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = "t3.medium"
  subnet_id                   = aws_subnet.public.id
  vpc_security_group_ids      = [aws_security_group.app.id]
  associate_public_ip_address = true
  iam_instance_profile        = aws_iam_instance_profile.k3s.name
  key_name                    = local.ssh_key_name
  user_data_replace_on_change = true
  user_data = templatefile("${path.module}/templates/cloud-init.yaml.tftpl", {
    k3s_version  = "v1.37.0+k3s1"
    helm_version = "v4.3.0"
  })

  metadata_options {
    http_endpoint = "enabled"
    http_tokens   = "required"
  }

  root_block_device {
    encrypted   = true
    volume_size = 20
    volume_type = "gp3"
  }

  tags = {
    Name = "${local.name_prefix}-k3s"
    Role = "k3s-server"
  }

  depends_on = [aws_iam_role_policy_attachment.ssm_core]
}
