# Target down runbook

## Trigger

`GameSessionApiTargetDown`: `up{service="game-session-api"} == 0` 상태가 1분 지속된다.

## Impact

Prometheus가 API metric을 수집하지 못한다. 실제 서비스 중단일 수도 있고 monitoring 경로만 끊긴 것일 수도 있어 사용자 요청 경로를 별도로 확인해야 한다.

## Queries

```promql
up{service="game-session-api"}
kube_pod_status_ready{namespace="gameops",condition="true"}
increase(kube_pod_container_status_restarts_total{namespace="gameops",container="api"}[10m])
```

## Diagnosis

1. 외부 `/healthz`와 `/readyz`를 호출해 사용자 경로 영향 여부를 구분한다.
2. Service selector, EndpointSlice, Pod readiness, `/metrics` 응답을 확인한다.
3. ServiceMonitor selector와 Prometheus target의 last error를 확인한다.
4. image pull, scheduling, OOMKilled, node NotReady event를 확인한다.

## Mitigation

잘못된 readiness fault는 원복하고, selector나 port 불일치는 선언 파일을 수정해 검증 후 배포한다. 잘못된 image rollout이면 rollback한다. Prometheus만 불건전하면 API를 불필요하게 재시작하지 말고 monitoring Pod를 조사한다.

## Recovery check

두 API endpoint가 모두 Prometheus에서 `up=1`이고 외부 smoke test가 통과하며 경보가 resolved되는지 확인한다.

## Escalation

모든 endpoint가 5분 이상 down이거나 node가 NotReady이거나 rollback 후에도 복구되지 않으면 새 변경을 중단하고 cluster와 EC2 계층까지 조사한다.
