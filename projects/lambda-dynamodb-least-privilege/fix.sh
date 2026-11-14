#!/usr/bin/env bash
# Attach the least-privilege policy: dynamodb:GetItem on the sw-orders table only.
set -euo pipefail
cd "$(dirname "$0")" && source ./config.sh
ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
sed "s/ACCOUNT_ID/$ACCOUNT/" policies/dynamodb-getitem.json > /tmp/dynamodb-getitem.json
aws iam put-role-policy --role-name "$ROLE" --policy-name dynamodb-getitem-sw-orders \
  --policy-document file:///tmp/dynamodb-getitem.json
echo "Fix attached. Waiting 15s for IAM to apply it..."; sleep 15
