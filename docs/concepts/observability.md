# 관측 가능성 기초

## 세 가지 신호

- **Metrics**는 시간에 따른 수치다. 요청률, 오류율, 지연시간, restart 수처럼 경향과 임계값 판단에 적합하다. 이 프로젝트는 Prometheus에 저장하고 Grafana에서 시각화한다.
- **Logs**는 개별 사건의 문맥이다. 어떤 Pod에서 어떤 오류가 발생했는지 상세 원인을 찾는 데 적합하다. 메모리 여유가 있으면 Alloy가 Kubernetes API로 Pod log를 수집해 Loki로 보낸다. Loki를 생략하면 `kubectl logs`가 fallback이다.
- **Traces**는 한 요청이 여러 서비스와 구간을 통과한 경로다. 분산 시스템의 병목을 연결해 보여 주지만, 단일 API인 이 실험의 범위에는 포함하지 않았다.

한 신호가 다른 신호를 대체하지 않는다. Metric 경보로 이상을 발견하고, dashboard로 범위를 좁힌 뒤, log로 원인을 확인하는 흐름을 사용한다.

## Prometheus pull 방식

Prometheus는 `ServiceMonitor`를 발견하고 15초마다 API의 `/metrics`를 직접 scrape한다. 애플리케이션이 monitoring 서버 주소를 알 필요가 없고, Prometheus의 target 화면에서 각 scrape의 성공 여부를 확인할 수 있다. `up{service="game-session-api"}`가 0이면 애플리케이션 오류뿐 아니라 Service selector, endpoint, network, scrape 설정 문제도 후보가 된다.

Metric label은 `method`, 정규화된 `route`, `status_class`처럼 가능한 값이 제한된 항목만 사용한다. session ID 같은 무한한 값은 time series 수와 메모리 사용량을 폭증시키므로 label로 사용하지 않는다.

## Histogram과 분위수

요청 지연시간 histogram은 각 bucket 이하의 관측 수를 누적한다. PromQL의 `histogram_quantile(0.95, sum by (le) (rate(..._bucket[5m])))`은 최근 5분 요청 분포에서 p95를 근사한다. p95 250ms는 요청의 약 95%가 250ms 안에 끝난다는 뜻이지, 모든 요청의 상한이 250ms라는 뜻은 아니다. 표본이 적거나 bucket 경계가 거칠면 근사 오차가 커진다.

## 경보 상태

- **Pending**: 식이 참이지만 `for` 시간이 아직 지나지 않은 상태다. 짧은 잡음을 걸러낸다.
- **Firing**: 식이 `for` 시간 동안 계속 참이어서 대응이 필요한 상태다.
- **Resolved**: 식이 다시 거짓이 되어 활성 경보가 해제된 상태다.

Alertmanager는 상태와 전달을 관리한다. 이 포트폴리오에서는 외부 paging 연동보다 pending→firing→resolved 전이와 대응 증거를 확인하는 데 초점을 둔다.

## 실험 목표와 생산 SLO

정상 부하에서 5xx 비율 1% 미만, p95 250ms 미만은 통제된 환경의 **실험 목표**다. 생산 SLO는 실제 사용자 영향, 측정 지점, rolling window, 허용 error budget, 제외 조건, 조직의 대응 약속까지 합의한 목표다. 짧은 단일 노드 실험 결과를 생산 신뢰성 약속처럼 표현하지 않는다.
