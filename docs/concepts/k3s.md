# k3s

k3s는 CNCF conformant Kubernetes 배포판으로, 설치 파일과 운영 의존성을 줄여 edge·개발·단일 노드 환경에서 쓰기 쉽게 만든다. Kubernetes API와 Deployment, Service, Ingress 같은 핵심 객체는 그대로 사용한다.

이 실습의 한 EC2가 control plane과 worker 역할을 모두 수행한다. API server와 scheduler가 원하는 상태를 관리하고, 같은 node의 kubelet/containerd가 실제 Pod를 실행한다. 내장 Traefik이 TCP 80 요청을 애플리케이션 Service로 전달한다.

단일 노드는 저렴하고 구조를 직접 관찰하기 쉽지만 host 장애가 곧 cluster 장애다. 두 Pod replica도 서로 다른 node에 분산되지 않으므로 고가용성이 아니다. 이 프로젝트의 목적은 HA를 주장하는 것이 아니라 배포·관측·복구 과정을 재현하는 것이다.

kubeconfig는 mode 600으로 유지하고 Kubernetes API를 security group에 공개하지 않는다. 운영 명령은 SSM으로 host 내부에서 실행한다.
