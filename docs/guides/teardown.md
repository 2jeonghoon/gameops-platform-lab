# Teardown 가이드

이 절차는 Terraform state가 있는 동일 checkout에서 프로젝트 인프라를 제거하고, state와 AWS 양쪽에 비용 발생 자원이 남지 않았음을 확인한다. `destroy` 전에 저장된 plan을 직접 검토해야 한다.

## 1. 배포 중지

GitHub repository variable을 먼저 끈다.

```bash
gh variable set AWS_ENVIRONMENT_ACTIVE --body false
```

이 값이 `false`이면 CI가 성공해도 deploy job은 실행되지 않는다.

## 2. 삭제 plan 검토

```bash
terraform -chdir=infra/terraform plan -destroy -out=gameops-destroy.tfplan
terraform -chdir=infra/terraform show gameops-destroy.tfplan
```

계획의 대상과 개수를 확인하고 Project 밖의 자원이 포함되지 않았는지 검토한다. 이 프로젝트의 실제 종료 계획은 `0 to add, 0 to change, 17 to destroy`였다.

## 3. 검토한 plan 적용

```bash
terraform -chdir=infra/terraform apply gameops-destroy.tfplan
```

새 plan을 즉석에서 다시 만들지 않고 검토한 파일을 적용한다. 2026-09-30 실제 실행은 17개 리소스 삭제로 완료됐다.

## 4. 잔존 자원 검증

```bash
AWS_PROFILE=gameops AWS_REGION=ap-northeast-2 \
  uv run python scripts/verify_teardown.py \
  --project gameops-platform-lab \
  --region ap-northeast-2
```

검증기는 Project tag가 붙은 미종료 EC2, EBS volume, Elastic IP와 `terraform state list`를 조회한다. 네 항목이 모두 0일 때만 성공한다. 조회 자체가 실패하면 안전하게 실패 코드 2를 반환한다.

## 5. 비용 확인

Cost Explorer에는 당일 사용량이 늦게 반영될 수 있다. 종료 직후와 다음 날 이후에 [비용 문서](../cost.md)의 명령으로 다시 확인한다. Budget 삭제는 비용 청구를 중지시키지 않으므로 잔존 자원 검증이 핵심이다.
