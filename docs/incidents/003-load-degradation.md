# Incident experiment 003 — Load degradation

> **NOT YET EXECUTED** — Task 10에서 실제 시각과 측정값으로 이 표시와 placeholder를 교체하기 전까지 계획서다.

## Hypothesis

고정 지연 또는 오류 fault와 높은 arrival rate를 결합하면 p95 250ms 또는 5xx 5% 경보가 정해진 `for` 시간 뒤 firing되고, fault를 제거하면 resolved된다.

## Preconditions and workload

- 정상 baseline 5분과 node/Pod resource 여유 기록
- Grafana, Prometheus target, Alertmanager 정상
- `load-test/degradation.js`는 threshold 실패를 성공으로 위장하지 않음

## Reproduction

```bash
sudo bash scripts/inject_fault.sh 350 0.10 false
k6 run -e BASE_URL=http://PUBLIC_IPV4 load-test/degradation.js
```

종료 후 반드시 fault를 복원한다.

```bash
sudo bash scripts/inject_fault.sh 0 0 false
```

## Timeline

NOT YET EXECUTED. fault 적용, 부하 시작, pending, firing, fault 해제, resolved UTC 시각을 기록한다.

## Metrics, logs, events, and alerts

NOT YET EXECUTED. k6 summary, 요청률, dropped iterations, 5xx, p50/p95/p99, CPU/memory, restart, log, alert 상태를 첨부한다.

## Response

NOT YET EXECUTED. threshold breach를 확인하고 계획된 종료 시점 또는 안전 한계에서 부하를 중단한다.

## Recovery

NOT YET EXECUTED. fault를 0/0/false로 되돌리고 Deployment rollout 완료 시각을 기록한다.

## Verification

NOT YET EXECUTED. smoke test, 정상 부하 재실행, p95 250ms 미만, 5xx 1% 미만, alert resolved를 기록한다.

## Root cause

NOT YET EXECUTED. 주입한 delay/error, 처리 용량, resource 포화 중 실제 지배 요인을 측정값으로 설명한다.

## Prevention

NOT YET EXECUTED. capacity test, autoscaling, timeout/backpressure, alert tuning 후보와 우선순위를 기록한다.
