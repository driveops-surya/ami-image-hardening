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

## Architecture Diagram

```mermaid
graph TB
    A["Daily Schedule"]
    B["Fetch Base AMI"]
    C["Packer Build"]
    D["Ansible Hardening"]
    E["Launch Instance"]
    F["Qualys Scan"]
    G{Vulnerabilities?}
    
    H["Tag: hardened=true"]
    I["Store in Catalog"]
    J["Success Report"]
    
    K["Generate Report"]
    L["Upload to S3"]
    M["Tag: security=failed"]
    N["SNS Alert"]
    
    O["Terminate Instance"]
    P["Archive Artifacts"]

    A --> B
    B --> C
    C --> D
    D --> E
    E --> F
    F --> G
    
    G -->|No| H
    H --> I
    I --> J
    J --> O
    
    G -->|Yes| K
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