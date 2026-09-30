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
