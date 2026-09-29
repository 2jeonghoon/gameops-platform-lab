import os
import subprocess
from pathlib import Path


def test_normal_profile_has_required_workflow_and_objectives() -> None:
    source = Path("load-test/normal.js").read_text()

    assert "BASE_URL" in source
    assert "http_req_failed" in source and "rate<0.01" in source
    assert "http_req_duration" in source and "p(95)<250" in source
    assert "http.post(" in source
    assert "`${baseUrl}/sessions`" in source
    assert "http.get(`${baseUrl}/sessions/${sessionId}`" in source
    assert "http.del(`${baseUrl}/sessions/${sessionId}`" in source


def test_degradation_profile_is_explicitly_expected_to_fail_thresholds() -> None:
    source = Path("load-test/degradation.js").read_text()

    assert "constant-arrival-rate" in source
    assert "expected threshold failure" in source.lower()
    assert "http_req_failed" in source
    assert "http_req_duration" in source


def test_fault_injection_rejects_invalid_values_before_kubectl(tmp_path: Path) -> None:
    marker = tmp_path / "k3s-called"
    fake_k3s = tmp_path / "k3s"
    fake_k3s.write_text(f"#!/usr/bin/env bash\ntouch '{marker}'\n")
    fake_k3s.chmod(0o755)
    environment = os.environ | {"PATH": f"{tmp_path}:{os.environ['PATH']}"}

    invalid_arguments = [
        ("-1", "0", "false"),
        ("10", "1.01", "false"),
        ("10", "-0.1", "false"),
        ("10", "0.1", "maybe"),
    ]
    for arguments in invalid_arguments:
        result = subprocess.run(
            ["bash", "scripts/inject_fault.sh", *arguments],
            capture_output=True,
            check=False,
            env=environment,
            text=True,
        )
        assert result.returncode == 2
        assert not marker.exists()


def test_incident_drafts_cannot_be_mistaken_for_executed_reports() -> None:
    required_sections = (
        "Hypothesis",
        "Preconditions and workload",
        "Reproduction",
        "Timeline",
        "Metrics, logs, events, and alerts",
        "Response",
        "Recovery",
        "Verification",
        "Root cause",
        "Prevention",
    )
    for name in (
        "001-pod-termination.md",
        "002-invalid-image.md",
        "003-load-degradation.md",
    ):
        source = (Path("docs/incidents") / name).read_text()
        assert "NOT YET EXECUTED" in source
        for section in required_sections:
            assert f"## {section}" in source
