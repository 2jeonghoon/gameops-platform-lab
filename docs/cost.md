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

NAT Gateway, load balancer, EKS, RDS, Route 53, ACM은 만들지 않는다. 실제 사용 시간과 비용은 라이브 실행 후 이 문서에 추정치와 함께 기록한다.
