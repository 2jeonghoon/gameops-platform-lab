# 비용 가드레일

## 한도

- AWS promotional credit 잔액: 사용자가 확인한 USD 114.51
- credit 만료일: 2027-01-14
- 이 프로젝트의 자체 지출 한도: USD 15
- AWS Budget 알림: 실제 비용 USD 5, USD 10

Budget은 지출을 자동 차단하지 않고 알림을 보낸다. 따라서 짧은 실행 시간, 금지 리소스 목록, 매일 확인, 종료 즉시 `terraform destroy`, tag 기반 잔존 리소스 확인을 함께 사용한다.

## 비용을 만들 수 있는 주요 항목

- `t3.medium` EC2 실행 시간
- 20 GiB gp3 EBS volume
- public IPv4 사용 시간
- 소량의 data transfer

NAT Gateway, load balancer, EKS, RDS, Route 53, ACM은 만들지 않는다.

## 실제 실행 기록

- 실행일: 2026-09-30
- 유료 자원 가동 관찰 구간: 약 10시간(프로비저닝 약 01:08 UTC, teardown 검증 11:08 UTC)
- teardown 결과: EC2 0, EBS 0, Elastic IP 0, Terraform state 0
- 2026-09-30 11:08 UTC Cost Explorer 조회: USD 0, `Estimated=true`

Cost Explorer 값은 결제 데이터 집계 지연이 있는 당일 추정치이므로 최종 비용이 0달러라고 단정하지 않는다. 최종 청구액은 다음 날 이후 동일한 Project tag와 기간으로 다시 확인해야 한다. 크레딧 적용 전 비용과 크레딧 차감은 청구서에서 별도로 확인한다.

```bash
aws ce get-cost-and-usage \
  --region us-east-1 \
  --time-period Start=2026-09-30,End=2026-10-01 \
  --granularity DAILY \
  --metrics UnblendedCost \
  --filter '{"Tags":{"Key":"Project","Values":["gameops-platform-lab"],"MatchOptions":["EQUALS"]}}'
```
