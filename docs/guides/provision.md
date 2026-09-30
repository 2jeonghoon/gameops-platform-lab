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

2026-09-30 실제 적용에서는 plan과 일치하는 17개 리소스를 생성했다. cloud-init 완료, SSM Agent active, k3s active, node Ready와 Kubernetes `/readyz`를 SSH 없이 SSM으로 확인했다. 월 USD 15 budget과 USD 5/10 알림은 지원자가 지정한 이메일로 설정했지만 주소는 repository에 기록하지 않는다.

인프라를 다시 만들고 배포 검증까지 마친 경우에만 GitHub repository variable `AWS_ENVIRONMENT_ACTIVE`를 `true`로 설정한다. 기본값 또는 `false`에서는 CI 이후 deploy job이 실행되지 않는다.

실습 종료 시에는 state를 가진 동일 checkout에서 [teardown guide](teardown.md)를 따라 destroy한다. 라이브 리소스가 남아 있는 동안 EC2와 EBS 비용이 계속 발생한다.
