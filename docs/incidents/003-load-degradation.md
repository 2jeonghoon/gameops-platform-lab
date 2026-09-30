# Incident experiment 003 — Load degradation

## Hypothesis

350ms 지연과 10% 오류를 주입한 상태에서 80 iteration/s를 가하면 실패율 5% 또는 p95 250ms 목표를 넘고, 지속 시간 뒤 Prometheus 경보가 firing된다. fault를 제거하면 smoke test가 복구되고 이동 창이 소진된 뒤 경보가 resolved되어야 한다.

## Preconditions and workload

- 2026-09-30 실행
- 정상 기준선: 18,939 요청, 실패 0%, p95 15.84ms
- Prometheus API 타깃 2개 `up`, 네 경보 inactive
- k6 2.3.0 constant-arrival-rate 80 iteration/s, 7분, 최대 150 VU
- 종료 트랩이 항상 fault를 `0 / 0 / false`로 복원하고 smoke test를 실행

## Reproduction

```bash
sudo bash scripts/inject_fault.sh 350 0.10 false
k6 run -e BASE_URL=http://REDACTED load-test/degradation.js
sudo bash scripts/inject_fault.sh 0 0 false
```

공인 주소와 AWS 식별자는 증거 파일과 공개 문서에서 제거했다.

## Timeline (UTC)

- 07:20:17 — fault rollout 완료, 부하 시작
- 07:22:47 — HighErrorRate와 HighLatency 모두 pending 관측
- 07:24:12 — HighErrorRate firing, HighLatency pending
- 07:27:18 — 7분 부하 종료, k6 exit 99
- 07:27:30 — HighErrorRate와 HighLatency 모두 firing
- 07:27:35 — fault 복원 rollout과 recovery smoke test 완료
- 복원 직후 — 두 경보는 이동 창 때문에 firing 상태 유지
- 07:35:39 — 네 경보 모두 inactive(resolved) 확인

## Metrics, logs, events, and alerts

- HTTP 요청: 93,737, 222.61 req/s
- HTTP 실패: 9,262건, 9.88%
- latency: 평균 370.29ms, p95 400.94ms, 최대 1.82s
- iteration: 33,441, dropped 160, interrupted 0
- 최대 VU: 150
- application check: 33,440 성공, 1 실패
- k6: `http_req_failed < 5%`, `p95 < 250ms` 두 threshold 모두 실패, exit 99
- Prometheus: error와 latency가 pending에서 firing으로 전이
- TargetDown, PodRestarted: inactive, monitoring Pod 6개 모두 Ready

## Response

의도한 안전 범위인 최대 150 VU와 7분을 넘기지 않았다. TargetDown이나 노드 장애가 없어서 조기 중단 조건은 충족되지 않았다. threshold 실패를 성공으로 숨기지 않고 exit 99를 증거로 보존했다.

## Recovery

종료 트랩이 ConfigMap을 delay 0, error rate 0, readiness false로 되돌리고 두 Pod rollout을 완료했다. 외부 health, readiness, 세션 생성·조회·삭제 smoke test가 통과했다. 07:35:39 UTC 확인에서 error, latency, target down, restart 경보가 모두 inactive였다.

## Verification

fault 복원 직후 smoke test와 후속 Prometheus 경보 해소가 모두 확인됐다. 원시 요약은 Git에 포함하지 않는 `work/evidence`에 보존하고 공개 문서에는 집계값과 재현 명령만 기록한다.

## Root cause

지배 요인은 의도적으로 주입한 350ms 응답 지연과 10% 오류다. 처리량은 목표 80 iteration/s에 근접했지만 최대 VU 150에 도달하고 160 iteration이 drop되어 지연이 동시성 요구량도 증가시켰다. CPU/메모리 고갈이나 target loss는 관찰되지 않았다.

## Prevention

- 배포 전 정상·열화 capacity profile을 반복 실행한다.
- 공유 상태 저장소 도입 후 수평 확장과 HPA를 검증한다.
- timeout, bounded concurrency, backpressure를 적용한다.
- 5분 latency 경보는 확실한 지속 장애를 잡지만 탐지 시간이 길다. warning과 page 조건을 분리하는 방안을 검토한다.
