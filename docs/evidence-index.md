# Evidence index

이 문서는 공개 가능한 재현 경로와 2026-09-30 실제 측정 결과를 연결한다. AWS 계정 ID, 공인 IP, instance ID, SSM command ID, Grafana 비밀번호, Terraform state는 기록하지 않았다. 원시 JSON과 console log는 Git에서 제외한 `work/evidence/`, 클러스터 event는 EC2의 `/var/lib/gameops/evidence/`에 보존한다.

## Build and delivery

| Claim | Public evidence | Verified result |
| --- | --- | --- |
| application, Terraform, manifest, monitoring, shell 검증 | [CI run](https://github.com/2jeonghoon/gameops-platform-lab/actions/runs/36680483754) | success |
| OIDC 단기 자격 증명, SHA image, SSM 배포 | [deploy run](https://github.com/2jeonghoon/gameops-platform-lab/actions/runs/36680649002) | success |
| immutable deployed revision | commit `a88f9f7`과 동일한 image SHA | rollout·smoke success |
| 공개 API lifecycle | `bash scripts/smoke_test.sh http://REDACTED` | 12/12 반복 통과 |

## Infrastructure and security

| Claim | Evidence path | Verified result |
| --- | --- | --- |
| 제한된 리소스와 비용 가드레일 | `terraform plan`, `terraform test`, [provision guide](guides/provision.md) | 17 resources, EC2 1대, 월 USD 15 budget |
| SSH·Kubernetes API 비공개 | Security Group plan과 [security 문서](security.md) | 공개 ingress는 TCP 80만 허용 |
| k3s bootstrap | SSM에서 cloud-init, systemd, node, `/readyz` 조회 | cloud-init done, k3s active, node Ready |
| 비밀 없는 배포 | GitHub OIDC trust와 SSM IAM policy tests | 장기 AWS key와 SSH key 없음 |
| 비용 안전 종료 | [teardown guide](guides/teardown.md), tag inventory, Terraform state | EC2 0, EBS 0, Elastic IP 0, state 0 |

## Observability

| Claim | Query or check | Verified result |
| --- | --- | --- |
| API metric collection | Prometheus `/api/v1/targets`, service label `game-session-api` | 두 endpoint 모두 up |
| Grafana dashboard | `/api/dashboards/uid/game-session-api` | title 확인, 8 panels |
| alert rules | Prometheus `/api/v1/rules?type=alert` | error, latency, target-down, restart 4개 |
| monitoring health | `kubectl -n monitoring get pods` | 6 Pods, not-ready 0 |
| log path | installer memory gate와 [observe guide](guides/observe.md) | MemAvailable 약 1.07GiB로 Loki 생략, Kubernetes logs 사용 |

## Performance and incidents

| Experiment | Workload | Result | Report |
| --- | --- | --- | --- |
| normal baseline | 5 VU, 5분 | 18,939 requests, 0% failed, p95 15.84ms | [Day 6](journal/day-6.md) |
| Pod termination | 정상 부하 중 Pod 1개 삭제 | replacement Ready 7.101초, 19,065 requests, 0% failed, p95 16.00ms | [Incident 001](incidents/001-pod-termination.md) |
| invalid image | 정상 부하 중 nonexistent tag | ImagePullBackOff, 기존 Ready 2, rollback 약 0.84초, 0% failed | [Incident 002](incidents/002-invalid-image.md) |
| degradation | 350ms, 10% 오류, 80 iter/s, 7분 | 93,737 requests, 9.88% failed, p95 400.94ms, alerts firing→inactive | [Incident 003](incidents/003-load-degradation.md) |

## Reproduction commands

```bash
make verify
bash scripts/smoke_test.sh http://PUBLIC_IPV4
k6 run -e BASE_URL=http://PUBLIC_IPV4 load-test/normal.js
sudo bash scripts/inject_fault.sh 350 0.10 false
k6 run -e BASE_URL=http://PUBLIC_IPV4 load-test/degradation.js
sudo bash scripts/inject_fault.sh 0 0 false
```

성능 수치는 이 단일 실행 환경의 측정값이며 보편적 benchmark로 주장하지 않는다.

## Teardown

2026-09-30 11:08 UTC에 저장한 destroy plan의 17개 리소스를 제거했다. `scripts/verify_teardown.py`가 Project tag 기반 EC2·EBS·Elastic IP inventory와 Terraform state를 별도로 조회해 모두 0건임을 확인했다. 당일 Cost Explorer 결과는 USD 0이지만 `Estimated=true`였으므로 확정 비용으로 사용하지 않는다. 종료 절차와 재검증 명령은 [Day 7](journal/day-7.md)에 기록했다.
