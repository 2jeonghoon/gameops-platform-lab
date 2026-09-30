# Incident experiment 001 — Pod termination

## Hypothesis

정상 부하 중 API Pod 하나를 삭제해도 남은 replica가 요청을 처리하고 Kubernetes가 replacement를 생성한다. 실험 목표는 HTTP 실패율 1% 미만과 p95 250ms 미만이다.

## Preconditions and workload

- 2026-09-30 실행, Deployment replica 2와 두 Pod Ready 확인
- fault 설정: delay 0ms, error rate 0, readiness false
- k6 2.3.0, 5 VU, 5분, 세션 생성·조회·삭제 반복
- Prometheus API 타깃 2개 `up`, Grafana 대시보드 8개 패널 로드 확인

## Reproduction

정상 k6 부하를 시작한 뒤 SSM Run Command로 label selector에서 Pod 하나를 선택해 `kubectl delete pod --wait=false`를 실행했다. 인스턴스 ID, Pod suffix, 공인 IP, SSM command ID는 공개 문서에서 제거했다.

## Timeline (UTC)

- 07:03:06.483 — Pod 삭제 요청
- 07:03:08.569 — 삭제된 Pod가 API에서 사라짐, 2.086초 경과
- 07:03:09.059 — replacement Pod 관측, 2.576초 경과
- 07:03:13.584 — 두 Pod 모두 Ready, 7.101초 경과
- 07:06:31 — 5분 부하와 요약 파일 생성 완료

## Metrics, logs, events, and alerts

- HTTP 요청: 19,065, 63.53 req/s
- HTTP 실패: 0건, 0.00%
- latency: 평균 11.17ms, p95 16.00ms, 최대 186.43ms
- iteration: 6,355, interrupted 0
- Kubernetes event: `Killing`, `SuccessfulCreate`, image already present, `Created`, `Started` 확인
- 새 Pod의 첫 startup probe는 container listen 전에 한 차례 connection refused였고 이후 Ready가 됐다.
- 실험 후 네 alert rule은 모두 inactive였다. Pod 삭제는 container restart가 아니므로 restart alert가 발생하지 않은 것이 기대 결과다.

## Response

자동 self-healing을 관찰했고 수동 개입은 하지 않았다. replacement가 180초 안에 Ready가 되지 않을 때만 node, scheduler, image pull 상태를 조사하는 조건이었다.

## Recovery

Deployment가 약 7.1초 안에 Ready replica 2를 복원했다. 별도 rollback은 필요하지 않았다.

## Verification

k6 threshold는 모두 통과했다. 기준선(p95 15.84ms, 실패 0%)과 비교해 p95 증가는 약 0.16ms였고 실패율 변화는 없었다. 실험 종료 후 외부 세션 생성·조회·삭제 smoke test도 통과했다.

## Root cause

장애 원인은 의도적인 Pod 삭제다. 서비스 중단이 발생하지 않은 직접 요인은 두 replica, `maxUnavailable: 0`, readiness probe, Kubernetes ReplicaSet의 replacement 생성이다.

## Prevention and limitations

- readiness/startup probe와 최소 두 replica를 유지한다.
- Pod replacement 시간과 Ready replica 수를 계속 경보·대시보드에서 추적한다.
- 현재 세션 저장소는 Pod 메모리이므로 삭제된 Pod의 기존 세션은 사라질 수 있다. 이번 짧은 요청 생명주기에서는 실패가 없었지만 운영 설계는 Redis, DynamoDB 또는 데이터베이스 같은 공유 저장소가 필요하다.
