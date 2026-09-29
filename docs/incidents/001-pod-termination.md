# Incident experiment 001 — Pod termination

> **NOT YET EXECUTED** — Task 10에서 실제 시각과 측정값으로 이 표시와 placeholder를 교체하기 전까지 계획서다.

## Hypothesis

정상 부하 중 API Pod 하나를 삭제해도 남은 replica가 요청을 처리하고 Kubernetes가 새 Pod를 생성한다. 짧은 tail latency 변화는 있을 수 있지만 5xx 비율은 실험 목표 1% 미만을 유지할 것으로 예상한다.

## Preconditions and workload

- Deployment replica 2, 두 Pod 모두 Ready
- 정상 fault 설정: delay 0, error rate 0, readiness false
- `k6 run -e BASE_URL=http://PUBLIC_IPV4 load-test/normal.js`
- Grafana dashboard와 Alertmanager 상태 기록 준비

## Reproduction

```bash
sudo k3s kubectl -n gameops get pods -l app.kubernetes.io/name=game-session-api
sudo k3s kubectl -n gameops delete pod POD_NAME
```

## Timeline

NOT YET EXECUTED. 시작, 삭제, 감지, replacement 생성, Ready, 안정화 UTC 시각을 기록한다.

## Metrics, logs, events, and alerts

NOT YET EXECUTED. 요청률, 5xx, p95/p99, Ready replica, restart, Pod event, k6 결과, alert 상태 전이를 첨부한다.

## Response

NOT YET EXECUTED. 자동 self-healing을 관찰하며 replica가 복구되지 않을 때만 scheduler/node 상태를 조사한다.

## Recovery

NOT YET EXECUTED. 새 Pod가 Ready가 되고 replica 2가 복원된 시각을 기록한다.

## Verification

NOT YET EXECUTED. 정상 부하 threshold, smoke test, Deployment rollout 상태를 기록한다.

## Root cause

NOT YET EXECUTED. 의도적으로 실행한 Pod deletion과 실제 관찰 결과를 구분해 작성한다.

## Prevention

NOT YET EXECUTED. probe, replica, resource, topology 설계에서 얻은 개선점을 작성한다.
