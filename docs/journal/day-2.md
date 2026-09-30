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

EC2·IAM·OIDC 구성도 mock provider로 추가 검증했다. `t3.medium`, Canonical Ubuntu 24.04 amd64, encrypted 20 GiB gp3, IMDSv2, SSM profile, SSH key 없음, 정확한 GitHub main subject와 네 가지 deploy action만 허용함을 테스트했다.

## Live result — 2026-09-30

AWS CLI의 `gameops` profile과 IAM 관리자 사용자의 임시 로그인 세션으로 identity를 확인했다. plan에는 승인한 17개 리소스만 있었고 SSH, NAT Gateway, load balancer, RDS, EKS, Route 53, ACM은 없었다. apply 후 월 USD 15 budget과 두 알림 threshold가 생성됐다. 계정 ID와 실제 이메일은 기록하지 않았다.
