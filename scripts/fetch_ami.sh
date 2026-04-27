#!/bin/bash

# Script to fetch latest AMI IDs from ap-south-1 region
set -euo pipefail

AWS_REGION="ap-south-1"
OUTPUT_DIR="${1:-./reports}"

mkdir -p "$OUTPUT_DIR"

# Fetch RHEL 9 AMI
echo "Fetching latest RHEL 9 AMI in $AWS_REGION..."
RHEL_AMI=$(aws ec2 describe-images \
    --region "$AWS_REGION" \
    --owners 309956199498 \
    --filters "Name=name,Values=RHEL-9.*_HVM-*" \
              "Name=state,available" \
              "Name=architecture,x86_64" \
    --query 'Images | sort_by(@, &CreationDate) | [-1].ImageId' \
    --output text)

# Fetch Amazon Linux 2023 AMI
echo "Fetching latest Amazon Linux 2023 AMI in $AWS_REGION..."
AMZN_AMI=$(aws ec2 describe-images \
    --region "$AWS_REGION" \
    --owners 137112412989 \
    --filters "Name=name,Values=al2023-ami-2023.*-x86_64" \
              "Name=state,available" \
              "Name=architecture,x86_64" \
    --query 'Images | sort_by(@, &CreationDate) | [-1].ImageId' \
    --output text)

# Create JSON output
cat > "$OUTPUT_DIR/latest_amis.json" <<EOF
{
  "timestamp": "$(date -Iseconds)",
  "region": "$AWS_REGION",
  "amis": {
    "rhel": {
      "version": "9",
      "ami_id": "$RHEL_AMI",
      "owner": "Red Hat"
    },
    "amazonlinux": {
      "version": "2023",
      "ami_id": "$AMZN_AMI",
      "owner": "Amazon"
    }
  }
}
EOF

echo "AMI IDs saved to $OUTPUT_DIR/latest_amis.json"
echo "RHEL AMI: $RHEL_AMI"
echo "Amazon Linux AMI: $AMZN_AMI"

# Export for GitHub Actions
if [[ -n "${GITHUB_ENV:-}" ]]; then
    echo "RHEL_AMI=$RHEL_AMI" >> "$GITHUB_ENV"
    echo "AMZN_AMI=$AMZN_AMI" >> "$GITHUB_ENV"
fi