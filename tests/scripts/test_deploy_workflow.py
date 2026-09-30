import stat
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
    assert "AWS_ACCESS_KEY_ID" not in source
    assert "AWS_SECRET_ACCESS_KEY" not in source


def test_instance_deploy_waits_for_rollout_and_preserves_failure_evidence() -> None:
    path = Path("scripts/deploy_on_instance.sh")
    source = path.read_text()

    assert path.stat().st_mode & stat.S_IXUSR
    assert "git checkout --detach" in source
    assert "kubectl set image --local" in source
    assert "rollout status" in source
    assert "/var/lib/gameops/evidence" in source
    assert "no automatic rollback performed" in source
    assert "scripts/smoke_test.sh" in source
