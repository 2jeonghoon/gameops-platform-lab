# 관측 stack 설치와 사용

## 설치

애플리케이션 배포 후 EC2의 repository root에서 실행한다.

```bash
sudo bash scripts/install_observability.sh
```

script는 고정된 chart 버전으로 Prometheus, Grafana, Alertmanager를 설치하고 `ServiceMonitor`, alert rule, dashboard를 적용한다. 모든 Service는 `ClusterIP`이고 외부 ingress를 만들지 않는다. 설치 시 생성된 Grafana Secret에서 비밀번호를 읽어 Prometheus datasource health를 검사하지만 비밀번호를 출력하거나 repository에 저장하지 않는다.

Prometheus stack 설치 후 호스트의 `/proc/meminfo`에서 `MemAvailable`이 1.5GiB 이상일 때만 Loki와 Alloy를 설치한다. 결과는 반드시 `Loki installed` 또는 `Loki skipped`로 log에 남는다. 이 gate는 순간값이므로 이후에도 Pod memory와 eviction을 관찰한다.

## 상태 확인

```bash
sudo k3s kubectl -n monitoring get pods,service
sudo k3s kubectl -n monitoring get servicemonitor,prometheusrule
sudo k3s kubectl -n monitoring get prometheusrule game-session-api -o yaml
```

Prometheus target은 `game-session-api` Service의 두 endpoint가 모두 `up`인지 확인한다. 설치 script도 같은 검사를 수행한다.

## 비공개 Grafana 접속

첫 번째 SSM Session Manager shell에서 Grafana를 EC2 loopback에 연결한다.

```bash
sudo k3s kubectl -n monitoring port-forward --address=127.0.0.1 \
  service/monitoring-grafana 3000:80
```

두 번째 로컬 terminal에서 SSM port forwarding session을 연다.

```bash
aws ssm start-session \
  --target INSTANCE_ID \
  --document-name AWS-StartPortForwardingSession \
  --parameters '{"portNumber":["3000"],"localPortNumber":["3000"]}'
```

브라우저에서 `http://127.0.0.1:3000`을 연다. 사용자는 `admin`이고 비밀번호는 shell에서 다음 명령으로 조회한다. 화면 공유나 기록에 비밀번호를 남기지 않는다.

```bash
sudo k3s kubectl -n monitoring get secret monitoring-grafana \
  -o jsonpath='{.data.admin-password}' | base64 --decode; echo
```

`Game Session API` dashboard에서 throughput, 5xx 비율, p50/p95/p99, Pod readiness/restart, CPU/memory, session 수를 확인한다. Alerting 화면에서는 rule의 pending/firing/resolved 상태를 확인한다.

## Log 조회

Loki가 설치되었다면 Grafana에 Loki datasource `http://loki-gateway.monitoring.svc.cluster.local`을 추가하고 Explore에서 다음 LogQL을 실행한다.

```text
{namespace="gameops", app="game-session-api"}
```

Loki가 생략되었거나 불건전하면 Kubernetes log를 사용한다.

```bash
sudo k3s kubectl -n gameops logs deployment/game-session-api --all-pods=true --since=15m
```
