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
        "Name=state,Values=available" \
        "Name=architecture,Values=x86_64" \
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
    }
  }
}
EOF

echo "AMI IDs saved to $OUTPUT_DIR/latest_amis.json"
echo "RHEL AMI: $RHEL_AMI"

# Export for GitHub Actions
if [[ -n "${GITHUB_ENV:-}" ]]; then
    echo "RHEL_AMI=$RHEL_AMI" >> "$GITHUB_ENV"
fi