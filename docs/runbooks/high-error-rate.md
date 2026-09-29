# High error rate runbook

## Trigger

`GameSessionApiHighErrorRate`: 전체 요청 중 5xx 비율이 5%를 초과한 상태가 2분 지속된다.

## Impact

세션 생성·조회·삭제 요청이 실패하며 client retry와 사용자 이탈이 증가할 수 있다.

## Queries

```promql
sum(rate(gameops_http_requests_total{status_class="5xx"}[2m])) / clamp_min(sum(rate(gameops_http_requests_total[2m])), 0.001)
sum by (route, method) (rate(gameops_http_requests_total{status_class="5xx"}[2m]))
```

Loki: `{namespace="gameops", app="game-session-api"} |= "error"`. Fallback: `kubectl -n gameops logs deployment/game-session-api --all-pods=true --since=15m`.

## Diagnosis

1. 오류가 특정 route·method·Pod에 집중되는지 확인한다.
2. `FAULT_ERROR_RATE`가 실험 종료 후 0으로 복원됐는지 확인한다.
3. Pod restart, readiness, CPU/memory limit, rollout SHA와 같은 시각의 event를 비교한다.

## Mitigation

실험 fault라면 ConfigMap 값을 0으로 복구하고 Deployment를 restart한다. 새 release가 원인이면 실패 증거를 보존한 뒤 rollback runbook을 실행한다. 자원 압박이면 부하를 중단하고 원인을 확인한다.

## Recovery check

5xx 비율이 1% 미만으로 돌아오고 경보가 resolved되며 smoke test가 통과하는지 확인한다.

## Escalation

5분 내 오류율이 하락하지 않거나 모든 replica가 실패하거나 rollback도 실패하면 실험을 중단하고 deployment, event, log, 실행 SHA를 함께 보존해 인프라·애플리케이션 원인을 공동 조사한다.
