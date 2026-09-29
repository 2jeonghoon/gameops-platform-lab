# 버전 매트릭스

2026-09-29에 검토하고 고정한 버전이다. 이미지와 도구를 변경할 때는 테스트와 취약점 검사를 다시 실행하고 이 표를 함께 갱신한다.

| 구성 요소 | 고정 버전 | 사용 위치 |
|---|---:|---|
| Python | 3.12.14 | 로컬 관리 런타임, 컨테이너 base image |
| uv | 0.12.17 | 의존성 잠금·동기화, 컨테이너 build stage |
| FastAPI | 0.141.1 | `uv.lock` |
| Pydantic | 2.13.5 | `uv.lock` |
| Uvicorn | 0.54.0 | `uv.lock` |
| Trivy | 0.74.0 | 컨테이너 취약점 검사 |
| Gitleaks | 8.30.1 | Git 기록과 작업 트리 비밀 검사 |
| actionlint | 1.7.12 | GitHub Actions 정적 검사 |
| Terraform CLI | 1.16.4 | IaC 작성·검증·실행 |
| AWS provider | 6.62.0 | `infra/terraform/.terraform.lock.hcl` |
| k3s / Kubernetes | v1.37.0+k3s1 / v1.37.0 | EC2 bootstrap |
| Helm | v4.3.0 | 관측 stack 설치 |
| kubectl / Kustomize | 1.37.0 / 5.8.1 | manifest 렌더링 |
| kubeconform | 0.8.0 | Kubernetes schema 검증 |
| ShellCheck | 0.11.0 | 배포·rollback shell script 정적 검사 |
| kube-prometheus-stack chart | 91.8.0 | Prometheus, Grafana, Alertmanager, exporters |
| Loki chart | 18.13.7 | 선택적 단일 바이너리 log storage |
| Grafana Alloy chart | 1.13.0 | 선택적 Kubernetes Pod log 수집 |
| actions/checkout | 7.0.1 / `3d3c42e5aac5ba805825da76410c181273ba90b1` | CI |
| actions/setup-python | 7.0.0 / `5fda3b95a4ea91299a34e894583c3862153e4b97` | CI |
| hashicorp/setup-terraform | 4.0.1 / `dfe3c3f87815947d99a8997f908cb6525fc44e9e` | CI |
| aws-actions/configure-aws-credentials | 6.3.0 / `e1253824e5c10ff9df46874f81ed3ec929e19cfd` | GitHub OIDC AWS 인증 |

확인 근거는 각 프로젝트의 공식 릴리스와 `uv.lock`이다. GitHub Actions는 이동 가능한 major tag 대신 검토한 commit SHA를 사용한다.
