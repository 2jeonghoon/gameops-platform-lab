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
