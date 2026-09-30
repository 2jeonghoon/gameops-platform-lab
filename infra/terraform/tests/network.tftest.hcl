mock_provider "aws" {}

run "network_and_cost_guardrails" {
  command = apply

  variables {
    budget_alert_email   = "operator@example.com"
    github_owner         = "example-owner"
    github_owner_id      = "12345678"
    github_repository    = "gameops-platform-lab"
    github_repository_id = "987654321"
  }

  assert {
    condition     = var.aws_region == "ap-northeast-2"
    error_message = "The lab must stay in ap-northeast-2."
  }

  assert {
    condition     = aws_vpc.main.cidr_block == "10.20.0.0/16"
    error_message = "The VPC CIDR must match the documented design."
  }

  assert {
    condition     = aws_subnet.public.cidr_block == "10.20.1.0/24" && aws_subnet.public.map_public_ip_on_launch
    error_message = "The public subnet must use 10.20.1.0/24 and assign public IPv4 addresses."
  }

  assert {
    condition     = aws_route.public_default.destination_cidr_block == "0.0.0.0/0" && aws_route.public_default.gateway_id == aws_internet_gateway.main.id
    error_message = "The public route table must send its default route to the Internet Gateway."
  }

  assert {
    condition     = length(local.public_ingress_rules) == 1 && local.public_ingress_rules[0].from_port == 80 && local.public_ingress_rules[0].to_port == 80
    error_message = "Exactly one public TCP ingress rule for port 80 is allowed."
  }

  assert {
    condition     = alltrue([for rule in local.public_ingress_rules : rule.from_port != 22 && rule.to_port != 22])
    error_message = "Public SSH ingress is forbidden."
  }

  assert {
    condition     = aws_budgets_budget.monthly.limit_amount == "15"
    error_message = "The monthly cost guardrail must be USD 15."
  }

  assert {
    condition     = toset(nonsensitive([for item in aws_budgets_budget.monthly.notification : tonumber(item.threshold)])) == toset([5, 10])
    error_message = "Budget notifications must fire at USD 5 and USD 10."
  }
}
