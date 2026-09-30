import subprocess
from pathlib import Path
from typing import Any

import yaml


def rendered_resources() -> dict[tuple[str, str], dict[str, Any]]:
    base = Path("k8s/base")
    assert base.is_dir(), "k8s/base must exist"
    result = subprocess.run(
        ["kubectl", "kustomize", str(base)],
        check=True,
        capture_output=True,
        text=True,
    )
    documents = [item for item in yaml.safe_load_all(result.stdout) if item]
    return {(item["kind"], item["metadata"]["name"]): item for item in documents}


def test_deployment_has_resilient_runtime_contract() -> None:
    deployment = rendered_resources()[("Deployment", "game-session-api")]
    spec = deployment["spec"]
    pod = spec["template"]["spec"]
    container = pod["containers"][0]

    assert spec["replicas"] == 2
    assert spec["strategy"]["rollingUpdate"] == {"maxUnavailable": 0, "maxSurge": 1}
    assert not container["image"].endswith(":latest")
    assert container["image"].endswith(":REPLACE_WITH_GIT_SHA")
    assert container["startupProbe"]["httpGet"]["path"] == "/healthz"
    assert container["livenessProbe"]["httpGet"]["path"] == "/healthz"
    assert container["readinessProbe"]["httpGet"]["path"] == "/readyz"
    assert container["resources"] == {
        "requests": {"cpu": "100m", "memory": "128Mi"},
        "limits": {"cpu": "500m", "memory": "384Mi"},
    }


def test_service_ingress_and_fault_defaults_are_private_and_bounded() -> None:
    resources = rendered_resources()
    service = resources[("Service", "game-session-api")]
    ingress = resources[("Ingress", "game-session-api")]
    config = resources[("ConfigMap", "game-session-api")]

    assert service["spec"]["type"] == "ClusterIP"
    assert service["spec"]["sessionAffinity"] == "ClientIP"
    assert service["spec"]["sessionAffinityConfig"] == {"clientIP": {"timeoutSeconds": 10800}}
    assert service["spec"]["ports"] == [{"name": "http", "port": 8000, "targetPort": "http"}]
    assert ingress["spec"]["rules"][0]["http"]["paths"][0]["path"] == "/"
    assert config["data"] == {
        "FAULT_DELAY_MS": "0",
        "FAULT_ERROR_RATE": "0",
        "READINESS_FAIL": "false",
    }
