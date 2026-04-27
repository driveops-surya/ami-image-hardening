#!/usr/bin/env python3
"""
Qualys Vulnerability Scanner for AMIs
Compatible with Python 3.8+
"""

import json
import subprocess
import argparse
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional
import boto3

class QualysScanner:
    def __init__(self, instance_id: str, region: str = "ap-south-1"):
        self.instance_id = instance_id
        self.region = region
        self.ec2 = boto3.client('ec2', region_name=region)
        self.results = {
            'scan_id': None,
            'instance_id': instance_id,
            'scan_date': datetime.now().isoformat(),
            'vulnerabilities': []
        }
    
    def wait_for_qualys_agent(self, timeout: int = 300) -> bool:
        """Wait for Qualys agent to register and report"""
        print(f"Waiting for Qualys agent to register on instance {self.instance_id}...")
        start_time = time.time()
        
        # Simulate waiting - In production, you would poll Qualys API
        while time.time() - start_time < timeout:
            # Check if agent is ready (simplified)
            time.sleep(10)
            print("Checking agent status...")
            # In real implementation, check Qualys API for host registration
            return True
        return False
    
    def trigger_scan(self, scan_timeout: int = 1800) -> Dict:
        """Trigger vulnerability scan using Qualys API"""
        print("Triggering Qualys vulnerability scan...")
        
        # Simulate scan initiation
        scan_id = f"scan_{int(time.time())}"
        self.results['scan_id'] = scan_id
        
        # Simulate scan progress
        for progress in range(0, 101, 20):
            print(f"Scan progress: {progress}%")
            time.sleep(5)  # Simulate scan time
        
        # In production, you would:
        # 1. Call Qualys API to launch scan
        # 2. Poll for scan completion
        # 3. Fetch scan results
        
        # Simulate some vulnerabilities for testing
        self.results['vulnerabilities'] = self._get_simulated_vulnerabilities()
        
        return self.results
    
    def _get_simulated_vulnerabilities(self) -> List[Dict]:
        """Generate simulated vulnerabilities for testing"""
        # In production, this would come from actual Qualys API response
        return [
            {
                'cve_id': 'CVE-2024-6387',
                'severity': 'HIGH',
                'cvss_score': 8.1,
                'package_name': 'openssh-server',
                'installed_version': '8.7p1-2',
                'fixed_version': '8.8p1-1',
                'description': 'OpenSSH signal handler race condition vulnerability',
                'solution': 'Update openssh-server to version 8.8p1-1 or later',
                'affected_services': ['sshd']
            },
            {
                'cve_id': 'CVE-2024-2961',
                'severity': 'MEDIUM',
                'cvss_score': 6.5,
                'package_name': 'glibc',
                'installed_version': '2.34-83',
                'fixed_version': '2.34-90',
                'description': 'Buffer overflow in iconv() function',
                'solution': 'Update glibc package',
                'affected_services': ['system']
            }
        ]
    
    def save_results(self, output_dir: str) -> str:
        """Save scan results to file"""
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, f"qualys_scan_{self.instance_id}.json")
        
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"Scan results saved to {output_file}")
        return output_file

def main():
    parser = argparse.ArgumentParser(description='Qualys vulnerability scanner')
    parser.add_argument('--instance-id', required=True, help='EC2 instance ID')
    parser.add_argument('--region', default='ap-south-1', help='AWS region')
    parser.add_argument('--output-dir', default='./reports', help='Output directory')
    parser.add_argument('--timeout', type=int, default=1800, help='Scan timeout in seconds')
    
    args = parser.parse_args()
    
    scanner = QualysScanner(args.instance_id, args.region)
    
    # Wait for Qualys agent
    if not scanner.wait_for_qualys_agent():
        print("Error: Qualys agent failed to register", file=sys.stderr)
        sys.exit(1)
    
    # Trigger scan
    results = scanner.trigger_scan(args.timeout)
    
    # Save results
    output_file = scanner.save_results(args.output_dir)
    
    # Output results for GitHub Actions
    vuln_count = len(results['vulnerabilities'])
    print(f"::set-output name=vulnerability_count::{vuln_count}")
    
    if vuln_count > 0:
        print(f"Found {vuln_count} vulnerabilities", file=sys.stderr)
        sys.exit(1)
    else:
        print("No vulnerabilities found")
        sys.exit(0)

if __name__ == '__main__':
    main()