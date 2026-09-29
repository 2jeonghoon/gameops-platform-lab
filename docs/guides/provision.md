# Terraform 프로비저닝

실제 값은 Git에 포함하지 않는 `infra/terraform/terraform.tfvars`에 작성한다.

```bash
cp infra/terraform/terraform.tfvars.example infra/terraform/terraform.tfvars
terraform -chdir=infra/terraform init
terraform -chdir=infra/terraform fmt -check -recursive
terraform -chdir=infra/terraform validate
terraform -chdir=infra/terraform test
terraform -chdir=infra/terraform plan -out=gameops.tfplan
terraform -chdir=infra/terraform show gameops.tfplan
```

plan에서 EC2 한 대, 20 GiB gp3, VPC 구성, IAM/OIDC, Budget만 있는지 확인한다. TCP 22, 6443, monitoring port와 EKS, NAT Gateway, load balancer, RDS, Route 53, ACM이 있으면 apply하지 않는다.

검토 후에만 `terraform -chdir=infra/terraform apply gameops.tfplan`을 실행한다. plan 파일과 state는 민감할 수 있으므로 공유하지 않는다.
