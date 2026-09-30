#!/usr/bin/env bash
set -euo pipefail

KUBE_PROMETHEUS_STACK_VERSION="91.8.0"
LOKI_VERSION="18.13.7"
ALLOY_VERSION="1.13.0"
MONITORING_NAMESPACE="monitoring"
LOKI_MIN_AVAILABLE_KIB=1572864
export KUBECONFIG="/etc/rancher/k3s/k3s.yaml"

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
port_forward_pid=""

kubectl() {
  k3s kubectl "$@"
}

stop_port_forward() {
  if [[ -n "${port_forward_pid}" ]]; then
    kill "${port_forward_pid}" 2>/dev/null || true
    wait "${port_forward_pid}" 2>/dev/null || true
    port_forward_pid=""
  fi
}
trap stop_port_forward EXIT

wait_for_url() {
  local url="$1"
  local attempts="${2:-60}"
  local attempt
  for ((attempt = 1; attempt <= attempts; attempt++)); do
    if curl --fail --silent --show-error "${url}" >/dev/null 2>&1; then
      return 0
    fi
    sleep 2
  done
  echo "timed out waiting for ${url}" >&2
  return 1
}

wait_for_prometheus_target() {
  local attempts="${1:-60}"
  local attempt
  local targets_json
  for ((attempt = 1; attempt <= attempts; attempt++)); do
    targets_json="$(curl --fail --silent --show-error \
      http://127.0.0.1:19090/api/v1/targets 2>/dev/null || true)"
    if python3 -c '
import json
import sys

try:
    targets = json.load(sys.stdin)["data"]["activeTargets"]
except (KeyError, json.JSONDecodeError):
    raise SystemExit(1)
selected = [target for target in targets if target.get("labels", {}).get("service") == "game-session-api"]
raise SystemExit(0 if len(selected) == 2 and all(target.get("health") == "up" for target in selected) else 1)
' <<<"${targets_json}"; then
      return 0
    fi
    sleep 2
  done
  echo "timed out waiting for two healthy game-session-api Prometheus targets" >&2
  return 1
}

kubectl create namespace "${MONITORING_NAMESPACE}" --dry-run=client -o yaml \
  | kubectl apply -f -

helm repo add prometheus-community https://prometheus-community.github.io/helm-charts --force-update
helm repo add grafana-community https://grafana-community.github.io/helm-charts --force-update
helm repo add grafana https://grafana.github.io/helm-charts --force-update
helm repo update

helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
  --namespace "${MONITORING_NAMESPACE}" \
  --version "${KUBE_PROMETHEUS_STACK_VERSION}" \
  --values "${repo_root}/monitoring/kube-prometheus-stack-values.yaml" \
  --wait --timeout 10m

kubectl apply -f "${repo_root}/monitoring/service-monitor.yaml"
kubectl apply -f "${repo_root}/monitoring/alerts.yaml"
kubectl -n "${MONITORING_NAMESPACE}" create configmap game-session-api-dashboard \
  --from-file="game-session-api.json=${repo_root}/monitoring/dashboards/game-session-api.json" \
  --dry-run=client -o yaml \
  | kubectl label --local -f - grafana_dashboard=1 -o yaml \
  | kubectl apply -f -

kubectl -n "${MONITORING_NAMESPACE}" wait --for=condition=Ready pod \
  -l app.kubernetes.io/instance=monitoring --timeout=300s

kubectl -n "${MONITORING_NAMESPACE}" port-forward \
  service/monitoring-kube-prometheus-prometheus 19090:9090 \
  >/tmp/gameops-prometheus-port-forward.log 2>&1 &
port_forward_pid=$!
wait_for_url http://127.0.0.1:19090/-/ready
wait_for_prometheus_target
stop_port_forward
echo "Prometheus target is healthy"

grafana_password="$(kubectl -n "${MONITORING_NAMESPACE}" get secret monitoring-grafana \
  -o jsonpath='{.data.admin-password}' | base64 --decode)"
kubectl -n "${MONITORING_NAMESPACE}" port-forward service/monitoring-grafana 13000:80 \
  >/tmp/gameops-grafana-port-forward.log 2>&1 &
port_forward_pid=$!
wait_for_url http://127.0.0.1:13000/api/health
curl --fail --silent --show-error --user "admin:${grafana_password}" \
  http://127.0.0.1:13000/api/datasources/uid/prometheus/health >/dev/null
stop_port_forward
unset grafana_password
echo "Grafana Prometheus data source is healthy"

available_kib="$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)"
if [[ "${available_kib}" -ge "${LOKI_MIN_AVAILABLE_KIB}" ]]; then
  helm upgrade --install loki grafana-community/loki \
    --namespace "${MONITORING_NAMESPACE}" \
    --version "${LOKI_VERSION}" \
    --values "${repo_root}/monitoring/loki-values.yaml" \
    --wait --timeout 10m
  helm upgrade --install alloy grafana/alloy \
    --namespace "${MONITORING_NAMESPACE}" \
    --version "${ALLOY_VERSION}" \
    --values "${repo_root}/monitoring/alloy-values.yaml" \
    --wait --timeout 5m
  kubectl -n "${MONITORING_NAMESPACE}" wait --for=condition=Ready pod \
    -l app.kubernetes.io/instance=loki --timeout=300s
  kubectl -n "${MONITORING_NAMESPACE}" wait --for=condition=Ready pod \
    -l app.kubernetes.io/instance=alloy --timeout=300s
  echo "Loki installed with Alloy log collection (MemAvailable=${available_kib} KiB)"
else
  echo "Loki skipped: MemAvailable=${available_kib} KiB is below ${LOKI_MIN_AVAILABLE_KIB} KiB"
fi
