# ADR-001: 단일 EC2에 k3s를 운영한다

- 상태: 채택
- 날짜: 2026-09-29

관리형 EKS 대신 `t3.medium` 한 대에 k3s를 설치한다. 일주일짜리 개인 프로젝트에서 control plane, node, Pod, Service, Ingress를 직접 관찰하면서 USD 15 한도를 지키기 위한 선택이다.

장점은 낮은 비용, 빠른 생성·삭제, Kubernetes 운영 요소의 가시성이다. 단점은 node 장애 시 전체 서비스가 중단되고 autoscaling·다중 AZ·관리형 control plane이 없다는 점이다. 따라서 이 결과를 production HA 경험으로 표현하지 않는다.
