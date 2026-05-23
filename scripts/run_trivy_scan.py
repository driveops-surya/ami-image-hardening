#!/usr/bin/env python3

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def run(cmd, check=True):
    print("Running command:", " ".join(cmd), flush=True)
    return subprocess.run(cmd, shell=False, check=check)


def ssh_command(instance_ip: str, key_path: str, remote_command: str, user: str = "ec2-user") -> None:
    cmd = [
        "ssh",
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        "-o", "ConnectTimeout=30",
        "-i", key_path,
        f"{user}@{instance_ip}",
        remote_command,
    ]
    run(cmd)


def scp_file(instance_ip: str, key_path: str, remote_path: str, local_dir: Path, user: str = "ec2-user") -> bool:
    local_dir.mkdir(parents=True, exist_ok=True)
    local_path = (local_dir / Path(remote_path).name).resolve()

    cmd = [
        "scp",
        "-O",
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        "-o", "ConnectTimeout=30",
        "-i", key_path,
        f"{user}@{instance_ip}:{remote_path}",
        str(local_path),
    ]

    try:
        run(cmd)
        print(f"Downloaded {remote_path} to {local_path}", flush=True)
        return True
    except subprocess.CalledProcessError as exc:
        print(f"ERROR: failed to download {remote_path}: {exc}", file=sys.stderr)
        return False


def ensure_output_dir(output_dir: Path) -> Path:
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Using output directory: {output_dir}", flush=True)
    return output_dir


def run_trivy_scan(instance_ip: str, key_path: str, output_dir: Path, user: str = "ec2-user") -> None:
    remote_base = "/tmp/trivy_reports"
    remote_json = f"{remote_base}/trivy_results.json"

    remote_command = f"""
set -e

sudo mkdir -p {remote_base}
sudo rm -f {remote_json}

echo "Checking Trivy installation..."
if ! command -v trivy >/dev/null 2>&1; then
  echo "ERROR: Trivy is not installed on the scan instance"
  exit 1
fi

trivy --version

echo "Running Trivy filesystem scan..."

sudo trivy filesystem / \
  --severity CRITICAL,HIGH,MEDIUM \
  --exit-code 0 \
  --scanners vuln \
  --skip-dirs /proc,/sys,/dev,/run,/tmp,/var/cache,/var/log,/mnt,/media,/home/ec2-user/.cache \
  --format json \
  --output {remote_json} \
  --timeout 20m

echo "Validating Trivy report..."
sudo ls -lah {remote_base} || true

if [ ! -f "{remote_json}" ]; then
  echo "ERROR: {remote_json} was not generated"
  exit 1
fi

if [ ! -s "{remote_json}" ]; then
  echo "ERROR: {remote_json} is empty"
  exit 1
fi

sudo chmod 644 {remote_json}

echo "Trivy JSON report generated successfully"
"""

    print(f"Starting Trivy scan against {instance_ip}", flush=True)
    ssh_command(instance_ip, key_path, remote_command, user=user)

    print(f"Downloading report from {remote_json} to {output_dir}", flush=True)

    downloaded = scp_file(
        instance_ip=instance_ip,
        key_path=key_path,
        remote_path=remote_json,
        local_dir=output_dir,
        user=user,
    )

    if not downloaded:
        raise RuntimeError("Failed to download trivy_results.json from scan instance")

    local_report = output_dir / "trivy_results.json"

    if not local_report.exists():
        raise RuntimeError(f"Downloaded report not found locally: {local_report}")

    if local_report.stat().st_size == 0:
        raise RuntimeError(f"Downloaded report is empty: {local_report}")

    print(f"Local report verified: {local_report}", flush=True)


def parse_json_counts(json_path: Path) -> dict:
    if not json_path.exists():
        raise FileNotFoundError(f"JSON report not found: {json_path}")

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
    parser = argparse.ArgumentParser(
        description="Run remote Trivy filesystem scan and collect JSON report."
    )
    parser.add_argument("--instance-ip", required=True)
    parser.add_argument("--private-key", required=True)
    parser.add_argument("--output-dir", default="./reports")
    parser.add_argument("--ssh-user", default="ec2-user")
    return parser


def main() -> int:
    args = build_parser().parse_args()

    output_dir = ensure_output_dir(Path(args.output_dir))
    private_key = Path(args.private_key).resolve()

    if not private_key.exists():
        print(f"Private key file not found: {private_key}", file=sys.stderr)
        return 1

    try:
        run_trivy_scan(
            instance_ip=args.instance_ip,
            key_path=str(private_key),
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

    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())