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
| actions/checkout | 7.0.1 / `3d3c42e5aac5ba805825da76410c181273ba90b1` | CI |
| actions/setup-python | 7.0.0 / `5fda3b95a4ea91299a34e894583c3862153e4b97` | CI |

확인 근거는 각 프로젝트의 공식 릴리스와 `uv.lock`이다. GitHub Actions는 이동 가능한 major tag 대신 검토한 commit SHA를 사용한다.
