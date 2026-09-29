# High latency runbook

## Trigger

`GameSessionApiHighLatency`: 최근 5분 요청의 p95가 250ms를 초과한 상태가 5분 지속된다.

## Impact

요청 timeout, queue 증가, client retry가 발생할 수 있고 오류율 상승으로 이어질 수 있다.

## Queries

```promql
histogram_quantile(0.95, sum by (le) (rate(gameops_http_request_duration_seconds_bucket[5m])))
sum by (pod) (rate(container_cpu_usage_seconds_total{namespace="gameops",container="api"}[5m]))
sum by (pod) (container_memory_working_set_bytes{namespace="gameops",container="api"})
```

## Diagnosis

1. p50/p95/p99을 비교해 전체 지연인지 tail latency인지 구분한다.
2. `FAULT_DELAY_MS`, 요청률, CPU throttling, memory pressure, restart, node 상태를 같은 시간축에서 비교한다.
3. 특정 Pod에만 집중되면 해당 Pod log와 event를 확인한다.

## Mitigation

실험 지연값을 0으로 복구하고 rollout을 기다린다. 과부하면 load generator를 중단한다. 새 release 이후 시작됐다면 증거를 보존하고 rollback한다. 단일 노드에서 관측 stack이 경쟁한다면 Loki를 먼저 제거하고 재측정한다.

## Recovery check

p95가 250ms 아래로 내려가 10분 유지되고, 오류율이 1% 미만이며 smoke test가 통과하는지 확인한다.

## Escalation

부하와 fault를 제거한 뒤에도 10분 이상 지속되거나 node memory pressure/eviction이 발생하면 실험을 중단하고 node·Pod resource 자료와 profile을 보존한다.
