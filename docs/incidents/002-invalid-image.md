# Incident experiment 002 — Invalid image rollout

## Hypothesis

존재하지 않는 image tag를 적용하면 새 Pod는 image pull에 실패하지만 `maxUnavailable: 0` 때문에 기존 Ready Pod 두 개가 서비스를 계속한다. 실패 증거를 확인한 뒤 명시적 rollback으로 정상 revision을 복원할 수 있어야 한다.

## Preconditions and workload

- 2026-09-30 실행
- 정상 SHA image와 Ready replica 2 기록
- k6 2.3.0, 5 VU, 5분 정상 부하 실행
- `/var/lib/gameops/evidence`에 원격 실행 로그 보존

## Reproduction

SSM Run Command로 `game-session-api:does-not-exist-incident`를 적용하고 rollout을 60초로 제한했다. public `main`에 고의 실패 commit을 만들지 않기 위해 이 실험은 CI/CD workflow가 아니라 동일한 클러스터 배포 명령 경계에서 실행했다.

## Timeline (UTC)

- 07:14:49.269 — 존재하지 않는 image rollout 시작
- 07:15:49.627 — rollout timeout과 exit 1 확인
- 07:15:50.379 — 실패 상태에서 smoke test 통과
- 07:15:50.381 — 운영자 rollback 시작
- 07:15:51.219 — 정상 revision 복원과 smoke test 완료, 약 0.84초 경과
- 07:17:45 — 전체 5분 부하 완료

## Metrics, logs, events, and alerts

- 새 Pod: `ErrImagePull` 이후 `ImagePullBackOff`
- event: registry reference `not found`, pull backoff 확인
- 실패 중 Ready replica: 2, 기존 정상 Pod 두 개 계속 Running
- HTTP 요청: 19,032, 63.40 req/s
- HTTP 실패: 0건, 0.00%
- latency: 평균 11.24ms, p95 14.92ms, 최대 344.08ms
- iteration: 6,344, interrupted 0

## Response

자동 rollback하지 않고 60초 동안 실패 Pod와 event를 보존했다. 정상 Pod가 계속 요청을 처리하는지 전체 API smoke flow로 확인한 뒤 rollback runbook을 실행했다.

## Recovery

`scripts/rollback.sh gameops game-session-api`가 `kubectl rollout undo`, rollout wait, smoke test를 순서대로 실행했다. 복구 image SHA는 실험 전 SHA와 일치했고 Ready replica는 2였다.

## Verification

실패 중과 rollback 후 모두 health, readiness, 세션 생성·조회·삭제가 통과했다. 전체 5분 k6 threshold도 실패율 1% 미만과 p95 250ms 미만을 만족했다.

## Root cause

의도적으로 존재하지 않는 immutable tag를 지정해 registry가 manifest를 찾지 못했다. Kubernetes는 새 replica를 Ready로 만들지 못했지만 rolling update 정책이 기존 replica를 제거하지 않았다.

## Prevention

- CI 성공 SHA와 container tag를 동일하게 유지하고 `latest`를 사용하지 않는다.
- 배포 전 registry manifest 존재 검사를 추가하는 방안을 우선 검토한다.
- 실패 시 자동 rollback으로 증거를 지우지 않고 event와 image를 먼저 보존한다.
- 규모가 커지면 admission policy와 progressive delivery를 추가한다.
