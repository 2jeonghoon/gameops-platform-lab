locals {
  name_prefix  = "${var.project_name}-${var.environment}"
  ssh_key_name = null

  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
  }

  public_ingress_rules = [
    {
      description = "Public HTTP entry point"
      ip_protocol = "tcp"
      from_port   = 80
      to_port     = 80
      cidr_ipv4   = "0.0.0.0/0"
    }
  ]
}
