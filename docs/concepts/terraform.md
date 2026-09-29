# Terraform

Terraform은 선언한 원하는 상태와 provider가 조회한 실제 상태의 차이를 계산해 인프라 변경 계획을 만든다.

## 기본 흐름

1. `terraform init`은 provider를 내려받고 잠금 파일을 만든다.
2. `terraform fmt`와 `validate`는 형식과 구성 오류를 검사한다.
3. `terraform plan`은 생성·변경·삭제 예정 항목을 보여주지만 적용하지 않는다.
4. `terraform apply`는 검토한 계획을 실행하고 state에 원격 리소스와 구성의 대응 관계를 기록한다.
5. `terraform destroy`는 state가 추적하는 프로젝트 리소스를 제거한다.

Terraform state는 단순 로그가 아니라 리소스 주소와 실제 AWS ID를 연결하는 운영 데이터다. 유실하면 삭제·변경 판단이 어려워지고, 동시에 여러 사람이 수정하면 충돌할 수 있다. state와 plan에는 민감값이 포함될 수 있으므로 Git에 커밋하지 않는다.

이 프로젝트의 `.tftest.hcl`은 AWS mock provider를 사용한다. 실제 계정이나 비용 없이 CIDR, 공개 포트, 예산 한도를 검증하지만, AWS 권한과 실제 API 동작까지 보장하지는 않는다. 실제 `plan`은 적용 전에 별도로 검토한다.
