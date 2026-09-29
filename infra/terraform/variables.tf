variable "aws_region" {
  description = "AWS region for every project resource."
  type        = string
  default     = "ap-northeast-2"

  validation {
    condition     = var.aws_region == "ap-northeast-2"
    error_message = "This costed lab is approved only for ap-northeast-2."
  }
}

variable "project_name" {
  description = "Stable project identifier used in names and tags."
  type        = string
  default     = "gameops-platform-lab"
}

variable "environment" {
  description = "Deployment environment tag."
  type        = string
  default     = "portfolio"
}

variable "budget_alert_email" {
  description = "Email address that receives USD 5 and USD 10 budget alerts."
  type        = string
  sensitive   = true

  validation {
    condition     = can(regex("^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$", var.budget_alert_email))
    error_message = "budget_alert_email must be a valid email address."
  }
}
