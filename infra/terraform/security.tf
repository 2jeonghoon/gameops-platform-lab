resource "aws_security_group" "app" {
  name        = "${local.name_prefix}-app"
  description = "Public HTTP only; administration uses AWS Systems Manager"
  vpc_id      = aws_vpc.main.id

  tags = {
    Name = "${local.name_prefix}-app"
  }
}

resource "aws_vpc_security_group_ingress_rule" "public" {
  for_each = { for rule in local.public_ingress_rules : rule.description => rule }

  security_group_id = aws_security_group.app.id
  description       = each.value.description
  ip_protocol       = each.value.ip_protocol
  from_port         = each.value.from_port
  to_port           = each.value.to_port
  cidr_ipv4         = each.value.cidr_ipv4
}

resource "aws_vpc_security_group_egress_rule" "all_ipv4" {
  security_group_id = aws_security_group.app.id
  description       = "Outbound package, registry, and AWS API access"
  ip_protocol       = "-1"
  cidr_ipv4         = "0.0.0.0/0"
}
