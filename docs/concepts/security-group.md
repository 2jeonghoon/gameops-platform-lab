# Security Group

Security Group은 ENI에 적용되는 stateful 가상 방화벽이다. 허용 규칙만 정의하며, 들어온 연결이 허용되면 그 응답 트래픽은 별도 inbound 규칙 없이 돌아갈 수 있다.

이 프로젝트의 공개 inbound 규칙은 TCP 80 하나뿐이다. SSH 22, Kubernetes API 6443, Grafana 3000, Prometheus, Alertmanager, Loki는 공개하지 않는다. 서버 관리는 SSH key와 공개 관리 포트 대신 AWS Systems Manager를 사용한다.

Outbound는 패키지 설치, GHCR image pull, AWS API와 SSM 연결을 위해 IPv4 전체를 허용한다. 이는 단일 실습 host의 단순화이며, production에서는 VPC endpoint, egress proxy, 목적지 제한을 검토해야 한다.

Terraform test는 공개 ingress 목록이 정확히 하나이고 포트가 80이며 22가 없음을 확인한다. 새 포트가 필요하면 코드부터 추가하는 것이 아니라 위협 모델과 접근 경로를 먼저 갱신해야 한다.
