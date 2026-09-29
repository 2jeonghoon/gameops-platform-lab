# GameOps Platform Lab

게임 세션 API를 AWS 단일 노드 k3s 환경에 배포하고, 자동화·관측·장애 대응·비용 통제를 실제 증거와 함께 학습하는 DevOps 포트폴리오 프로젝트입니다.

현재 애플리케이션은 인프라와 운영 절차를 검증하기 위한 작은 FastAPI 서비스입니다. 사용자 기능을 넓히는 대신 배포 안정성, 가시성, 복구 가능성을 깊게 다루는 것이 목표입니다.

## 로컬 실행

```bash
uv sync
uv run uvicorn app.main:app --reload
```

검증은 `make verify`로 실행합니다.

## 컨테이너

```bash
bash tests/container/test_container.sh
```

이미지는 잠긴 runtime 의존성만 설치하며 UID 10001로 실행됩니다. `/healthz` 기반 Docker health check와 포트 8000을 제공합니다.

## 현재 제한

- 세션 데이터는 프로세스 메모리에만 저장됩니다.
- 프로세스나 Pod가 재시작되면 세션 데이터가 사라집니다.
- 인증과 영구 데이터베이스는 이 프로젝트의 운영 자동화 범위에 포함하지 않습니다.
