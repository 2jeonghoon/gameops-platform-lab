import stat
import subprocess
from pathlib import Path

import yaml


def test_deploy_workflow_is_gated_and_uses_short_lived_identity() -> None:
    path = Path(".github/workflows/deploy.yml")
    assert path.is_file(), "deploy workflow must exist"
    workflow = yaml.load(path.read_text(), Loader=yaml.BaseLoader)
    source = path.read_text()

    assert workflow["on"]["workflow_run"]["workflows"] == ["ci"]
    assert workflow["on"]["workflow_run"]["branches"] == ["main"]
    assert workflow["permissions"]["id-token"] == "write"
    assert "github.event.workflow_run.conclusion == 'success'" in workflow["jobs"]["deploy"]["if"]
    assert "github.event.workflow_run.head_sha" in source
    assert "game-session-api:${DEPLOY_SHA}" in source
    assert "aws ssm wait command-executed" in source
    assert 'remote_command="bash -lc' in source
    assert "git -C /opt/gameops/repository checkout --detach '${DEPLOY_SHA}'" in source
    assert "bash /opt/gameops/repository/scripts/deploy_on_instance.sh" in source
    assert "AWS_ACCESS_KEY_ID" not in source
    assert "AWS_SECRET_ACCESS_KEY" not in source


def test_instance_deploy_waits_for_rollout_and_preserves_failure_evidence() -> None:
    path = Path("scripts/deploy_on_instance.sh")
    source = path.read_text()

    assert path.stat().st_mode & stat.S_IXUSR
    assert "git checkout --detach" in source
    assert "scripts/render_manifests.sh" in source
    assert "rollout status" in source
    assert "/var/lib/gameops/evidence" in source
    assert "no automatic rollback performed" in source
    assert "scripts/smoke_test.sh" in source


def test_manifest_renderer_preserves_resources_and_pins_verified_image() -> None:
    image_ref = "ghcr.io/example/game-session-api:" + "a" * 40

    result = subprocess.run(
        ["bash", "scripts/render_manifests.sh", image_ref],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    resources = [item for item in yaml.safe_load_all(result.stdout) if item]
    assert {item["kind"] for item in resources} == {
        "ConfigMap",
        "Deployment",
        "Ingress",
        "Namespace",
        "Service",
    }
    deployment = next(item for item in resources if item["kind"] == "Deployment")
    assert deployment["spec"]["template"]["spec"]["containers"][0]["image"] == image_ref


def test_smoke_test_waits_only_for_safe_readiness_requests() -> None:
    source = Path("scripts/smoke_test.sh").read_text()

    assert 'wait_for_status 200 "${base_url}/healthz"' in source
    assert 'wait_for_status 200 "${base_url}/readyz"' in source
    assert source.index("wait_for_status 200") < source.index("expect_status 201")
