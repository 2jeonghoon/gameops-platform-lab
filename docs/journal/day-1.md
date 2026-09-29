# Day 1 — API 기반과 테스트 계약

## 목표

운영 실험의 대상으로 사용할 최소한의 게임 세션 API를 만들고, 입력 검증과 상태 변경 규칙을 자동 테스트로 고정한다.

## 구현 범위

- `GET /healthz`, `GET /readyz`
- `POST /sessions`, `GET /sessions/{id}`, `DELETE /sessions/{id}`
- `player_count` 허용 범위: 1–100
- UTC 생성 시각과 UUID 세션 식별자
- 비동기 잠금으로 보호되는 인메모리 저장소

## 실행 명령

```bash
uv run pytest tests/app/test_health.py tests/app/test_sessions.py -v
uv run ruff check app tests
uv run ruff format --check app tests
```

## 테스트 기록

구현 전 테스트 수집은 `ModuleNotFoundError: No module named 'app'`로 실패했다. 이는 아직 API 구현이 없다는 이유로 실패한 의도한 RED 상태였다. 구현 후 동일 명령에서 6개 테스트가 모두 통과했고, Ruff lint와 format 검사도 오류 없이 끝났다.

## 의도한 한계

세션 저장소는 메모리 기반이므로 프로세스 재시작 시 데이터가 사라진다. 이 선택은 애플리케이션 기능보다 Terraform, k3s, CI/CD, 관측, 장애 대응을 학습하는 데 시간을 집중하기 위한 것이다.

## 장애 주입과 메트릭

환경변수 `FAULT_DELAY_MS`, `FAULT_ERROR_RATE`, `READINESS_FAIL`로 지연·오류·readiness 장애를 제어한다. 잘못된 범위는 시작 시 Pydantic 검증 오류로 거부한다. 장애는 `/sessions` 경로에만 적용하여 `/healthz`를 통한 프로세스 확인은 유지한다.

Prometheus 메트릭에는 HTTP 요청 수·지연시간, 활성 세션 수, 생성·삭제 누적 수를 기록한다. 요청 경로는 실제 UUID가 아닌 `/sessions/{session_id}` 템플릿으로 기록해 시계열의 label cardinality 증가를 방지한다. 구현 전에는 `app.telemetry`가 없어 1개 수집 오류로 RED를 확인했고, 구현 후 Task 2 테스트 7개가 통과했다.
