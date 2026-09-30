# GameOps Platform Lab

AWS 단일 노드 k3s에 게임 세션 API를 배포하고, CI/CD·관측·장애 대응·비용 통제를 실제 운영 증거로 검증한 DevOps 포트폴리오입니다. 2026-09-30 라이브 환경에서 정상 부하와 세 가지 장애 실험을 완료한 뒤 Terraform으로 전체 인프라를 제거하고 잔존 자원 0건을 확인했습니다.

## 검증한 결과

- Terraform으로 VPC, public subnet, Security Group, EC2, IAM, GitHub OIDC, AWS Budget 등 17개 리소스를 선언하고 실제 적용
- GitHub Actions CI 성공 commit만 전체 SHA 이미지로 빌드하고, OIDC 단기 자격 증명과 SSM으로 배포
- Prometheus와 Grafana로 두 API endpoint 및 네 가지 alert rule을 확인
- 정상 부하 18,939 requests, 실패 0%, p95 15.84ms
- Pod 삭제 후 7.101초 내 대체 Pod Ready, 요청 실패 0%
- 잘못된 이미지에서 기존 Ready replica 2개 유지, 약 0.84초 만에 rollback
- 의도적 열화에서 error·latency alert의 pending → firing → inactive 전이 확인
- 종료 후 EC2·EBS·Elastic IP·Terraform state 모두 0건 확인

수치는 한 번의 단일 노드 실험 결과이며 일반적인 성능 기준으로 주장하지 않습니다. 상세 근거는 [Evidence index](docs/evidence-index.md)에 연결했습니다.

## 구조

```text
GitHub push
    └─ CI: test · lint · Terraform · Kubernetes · monitoring 검증
        └─ deploy gate가 켜진 경우
            ├─ GHCR: commit SHA 이미지
            └─ GitHub OIDC → AWS IAM → SSM
                                      └─ EC2 Ubuntu
                                          └─ k3s
                                              ├─ game-session-api × 2
                                              └─ Prometheus · Grafana
```

외부 공개 ingress는 HTTP 80만 허용했습니다. SSH 22, Kubernetes API 6443, 관측 포트는 공개하지 않았고 운영 명령은 SSM으로 실행했습니다. 자세한 설계와 한계는 [architecture](docs/architecture.md), [security](docs/security.md)를 참고하십시오.

## 로컬 검증

필요 도구와 버전은 [prerequisites](docs/guides/prerequisites.md), 고정한 버전은 [version matrix](docs/guides/version-matrix.md)에 기록했습니다.

```bash
uv sync
make verify
uv run uvicorn app.main:app --reload
```

## 라이브 환경 재현

1. [Terraform 프로비저닝](docs/guides/provision.md)
2. [k3s bootstrap](docs/guides/bootstrap-k3s.md)
3. [배포](docs/guides/deploy.md)
4. [관측](docs/guides/observe.md)
5. [teardown](docs/guides/teardown.md)

배포 워크플로는 삭제된 환경에 접근하지 않도록 repository variable `AWS_ENVIRONMENT_ACTIVE=false` 상태입니다. 인프라를 다시 만든 뒤 배포 대상과 IAM을 검증하고 이 값을 `true`로 바꿔야 합니다.

## 운영 문서

- 장애 대응: [deployment failure](docs/runbooks/deployment-failure.md), [rollback](docs/runbooks/rollback.md), [high error rate](docs/runbooks/high-error-rate.md), [high latency](docs/runbooks/high-latency.md), [target down](docs/runbooks/target-down.md)
- 장애 실험: [Pod termination](docs/incidents/001-pod-termination.md), [invalid image](docs/incidents/002-invalid-image.md), [load degradation](docs/incidents/003-load-degradation.md)
- 개념 설명: [Terraform](docs/concepts/terraform.md), [VPC](docs/concepts/vpc.md), [Security Group](docs/concepts/security-group.md), [k3s](docs/concepts/k3s.md)

## 범위와 한계

- 세션 데이터는 메모리에만 저장되어 Pod 재시작 시 사라집니다.
- 단일 EC2와 단일 k3s node이므로 node 장애를 견디는 고가용성 구성은 아닙니다.
- Loki는 가용 메모리 기준을 충족하지 못해 설치하지 않고 Kubernetes logs를 사용했습니다.
- TLS, 인증, 영구 데이터베이스, 원격 Terraform state는 이번 실습 범위에서 제외했습니다.
