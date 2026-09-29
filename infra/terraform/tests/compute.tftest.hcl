mock_provider "aws" {}

run "secure_single_node_compute" {
  command = plan

  override_data {
    target = data.aws_ami.ubuntu
    values = {
      id = "ami-test"
    }
  }

  variables {
    budget_alert_email = "operator@example.com"
    github_owner       = "example-owner"
    github_repository  = "gameops-platform-lab"
  }

  assert {
    condition     = aws_instance.k3s.instance_type == "t3.medium"
    error_message = "The approved instance type is t3.medium."
  }

  assert {
    condition     = toset(data.aws_ami.ubuntu.owners) == toset(["099720109477"]) && anytrue([for item in data.aws_ami.ubuntu.filter : item.name == "name" && anytrue([for value in item.values : strcontains(value, "ubuntu-noble-24.04-amd64")])])
    error_message = "The AMI must select Canonical Ubuntu 24.04 LTS amd64."
  }

  assert {
    condition     = aws_instance.k3s.root_block_device[0].encrypted && aws_instance.k3s.root_block_device[0].volume_size == 20 && aws_instance.k3s.root_block_device[0].volume_type == "gp3"
    error_message = "The root volume must be encrypted 20 GiB gp3."
  }

  assert {
    condition     = aws_instance.k3s.metadata_options[0].http_tokens == "required"
    error_message = "IMDSv2 must be required."
  }

  assert {
    condition     = aws_instance.k3s.iam_instance_profile == aws_iam_instance_profile.k3s.name && local.ssh_key_name == null
    error_message = "The host must use the SSM profile and no SSH key pair."
  }
}
