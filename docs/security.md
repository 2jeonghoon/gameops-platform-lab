# Security review

## Identity and deployment

- GitHub Actions는 저장된 AWS access key 대신 OIDC로 짧은 수명의 역할 자격 증명을 받는다.
- trust policy는 immutable repository owner/repository ID와 `refs/heads/main` subject에 묶여 있다.
- 배포 역할은 프로젝트 tag가 붙은 단일 EC2에 승인된 SSM document를 실행하고 상태를 읽는 권한만 갖는다.
- EC2 instance role은 SSM 관리에 필요한 managed policy만 사용한다.
- SSH key pair와 inbound TCP 22는 만들지 않는다.

## Network boundary

- public subnet의 Security Group ingress는 TCP 80뿐이다.
- k3s API 6443, Grafana, Prometheus, Alertmanager는 인터넷에 열지 않는다.
- 운영 접근은 SSM outbound channel과 필요 시 loopback port forwarding을 사용한다.
- NAT Gateway, external load balancer, EKS, RDS, Route 53, ACM은 이 비용 제한 실습의 범위 밖이다.

## Workload controls

- container는 non-root, `allowPrivilegeEscalation: false`, all capabilities drop, read-only root filesystem로 실행한다.
- startup, liveness, readiness probe와 CPU/memory request·limit을 둔다.
- image는 전체 Git SHA tag로 배포하며 `latest`를 사용하지 않는다.
- rolling update는 `maxUnavailable: 0`으로 기존 정상 replica를 보존한다.
- Trivy critical vulnerability scan, Gitleaks history scan, actionlint, kubeconform을 CI에서 실행한다.

## Secret and evidence handling

- `terraform.tfvars`, state, plan, kubeconfig, `.env`, credentials, `work/`, `outputs/`는 Git에서 제외한다.
- Grafana admin password는 설치 중 health check에만 사용하고 출력·저장하지 않는다.
- 공개 문서에서 account ID, instance ID, public IP, SSM command ID, Pod suffix를 제거한다.
- resume 사진, 이메일, 전화번호 같은 지원자 개인정보는 public repository에 넣지 않는다.
- 실제 raw output은 로컬 ignored directory와 임시 EC2 evidence directory에만 둔다.

## Known limitations

- 단일 EC2와 단일 k3s node이므로 host/AZ 장애에 대한 고가용성은 없다.
- application 세션은 메모리 저장소다. Traefik NativeLB와 Service ClientIP affinity는 짧은 실험용 보완이며 Pod replacement 시 상태를 보존하지 못한다.
- production에서는 공유 상태 저장소, TLS, WAF/rate limit, private worker subnet, 중앙 log 보존, remote encrypted Terraform state와 state locking이 필요하다.
- Loki는 설치 시 가용 메모리가 안전 기준보다 낮아 생략했다. Kubernetes logs를 fallback으로 사용했으며 장기 log 보존은 제공하지 않는다.

## Audit checklist

```bash
git status --short
git ls-files | rg '(tfstate|tfplan|terraform[.]tfvars|kubeconfig|credentials|outputs/|work/)'
gitleaks git --redact
gitleaks dir . --redact
```

마지막 검증에서는 추적 파일 목록에 금지된 경로가 없어야 하고 두 Gitleaks 실행이 모두 0으로 종료되어야 한다.
