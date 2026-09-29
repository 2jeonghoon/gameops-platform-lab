# Day 6 — 부하와 incident 실험 설계

## 구현

- 5 VU, 5분 동안 세션 생성·조회·삭제를 반복하는 정상 부하
- 80 iteration/s, 최대 150 VU로 경보 임계값을 넘기기 위한 열화 부하
- 5xx 1% 미만과 p95 250ms 미만 정상 threshold
- 실패 threshold를 숨기지 않는 열화 profile
- 범위를 먼저 검증한 뒤 ConfigMap을 변경하는 fault injection script
- Pod 삭제, 잘못된 image, load degradation incident 기록 양식

## 안전장치

fault script는 음수 delay, 0..1 밖 error rate, boolean이 아닌 readiness 값을 `kubectl` 호출 전에 거절한다. 변경 뒤 Deployment를 restart하고 rollout을 기다려 설정 적용 완료를 명시적으로 확인한다.

Incident 문서는 아직 실행하지 않은 계획을 완료 보고서처럼 보이게 하지 않도록 `NOT YET EXECUTED` 표시를 넣었다. Task 10에서 실제 UTC timeline, metric, log, event, alert, k6 결과를 얻은 경우에만 이를 교체한다.

열화 부하는 threshold 위반으로 k6가 non-zero 종료하는 것이 예상된 증거다. 이 결과를 CI 실패와 혼동하지 않도록 CI에서는 실행하지 않고 syntax와 archive 생성만 검증한다.
