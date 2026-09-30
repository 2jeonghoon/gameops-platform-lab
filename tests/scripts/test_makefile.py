import os
import subprocess
from pathlib import Path


def test_terraform_check_initializes_plugins_before_validation(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    call_log = tmp_path / "terraform-calls.log"
    init_marker = tmp_path / "terraform-initialized"
    fake_terraform = bin_dir / "terraform"
    fake_terraform.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
printf '%s\\n' "$*" >>"${FAKE_TERRAFORM_CALL_LOG}"
case "$*" in
  *" init "*|*" init") touch "${FAKE_TERRAFORM_INIT_MARKER}" ;;
  *" validate"|*" test") test -f "${FAKE_TERRAFORM_INIT_MARKER}" ;;
esac
"""
    )
    fake_terraform.chmod(0o755)

    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env['PATH']}"
    env["FAKE_TERRAFORM_CALL_LOG"] = str(call_log)
    env["FAKE_TERRAFORM_INIT_MARKER"] = str(init_marker)

    result = subprocess.run(
        ["make", "terraform-check"],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    calls = call_log.read_text().splitlines()
    init_index = next(index for index, call in enumerate(calls) if " init" in call)
    validate_index = next(index for index, call in enumerate(calls) if " validate" in call)
    assert init_index < validate_index


def test_kubernetes_check_streams_rendered_manifests_to_pinned_container(
    tmp_path: Path,
) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    rendered_input = tmp_path / "rendered-input.yaml"

    fake_kubectl = bin_dir / "kubectl"
    fake_kubectl.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' 'apiVersion: v1' 'kind: ConfigMap' 'metadata:' '  name: rendered-marker'
"""
    )
    fake_kubectl.chmod(0o755)

    fake_docker = bin_dir / "docker"
    fake_docker.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
[[ "$*" == *"ghcr.io/yannh/kubeconform:v0.8.0"* ]]
cat >"${FAKE_RENDERED_INPUT}"
grep -q 'name: rendered-marker' "${FAKE_RENDERED_INPUT}"
"""
    )
    fake_docker.chmod(0o755)

    fake_uv = bin_dir / "uv"
    fake_uv.write_text("#!/usr/bin/env bash\nexit 0\n")
    fake_uv.chmod(0o755)

    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env['PATH']}"
    env["FAKE_RENDERED_INPUT"] = str(rendered_input)

    result = subprocess.run(
        ["make", "kubernetes-check"],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "name: rendered-marker" in rendered_input.read_text()
