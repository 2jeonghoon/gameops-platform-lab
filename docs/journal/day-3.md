# Day 3 — 안전한 k3s host bootstrap

cloud-init은 `git`, `curl`, SSM agent를 준비하고 k3s `v1.37.0+k3s1`, Helm `v4.3.0`을 고정 설치한다. kubeconfig는 mode 600이며 node 조회가 성공한 뒤에만 bootstrap marker를 쓴다.

구현 전 Terraform 테스트 2개는 리소스 미정의로 실패했고 cloud-init 검사는 template 부재로 실패했다. 구현 후 network·compute·IAM mock test 3개와 cloud-init 계약이 통과했다. 아직 실제 EC2를 만들지 않았으므로 cloud-init 실행 성공은 라이브 단계에서 SSM으로 확인해야 한다.

Kubernetes manifest 정책 테스트는 `k8s/base` 부재로 먼저 2개가 실패했다. 구현 후 정책 테스트 2개와 kubeconform schema 검증에서 5개 resource가 모두 유효했다. 로컬 컨테이너에 `smoke_test.sh`를 실행해 health, readiness, 세션 생성·조회·삭제가 통과하는 것도 확인했다.
