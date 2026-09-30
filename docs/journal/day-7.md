# Day 7 — 종료와 제출 자료 정리

## 안전한 종료

2026-09-30 11:08 UTC에 사전 검토한 destroy plan을 적용해 Terraform 관리 리소스 17개를 제거했다. 이후 자동 검증기로 Project tag 기반 AWS inventory와 Terraform state를 교차 확인했다.

```text
ec2_instances: 0
ebs_volumes: 0
elastic_ips: 0
terraform_state: 0
```

새 문서 커밋 때문에 삭제된 환경으로 배포가 재시도되지 않도록 deploy job에 `AWS_ENVIRONMENT_ACTIVE == 'true'` 조건을 추가하고 repository variable을 `false`로 설정했다.

## 비용 해석

당일 Cost Explorer는 USD 0, `Estimated=true`를 반환했다. 이는 최종 청구액이 아니라 집계 중인 값이다. 약 10시간의 라이브 구간과 종료 시각을 기록하고, 다음 날 이후 Project tag 기준으로 다시 조회할 수 있도록 명령을 남겼다.

## 포트폴리오 정리

공개 저장소에는 계정 ID, instance ID, 공인 IP, SSM command ID, 이메일, 비밀번호, Terraform state와 원시 운영 로그를 포함하지 않는다. 재현 가능한 코드·runbook·수치 요약·공개 GitHub Actions 실행 링크만 evidence index에 연결했다.
