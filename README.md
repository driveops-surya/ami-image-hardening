# AMI DevOps Pipeline - ap-south-1 Region

## Overview
Fully automated CI/CD pipeline for building, hardening, and scanning Amazon Machine Images (AMIs) in the **ap-south-1 (Mumbai) region**.

## Features
- 🚀 **Automated Daily Builds** at 12:00 PM UTC (5:30 PM IST)
- 🔒 **Security Hardening** using Ansible (CIS Level 1 compliance)
- 🔍 **Vulnerability Scanning** with Qualys integration
- 📊 **Comprehensive Reporting** in HTML, CSV, and JSON formats
- 🏷️ **Smart AMI Tagging** based on security scan results
- 🌏 **Region Specific** - Optimized for ap-south-1 (Mumbai)
- 🔐 **Branch Protection** and code ownership
- 📧 **Notifications** via SNS (optional)

## Quick Start

### Prerequisites

1. **AWS Setup** (ap-south-1 region):
```bash
# Configure AWS CLI
aws configure --profile production
# Set region to ap-south-1

## Architecture Diagram

```mermaid
graph TB
    subgraph "Schedule Trigger"
        A[Cron: 0 12 * * *<br/>Daily 12:00 PM UTC<br/>5:30 PM IST]
    end

    subgraph "GitHub Actions Pipeline"
        B[Fetch Latest Base AMI<br/>RHEL 9 / Amazon Linux 2023]
        C[Packer Build<br/>HCL Templates]
        D[Ansible Hardening<br/>CIS Level 1 Compliance]
        E[Launch Test Instance<br/>ap-south-1 Region]
        F[Qualys Vulnerability Scan]
        G{Decision Logic<br/>Vulnerabilities Found?}
    end

    subgraph "Success Path"
        H[Tag AMI<br/>hardened=true<br/>security=passed]
        I[Store in AWS AMI Catalog]
        J[Generate Success Report]
    end

    subgraph "Failure Path"
        K[Generate Detailed Report<br/>CVE Details & Severity]
        L[Upload to S3 Bucket<br/>/failures/ directory]
        M[Tag AMI<br/>hardened=false<br/>security=failed]
        N[Send SNS Alert<br/>Security Team Notification]
    end

    subgraph "Cleanup"
        O[Terminate Test Instance]
        P[Archive Pipeline Artifacts]
    end

    A --> B
    B --> C
    C --> D
    D --> E
    E --> F
    F --> G
    
    G -->|No Vulnerabilities| H
    H --> I
    I --> J
    J --> O
    
    G -->|Vulnerabilities Found| K
    K --> L
    L --> M
    M --> N
    N --> O
    
    O --> P

    style A fill:#f9f,stroke:#333,stroke-width:2px
    style G fill:#ffeb3b,stroke:#333,stroke-width:2px
    style H fill:#4caf50,stroke:#333,stroke-width:2px,color:#fff
    style K fill:#f44336,stroke:#333,stroke-width:2px,color:#fff
    style M fill:#ff9800,stroke:#333,stroke-width:2px
```