#!/usr/bin/env python3
"""
Generate HTML report from Trivy scan results
"""

import json
import argparse
import os
from pathlib import Path
from datetime import datetime
import html

def generate_html_report(report_file: Path, output_dir: Path, ami_id: str, os_type: str):
    """Generate HTML report from Trivy JSON results"""
    
    # Load Trivy results
    with open(report_file, 'r') as f:
        data = json.load(f)
    
    # Parse vulnerabilities
    vulnerabilities = []
    severity_counts = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
    
    for result in data.get('Results', []):
        target = result.get('Target', 'Unknown')
        for vuln in result.get('Vulnerabilities', []):
            severity = vuln.get('Severity', 'UNKNOWN')
            if severity in severity_counts:
                severity_counts[severity] += 1
            
            vulnerabilities.append({
                'cve_id': vuln.get('VulnerabilityID', 'Unknown'),
                'severity': severity,
                'package_name': vuln.get('PkgName', 'Unknown'),
                'installed_version': vuln.get('InstalledVersion', 'Unknown'),
                'fixed_version': vuln.get('FixedVersion', 'Not available'),
                'title': vuln.get('Title', 'No description'),
                'cvss_score': vuln.get('CVSS', {}).get('nvd', {}).get('V3Score', 'N/A')
            })
    
    total_vulns = len(vulnerabilities)
    
    # Generate HTML
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trivy AMI Vulnerability Scan Report</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }}
        h2 {{ color: #666; margin-top: 20px; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }}
        .card {{ padding: 20px; border-radius: 8px; text-align: center; color: white; }}
        .card.critical {{ background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }}
        .card.high {{ background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); color: #333; }}
        .card.medium {{ background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%); color: #333; }}
        .card.low {{ background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%); color: #333; }}
        .card.total {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }}
        .card-number {{ font-size: 36px; font-weight: bold; }}
        .card-label {{ font-size: 14px; text-transform: uppercase; margin-top: 10px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th {{ background-color: #4CAF50; color: white; padding: 12px; text-align: left; }}
        td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
        tr:hover {{ background-color: #f5f5f5; }}
        .severity {{ display: inline-block; padding: 3px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }}
        .severity-CRITICAL {{ background-color: #dc3545; color: white; }}
        .severity-HIGH {{ background-color: #fd7e14; color: white; }}
        .severity-MEDIUM {{ background-color: #ffc107; color: #333; }}
        .severity-LOW {{ background-color: #28a745; color: white; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; text-align: center; color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🐛 Trivy AMI Vulnerability Scan Report</h1>
        
        <div class="summary">
            <div class="card total">
                <div class="card-number">{total_vulns}</div>
                <div class="card-label">Total Vulnerabilities</div>
            </div>
            <div class="card critical">
                <div class="card-number">{severity_counts['CRITICAL']}</div>
                <div class="card-label">Critical</div>
            </div>
            <div class="card high">
                <div class="card-number">{severity_counts['HIGH']}</div>
                <div class="card-label">High</div>
            </div>
            <div class="card medium">
                <div class="card-number">{severity_counts['MEDIUM']}</div>
                <div class="card-label">Medium</div>
            </div>
        </div>
        
        <div class="details">
            <h2>📊 Scan Information</h2>
            <p><strong>Scanner:</strong> Trivy (Open Source Vulnerability Scanner)</p>
            <p><strong>AMI ID:</strong> {ami_id}</p>
            <p><strong>OS Type:</strong> {os_type}</p>
            <p><strong>Scan Date:</strong> {datetime.now().isoformat()}</p>
            <p><strong>Severity Threshold:</strong> CRITICAL, HIGH, MEDIUM</p>
        </div>
        
        <div class="vulnerabilities">
            <h2>🔍 Vulnerability Details</h2>
            {generate_table(vulnerabilities)}
        </div>
        
        <div class="footer">
            Generated by Trivy Scanner - AMI Security Pipeline on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </div>
</body>
</html>
    """
    
    output_file = output_dir / 'trivy_report.html'
    with open(output_file, 'w') as f:
        f.write(html_content)
    print(f"HTML report generated: {output_file}")

def generate_table(vulnerabilities):
    if not vulnerabilities:
        return '<p style="color: green;">✅ No vulnerabilities detected!</p>'
    
    table = '<table><thead><tr><th>CVE ID</th><th>Severity</th><th>Package</th><th>Installed</th><th>Fixed</th><th>CVSS</th></tr></thead><tbody>'
    for vuln in vulnerabilities[:100]:  # Limit to 100 for display
        severity_class = f"severity-{vuln['severity']}"
        table += f"""
            <tr>
                <td><strong>{html.escape(vuln['cve_id'])}</strong></td>
                <td><span class="severity {severity_class}">{vuln['severity']}</span></td>
                <td>{html.escape(vuln['package_name'])}</td>
                <td>{html.escape(vuln['installed_version'])}</td>
                <td>{html.escape(vuln['fixed_version'])}</td>
                <td>{vuln['cvss_score']}</td>
            </tr>
        """
    table += '</tbody></table>'
    return table

def main():
    parser = argparse.ArgumentParser(description='Generate HTML report from Trivy results')
    parser.add_argument('--report-file', required=True, help='Trivy results JSON file')
    parser.add_argument('--output-dir', default='./reports', help='Output directory')
    parser.add_argument('--ami-id', required=True, help='AMI ID')
    parser.add_argument('--os-type', required=True, help='OS type')
    
    args = parser.parse_args()
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    generate_html_report(
        Path(args.report_file),
        output_dir,
        args.ami_id,
        args.os_type
    )

if __name__ == '__main__':
    main()