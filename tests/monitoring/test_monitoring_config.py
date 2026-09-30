import json
from pathlib import Path

import yaml

MONITORING = Path("monitoring")


def _yaml(name: str) -> dict:
    return yaml.safe_load((MONITORING / name).read_text())


def _walk_mappings(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk_mappings(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_mappings(child)


def test_core_stack_is_single_replica_private_and_resource_bounded() -> None:
    values = _yaml("kube-prometheus-stack-values.yaml")

    assert values["prometheus"]["prometheusSpec"]["replicas"] == 1
    assert values["prometheus"]["prometheusSpec"]["retention"] == "2d"
    assert values["alertmanager"]["alertmanagerSpec"]["replicas"] == 1
    assert values["grafana"]["replicas"] == 1

    for component in ("prometheusSpec", "alertmanagerSpec"):
        owner = "prometheus" if component == "prometheusSpec" else "alertmanager"
        resources = values[owner][component]["resources"]
        assert resources["requests"] and resources["limits"]
    assert values["grafana"]["resources"]["requests"]
    assert values["grafana"]["resources"]["limits"]

    service_types = {
        mapping["type"]
        for mapping in _walk_mappings(values)
        if "type" in mapping and mapping["type"] in {"ClusterIP", "NodePort", "LoadBalancer"}
    }
    assert service_types <= {"ClusterIP"}


def test_loki_is_optional_single_binary_and_bounded() -> None:
    values = _yaml("loki-values.yaml")

    assert values["deploymentMode"] == "Monolithic"
    assert values["singleBinary"]["replicas"] == 1
    assert values["singleBinary"]["resources"]["requests"]
    assert values["singleBinary"]["resources"]["limits"]
    assert values["gateway"]["service"]["type"] == "ClusterIP"
    assert values["loki"]["limits_config"]["retention_period"] == "24h"


def test_service_monitor_selects_api_metrics_endpoint() -> None:
    monitor = _yaml("service-monitor.yaml")

    assert monitor["kind"] == "ServiceMonitor"
    assert monitor["metadata"]["namespace"] == "monitoring"
    assert monitor["spec"]["namespaceSelector"]["matchNames"] == ["gameops"]
    assert (
        monitor["spec"]["selector"]["matchLabels"]["app.kubernetes.io/name"] == "game-session-api"
    )
    assert monitor["spec"]["endpoints"] == [{"port": "http", "path": "/metrics", "interval": "15s"}]


def test_alert_thresholds_and_durations_match_experiments() -> None:
    manifest = _yaml("alerts.yaml")
    rules = {rule["alert"]: rule for group in manifest["spec"]["groups"] for rule in group["rules"]}

    assert set(rules) == {
        "GameSessionApiHighErrorRate",
        "GameSessionApiHighLatency",
        "GameSessionApiTargetDown",
        "GameSessionApiPodRestarted",
    }
    assert "> 0.05" in rules["GameSessionApiHighErrorRate"]["expr"]
    assert rules["GameSessionApiHighErrorRate"]["for"] == "2m"
    assert "histogram_quantile(0.95" in rules["GameSessionApiHighLatency"]["expr"]
    assert "> 0.25" in rules["GameSessionApiHighLatency"]["expr"]
    assert rules["GameSessionApiHighLatency"]["for"] == "5m"
    assert "up{" in rules["GameSessionApiTargetDown"]["expr"]
    assert rules["GameSessionApiTargetDown"]["for"] == "1m"
    assert (
        "increase(kube_pod_container_status_restarts_total"
        in rules["GameSessionApiPodRestarted"]["expr"]
    )


def test_dashboard_covers_service_and_resource_signals() -> None:
    dashboard = json.loads((MONITORING / "dashboards" / "game-session-api.json").read_text())
    expressions = "\n".join(
        target["expr"]
        for panel in dashboard["panels"]
        for target in panel.get("targets", [])
        if "expr" in target
    )

    required_fragments = (
        "gameops_http_requests_total",
        'status_class="5xx"',
        "histogram_quantile(0.50",
        "histogram_quantile(0.95",
        "histogram_quantile(0.99",
        "kube_pod_status_ready",
        "kube_pod_container_status_restarts_total",
        "container_cpu_usage_seconds_total",
        "container_memory_working_set_bytes",
        "gameops_active_sessions",
        "gameops_sessions_created_total",
        "gameops_sessions_deleted_total",
    )
    for fragment in required_fragments:
        assert fragment in expressions


def test_install_script_pins_charts_checks_health_and_gates_loki() -> None:
    source = Path("scripts/install_observability.sh").read_text()

    assert 'KUBE_PROMETHEUS_STACK_VERSION="91.8.0"' in source
    assert 'LOKI_VERSION="18.13.7"' in source
    assert 'ALLOY_VERSION="1.13.0"' in source
    assert 'export KUBECONFIG="/etc/rancher/k3s/k3s.yaml"' in source
    assert "MemAvailable" in source
    assert "api/v1/targets" in source
    assert "wait_for_prometheus_target" in source
    assert "api/datasources/uid/prometheus/health" in source
    assert "admin-password" in source
    assert "Loki installed" in source
    assert "Loki skipped" in source
