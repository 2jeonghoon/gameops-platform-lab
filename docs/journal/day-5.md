# Day 5 — 관측 가능성과 경보

## 구현

- 제한된 resource와 짧은 retention을 가진 단일 replica Prometheus, Grafana, Alertmanager
- `/metrics`를 15초마다 수집하는 ServiceMonitor와 네 가지 alert rule
- throughput, 5xx, latency 분위수, Pod, resource, session dashboard
- 메모리 여유가 있을 때만 설치되는 Loki 단일 바이너리와 Alloy log 수집
- 설치 후 Prometheus target 및 Grafana datasource health 검사
- error, latency, target down 대응 runbook

## 설계 판단

4GiB 단일 노드에서 관측 stack 자체가 실험 대상을 압박하지 않도록 모든 핵심 component를 한 replica로 제한했다. Prometheus retention은 2일, Loki retention은 24시간이다. Loki는 필수 metric 경로보다 우선순위가 낮으므로 설치 시 가용 메모리가 1.5GiB 미만이면 명시적으로 생략한다.

경보는 단순 임계값뿐 아니라 지속 시간을 둔다. 짧은 spike를 곧바로 incident로 판단하지 않으면서도, 의도적으로 주입한 오류·지연·target failure가 pending에서 firing으로 전환되는 과정을 관찰할 수 있다.

최신 chart는 기본적으로 Loki simple-scalable target을 각각 세 replica로 설정했다. 처음 `helm template`에서 Monolithic replica와 충돌하는 오류를 확인했고, read/write/backend를 0으로 명시해 단일 노드 의도를 재현 가능하게 만들었다.

## 검증

```bash
uv run pytest tests/monitoring/test_monitoring_config.py -v
shellcheck scripts/install_observability.sh
helm template monitoring prometheus-community/kube-prometheus-stack --version 91.8.0 -f monitoring/kube-prometheus-stack-values.yaml
helm template loki grafana-community/loki --version 18.13.7 -f monitoring/loki-values.yaml
helm template alloy grafana/alloy --version 1.13.0 -f monitoring/alloy-values.yaml
```

## Live result — 2026-09-30

Helm은 SSM 비대화형 shell에서 kubeconfig를 자동으로 찾지 못해 `KUBECONFIG=/etc/rancher/k3s/k3s.yaml`을 명시했다. ServiceMonitor 생성 직후 target discovery가 비동기적으로 늦어질 수 있어 API endpoint 두 개가 모두 `up`일 때까지 제한 폴링하도록 수정했다.

Prometheus target 2개, Grafana datasource와 8개 dashboard panel, Alertmanager, monitoring Pod 6개 Ready를 확인했다. Loki/Alloy는 설치 시 가용 메모리가 약 1.07GiB로 안전 기준 1.5GiB 미만이라 생략했고 Kubernetes logs를 fallback으로 선택했다.
