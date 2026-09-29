# ADR-002: 실습 기간에는 local Terraform state를 사용한다

- 상태: 채택
- 날짜: 2026-09-29

## 맥락

한 명이 일주일 동안 실행하고 마지막에 모든 AWS 리소스를 삭제하는 포트폴리오 실습이다. remote backend용 S3와 DynamoDB를 추가하면 학습 가치는 있지만 리소스·권한·정리 범위가 늘어난다.

## 결정

Terraform 기본 local state를 사용한다. `*.tfstate*`, plan, 실제 tfvars는 Git에서 제외하고 한 workstation에서만 apply/destroy한다. 작업 종료 전에 state가 추적하는 리소스와 AWS tag 기반 조회를 모두 확인한다.

## 결과

구성이 단순하고 추가 AWS 비용이 없다. 반면 협업 잠금, 원격 백업, 암호화된 중앙 보관, CI 실행은 제공하지 않는다. state 파일을 잃으면 복구가 어렵다는 위험을 감수한다.

production 또는 다인 협업으로 확장한다면 versioning·encryption·접근 통제를 적용한 S3 backend와 state locking을 사용하고, backend bootstrap을 별도 stack으로 관리한다.
