#!/usr/bin/env bash
# Delete everything deploy.sh made, then prove each resource is gone.
set -uo pipefail
cd "$(dirname "$0")" && source ./config.sh

aws lambda delete-function --function-name "$FN" 2>/dev/null && echo "deleted function $FN"
for p in $(aws iam list-role-policies --role-name "$ROLE" --query 'PolicyNames' --output text 2>/dev/null); do
  aws iam delete-role-policy --role-name "$ROLE" --policy-name "$p" && echo "deleted policy $p"
done
aws iam delete-role --role-name "$ROLE" 2>/dev/null && echo "deleted role $ROLE"
aws logs delete-log-group --log-group-name "$LOG_GROUP" 2>/dev/null && echo "deleted log group $LOG_GROUP"
aws dynamodb delete-table --table-name "$TABLE" > /dev/null 2>&1 && echo "deleting table $TABLE..." \
  && aws dynamodb wait table-not-exists --table-name "$TABLE" && echo "deleted table $TABLE"

echo; echo "== Proof: each check must say GONE"
gone() { if eval "$2" > /dev/null 2>&1; then echo "STILL EXISTS  $1"; else echo "GONE          $1"; fi; }
gone "function $FN"   "aws lambda get-function --function-name $FN"
gone "role $ROLE"     "aws iam get-role --role-name $ROLE"
gone "table $TABLE"   "aws dynamodb describe-table --table-name $TABLE"
gone "log group $LOG_GROUP" "[ -n \"\$(aws logs describe-log-groups --log-group-name-prefix $LOG_GROUP --query 'logGroups[0].logGroupName' --output text | grep -v None)\" ]"
