#!/usr/bin/env python3

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def run(cmd, check=True):
    return subprocess.run(cmd, shell=False, check=check)


def ssh_command(instance_ip: str, key_path: str, remote_command: str, user: str = "ec2-user") -> None:
    cmd = [
        "ssh",
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        "-i", key_path,
        f"{user}@{instance_ip}",
        remote_command,
    ]
    run(cmd)


def scp_file(instance_ip: str, key_path: str, remote_path: str, local_dir: Path, user: str = "ec2-user") -> bool:
    local_path = local_dir / Path(remote_path).name

    cmd = [
        "scp",
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        "-i", key_path,
        f"{user}@{instance_ip}:{remote_path}",
        str(local_path),
    ]

    try:
        run(cmd)
        print(f"Downloaded {remote_path} to {local_path}")
        return True
    except subprocess.CalledProcessError as exc:
        print(f"Warning: failed to download {remote_path}: {exc}", file=sys.stderr)
        return False


def ensure_output_dir(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Using output directory: {output_dir}")


def run_trivy_scan(instance_ip: str, key_path: str, output_dir: Path, user: str = "ec2-user") -> None:
    remote_base = "/tmp/trivy_reports"

    remote_command = f"""
sudo mkdir -p {remote_base}
set -e

sudo trivy filesystem / \
  --severity CRITICAL,HIGH,MEDIUM \
  --exit-code 0 \
  --scanners vuln \
  --skip-dirs /proc,/sys,/dev,/run,/tmp,/var/cache,/var/log,/mnt,/media \
  --format json \
  --output {remote_base}/trivy_results.json \
  --timeout 20m || true
"""

    print("Running Trivy filesystem scan once in JSON format...")
    ssh_command(instance_ip, key_path, remote_command, user=user)

    scp_file(
        instance_ip,
        key_path,
        f"{remote_base}/trivy_results.json",
        output_dir,
        user=user,
    )


def parse_json_counts(json_path: Path) -> dict:
    if not json_path.exists():
        print(f"Warning: JSON report not found at {json_path}", file=sys.stderr)
        return {
            "total": 0,
            "critical": 0,
            "high": 0,
            "medium": 0,
        }

    with json_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    vulns = [
        vuln
        for result in data.get("Results", [])
        for vuln in result.get("Vulnerabilities", [])
        if vuln
    ]

    critical = sum(1 for v in vulns if v.get("Severity") == "CRITICAL")
    high = sum(1 for v in vulns if v.get("Severity") == "HIGH")
    medium = sum(1 for v in vulns if v.get("Severity") == "MEDIUM")
    total = critical + high + medium

    return {
        "total": total,
        "critical": critical,
        "high": high,
        "medium": medium,
    }


def write_github_outputs(outputs: dict) -> None:
    github_output = os.getenv("GITHUB_OUTPUT")

    if not github_output:
        print("GITHUB_OUTPUT is not defined; skipping output export", file=sys.stderr)
        return

    with open(github_output, "a", encoding="utf-8") as f:
        for name, value in outputs.items():
            f.write(f"{name}={value}\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a remote Trivy scan and collect JSON report.")

    parser.add_argument("--instance-ip", required=True)
    parser.add_argument("--private-key", required=True)
    parser.add_argument("--output-dir", default="./reports")
    parser.add_argument("--ssh-user", default="ec2-user")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    ensure_output_dir(output_dir)

    if not Path(args.private_key).exists():
        print(f"Private key file not found: {args.private_key}", file=sys.stderr)
        return 1

    print(f"Starting Trivy scan against {args.instance_ip}")

    run_trivy_scan(
        instance_ip=args.instance_ip,
        key_path=args.private_key,
        output_dir=output_dir,
        user=args.ssh_user,
    )

    counts = parse_json_counts(output_dir / "trivy_results.json")

    write_github_outputs(
        {
            "total_vulnerabilities": counts["total"],
            "critical_count": counts["critical"],
            "high_count": counts["high"],
            "medium_count": counts["medium"],
        }
    )

    print("=== Scan Results ===")
    print(
        f"Total: {counts['total']} | "
        f"Critical: {counts['critical']} | "
        f"High: {counts['high']} | "
        f"Medium: {counts['medium']}"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())