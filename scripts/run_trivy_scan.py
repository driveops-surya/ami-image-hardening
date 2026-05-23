#!/usr/bin/env python3
"""
Run a remote Trivy filesystem scan on an EC2 instance and copy reports locally.
Compatible with Python 3.8+.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def run(cmd, capture_output=False, check=True):
    if capture_output:
        result = subprocess.run(cmd, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if check and result.returncode != 0:
            raise subprocess.CalledProcessError(result.returncode, cmd, output=result.stdout, stderr=result.stderr)
        return result
    return subprocess.run(cmd, shell=False, check=check)


def ssh_command(instance_ip: str, key_path: str, remote_command: str, user: str = "ec2-user") -> None:
    cmd = [
        "ssh",
        "-o",
        "StrictHostKeyChecking=no",
        "-o",
        "UserKnownHostsFile=/dev/null",
        "-i",
        key_path,
        f"{user}@{instance_ip}",
        remote_command,
    ]
    print("Running remote SSH command...")
    run(cmd)


def scp_file(instance_ip: str, key_path: str, remote_path: str, local_dir: Path, user: str = "ec2-user") -> bool:
    local_path = local_dir / Path(remote_path).name
    cmd = [
        "scp",
        "-o",
        "StrictHostKeyChecking=no",
        "-o",
        "UserKnownHostsFile=/dev/null",
        "-i",
        key_path,
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


def install_trivy(instance_ip: str, key_path: str, user: str = "ec2-user") -> None:
    remote_command = """
sudo tee /etc/yum.repos.d/trivy.repo > /dev/null <<'REPO'
[trivy]
name=Trivy
baseurl=https://aquasecurity.github.io/trivy-repo/rpm/releases/9/x86_64/
gpgcheck=0
enabled=1
REPO
sudo yum clean all
sudo yum makecache
sudo yum install -y trivy
trivy --version
"""
    ssh_command(instance_ip, key_path, remote_command, user=user)


def run_trivy_scans(instance_ip: str, key_path: str, output_dir: Path, user: str = "ec2-user") -> None:
    remote_base = "/tmp/trivy_reports"
    remote_command = f"""
sudo mkdir -p {remote_base}
set -e
sudo trivy filesystem \
  --severity CRITICAL,HIGH,MEDIUM \
  --exit-code 0 \
  --scanners vuln \
  --skip-dirs /proc,/sys,/dev \
  --format json \
  --output {remote_base}/trivy_results.json \
  / || true
sudo trivy filesystem \
  --severity CRITICAL,HIGH,MEDIUM \
  --exit-code 0 \
  --scanners vuln \
  --skip-dirs /proc,/sys,/dev \
  --format template \
  --template '@contrib/html.tpl' \
  --output {remote_base}/trivy_report.html \
  / || true
sudo trivy filesystem \
  --severity CRITICAL,HIGH,MEDIUM \
  --exit-code 0 \
  --scanners vuln \
  --skip-dirs /proc,/sys,/dev \
  --format sarif \
  --output {remote_base}/trivy_results.sarif \
  / || true
"""
    ssh_command(instance_ip, key_path, remote_command, user=user)
    for remote_file in [
        f"{remote_base}/trivy_results.json",
        f"{remote_base}/trivy_report.html",
        f"{remote_base}/trivy_results.sarif",
    ]:
        scp_file(instance_ip, key_path, remote_file, output_dir, user=user)


def parse_json_counts(json_path: Path) -> dict:
    if not json_path.exists():
        print(f"Warning: JSON report not found at {json_path}", file=sys.stderr)
        return {"total": 0, "critical": 0, "high": 0, "medium": 0}

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

    return {"total": total, "critical": critical, "high": high, "medium": medium}


def write_github_outputs(outputs: dict) -> None:
    github_output = os.getenv("GITHUB_OUTPUT")
    if not github_output:
        print("GITHUB_OUTPUT is not defined; skipping output export", file=sys.stderr)
        return

    with open(github_output, "a", encoding="utf-8") as f:
        for name, value in outputs.items():
            f.write(f"{name}={value}\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a remote Trivy scan and collect reports.")
    parser.add_argument("--instance-ip", required=True, help="EC2 instance public IP address")
    parser.add_argument("--private-key", required=True, help="Path to SSH private key file")
    parser.add_argument("--output-dir", default="./reports", help="Local directory for downloaded reports")
    parser.add_argument("--ssh-user", default="ec2-user", help="SSH user to connect as")
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
    install_trivy(args.instance_ip, args.private_key, user=args.ssh_user)
    run_trivy_scans(args.instance_ip, args.private_key, output_dir, user=args.ssh_user)

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
    print(f"Total: {counts['total']} | Critical: {counts['critical']} | High: {counts['high']} | Medium: {counts['medium']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
