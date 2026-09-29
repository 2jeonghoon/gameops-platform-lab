# Incident experiment 002 — Invalid image rollout

> **NOT YET EXECUTED** — Task 10에서 실제 시각과 측정값으로 이 표시와 placeholder를 교체하기 전까지 계획서다.

## Hypothesis

존재하지 않는 image tag를 적용하면 새 Pod가 ImagePullBackOff가 되지만 `maxUnavailable: 0` 때문에 기존 Ready Pod는 유지된다. rollout은 실패하고 운영자가 증거를 확인한 뒤 명시적으로 undo할 수 있다.

## Preconditions and workload

- 현재 Deployment와 image SHA 기록
- 정상 부하 실행 중
- rollout history와 `/var/lib/gameops/evidence` 보존

## Reproduction

```bash
sudo k3s kubectl -n gameops set image deployment/game-session-api \
  api=ghcr.io/OWNER/REPOSITORY/game-session-api:does-not-exist
sudo k3s kubectl -n gameops rollout status deployment/game-session-api --timeout=180s
```

## Timeline

NOT YET EXECUTED. image 변경, pull failure, rollout timeout, 대응, rollback, 정상화 UTC 시각을 기록한다.

## Metrics, logs, events, and alerts

NOT YET EXECUTED. ImagePullBackOff event, Ready replica, 요청 실패율, latency, alert 상태, rollout 출력을 첨부한다.

## Response

NOT YET EXECUTED. 실패 Pod와 event를 보존하고 현재/이전 image를 확인한다.

## Recovery

```bash
sudo bash scripts/rollback.sh gameops game-session-api
```

NOT YET EXECUTED. undo된 revision과 완료 시각을 기록한다.

## Verification

NOT YET EXECUTED. rollout status, 두 Ready Pod, smoke test, 정상 부하 threshold를 기록한다.

## Root cause

NOT YET EXECUTED. 의도적인 nonexistent immutable tag와 실제 failure mode를 작성한다.

## Prevention

NOT YET EXECUTED. registry 존재 확인, admission policy, progressive delivery 중 이 규모에 적합한 개선점을 기록한다.
