# Day 2 — Terraform 네트워크와 비용 가드레일

## 목표

AWS 리소스를 생성하기 전에 VPC, 공개 subnet, Internet Gateway, route table, HTTP-only security group, 월 USD 15 budget을 코드와 테스트로 고정한다.

## RED

구현 전 `terraform test`는 AWS provider와 참조 리소스가 없어 실패했다.

## GREEN

```bash
terraform -chdir=infra/terraform fmt -check -recursive
terraform -chdir=infra/terraform validate
terraform -chdir=infra/terraform test
```

Terraform 1.16.4와 AWS provider 6.62.0으로 구성 검증에 성공했다. mock provider 테스트 결과는 `1 passed, 0 failed`였다. 테스트는 서울 region, CIDR, 공개 IPv4, IGW 기본 경로, TCP 80 단일 공개 규칙, SSH 금지, USD 15 한도와 USD 5/10 알림을 확인한다.

이 단계에서는 실제 AWS API를 호출하거나 유료 리소스를 만들지 않았다. 계정 ID, credential, 실제 알림 이메일도 기록하지 않았다.
