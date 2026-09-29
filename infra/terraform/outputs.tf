output "vpc_id" {
  description = "ID of the project VPC."
  value       = aws_vpc.main.id
}

output "public_subnet_id" {
  description = "ID of the single public subnet."
  value       = aws_subnet.public.id
}

output "app_security_group_id" {
  description = "ID of the HTTP-only application security group."
  value       = aws_security_group.app.id
}

output "instance_id" {
  description = "ID of the single k3s EC2 instance."
  value       = aws_instance.k3s.id
}

output "public_ipv4" {
  description = "Ephemeral public IPv4 address used for HTTP access."
  value       = aws_instance.k3s.public_ip
}

output "github_deploy_role_arn" {
  description = "Role assumed by GitHub Actions after OIDC verification."
  value       = aws_iam_role.github_deploy.arn
}
