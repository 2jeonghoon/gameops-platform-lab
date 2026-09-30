#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

Runner = Callable[..., subprocess.CompletedProcess[str]]


def _run_json(command: list[str], runner: Runner) -> dict:
    result = runner(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"command failed: {' '.join(command)}")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise RuntimeError(f"invalid JSON from {' '.join(command)}") from error


def collect_remaining(
    project: str,
    region: str,
    terraform_dir: Path,
    runner: Runner = subprocess.run,
) -> dict[str, list[str]]:
    tag_filter = f"Name=tag:Project,Values={project}"
    aws_base = ["aws", "--region", region, "ec2"]

    instances_data = _run_json(
        [
            *aws_base,
            "describe-instances",
            "--filters",
            tag_filter,
            "Name=instance-state-name,Values=pending,running,stopping,stopped",
            "--output",
            "json",
        ],
        runner,
    )
    volumes_data = _run_json(
        [
            *aws_base,
            "describe-volumes",
            "--filters",
            tag_filter,
            "--output",
            "json",
        ],
        runner,
    )
    addresses_data = _run_json(
        [
            *aws_base,
            "describe-addresses",
            "--filters",
            tag_filter,
            "--output",
            "json",
        ],
        runner,
    )

    state_result = runner(
        ["terraform", f"-chdir={terraform_dir}", "state", "list"],
        capture_output=True,
        text=True,
        check=False,
    )
    if state_result.returncode != 0:
        raise RuntimeError(state_result.stderr.strip() or "terraform state list failed")

    return {
        "ec2_instances": [
            instance["InstanceId"]
            for reservation in instances_data.get("Reservations", [])
            for instance in reservation.get("Instances", [])
        ],
        "ebs_volumes": [volume["VolumeId"] for volume in volumes_data.get("Volumes", [])],
        "elastic_ips": [
            address.get("AllocationId", address.get("PublicIp", "unknown"))
            for address in addresses_data.get("Addresses", [])
        ],
        "terraform_state": [
            address for address in state_result.stdout.splitlines() if address.strip()
        ],
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fail unless project EC2/EBS/EIP inventory and Terraform state are empty."
    )
    parser.add_argument("--project", required=True)
    parser.add_argument("--region", required=True)
    parser.add_argument("--terraform-dir", type=Path, default=Path("infra/terraform"))
    return parser


def main(argv: Sequence[str] | None = None, runner: Runner = subprocess.run) -> int:
    arguments = _parser().parse_args(argv)
    try:
        remaining = collect_remaining(
            arguments.project,
            arguments.region,
            arguments.terraform_dir,
            runner,
        )
    except RuntimeError as error:
        print(f"teardown verification error: {error}", file=sys.stderr)
        return 2

    for category, identifiers in remaining.items():
        print(f"{category}: {len(identifiers)}")
        for identifier in identifiers:
            print(f"  - {identifier}")

    if any(remaining.values()):
        print("teardown incomplete: project resources or Terraform state remain")
        return 1

    print("teardown verified: no tracked or tagged cost-bearing resources remain")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
