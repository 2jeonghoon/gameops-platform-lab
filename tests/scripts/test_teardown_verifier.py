import json
import subprocess

import pytest

from scripts import verify_teardown


class FakeRunner:
    def __init__(self, *, instances=None, volumes=None, addresses=None, state=None, fail=None):
        self.instances = instances or []
        self.volumes = volumes or []
        self.addresses = addresses or []
        self.state = state or []
        self.fail = fail

    def __call__(self, command, **_kwargs):
        joined = " ".join(command)
        if self.fail and self.fail in joined:
            return subprocess.CompletedProcess(command, 1, "", "inventory unavailable")
        if "describe-instances" in command:
            payload = {"Reservations": [{"Instances": self.instances}] if self.instances else []}
        elif "describe-volumes" in command:
            payload = {"Volumes": self.volumes}
        elif "describe-addresses" in command:
            payload = {"Addresses": self.addresses}
        elif "state" in command and "list" in command:
            return subprocess.CompletedProcess(command, 0, "\n".join(self.state), "")
        else:
            raise AssertionError(f"unexpected command: {joined}")
        return subprocess.CompletedProcess(command, 0, json.dumps(payload), "")


@pytest.mark.parametrize(
    ("runner", "expected"),
    [
        (FakeRunner(instances=[{"InstanceId": "i-test"}]), "ec2_instances"),
        (FakeRunner(volumes=[{"VolumeId": "vol-test"}]), "ebs_volumes"),
        (FakeRunner(addresses=[{"AllocationId": "eipalloc-test"}]), "elastic_ips"),
        (FakeRunner(state=["aws_instance.k3s"]), "terraform_state"),
    ],
)
def test_main_fails_for_each_remaining_resource(runner, expected, tmp_path, capsys) -> None:
    result = verify_teardown.main(
        [
            "--project",
            "gameops-platform-lab",
            "--region",
            "ap-northeast-2",
            "--terraform-dir",
            str(tmp_path),
        ],
        runner=runner,
    )

    assert result == 1
    assert expected in capsys.readouterr().out


def test_main_succeeds_only_when_inventory_and_state_are_empty(tmp_path, capsys) -> None:
    result = verify_teardown.main(
        [
            "--project",
            "gameops-platform-lab",
            "--region",
            "ap-northeast-2",
            "--terraform-dir",
            str(tmp_path),
        ],
        runner=FakeRunner(),
    )

    assert result == 0
    output = capsys.readouterr().out
    assert "teardown verified" in output
    assert "ec2_instances: 0" in output


def test_main_fails_closed_when_inventory_query_errors(tmp_path, capsys) -> None:
    result = verify_teardown.main(
        [
            "--project",
            "gameops-platform-lab",
            "--region",
            "ap-northeast-2",
            "--terraform-dir",
            str(tmp_path),
        ],
        runner=FakeRunner(fail="describe-volumes"),
    )

    assert result == 2
    assert "inventory unavailable" in capsys.readouterr().err
