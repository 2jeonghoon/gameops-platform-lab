mock_provider "aws" {}

run "github_oidc_and_least_privilege" {
  command = apply

  variables {
    budget_alert_email   = "operator@example.com"
    github_owner         = "example-owner"
    github_owner_id      = "12345678"
    github_repository    = "gameops-platform-lab"
    github_repository_id = "987654321"
  }

  assert {
    condition     = toset(aws_iam_openid_connect_provider.github.client_id_list) == toset(["sts.amazonaws.com"])
    error_message = "GitHub OIDC must use the AWS STS audience."
  }

  assert {
    condition     = strcontains(aws_iam_role.github_deploy.assume_role_policy, "repo:example-owner@12345678/gameops-platform-lab@987654321:ref:refs/heads/main")
    error_message = "Only the immutable repository identity on main may assume the deploy role."
  }

  assert {
    condition = toset(flatten([
      for statement in jsondecode(aws_iam_role_policy.github_deploy.policy).Statement :
      statement.Action
      ])) == toset([
      "ec2:DescribeInstances",
      "ssm:SendCommand",
      "ssm:GetCommandInvocation",
      "ssm:ListCommandInvocations"
    ])
    error_message = "The deploy role must contain only approved discovery and SSM actions."
  }

  assert {
    condition     = strcontains(aws_iam_role_policy.github_deploy.policy, "AWS-RunShellScript") && strcontains(aws_iam_role_policy.github_deploy.policy, "ssm:resourceTag/Project")
    error_message = "SendCommand must be limited to AWS-RunShellScript and project-tagged instances."
  }
}
