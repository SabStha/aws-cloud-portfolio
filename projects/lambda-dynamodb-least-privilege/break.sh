#!/usr/bin/env bash
# Remove the fix again, to reproduce the incident (logs-only role).
set -euo pipefail
cd "$(dirname "$0")" && source ./config.sh
aws iam delete-role-policy --role-name "$ROLE" --policy-name dynamodb-getitem-sw-orders
echo "Fix removed: the role can only write logs again."
