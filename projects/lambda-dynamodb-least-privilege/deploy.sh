#!/usr/bin/env bash
# Build the system with a role that can ONLY write logs (this reproduces the incident).
set -euo pipefail
cd "$(dirname "$0")" && source ./config.sh
ACCOUNT=$(aws sts get-caller-identity --query Account --output text)

echo "1/6 Create DynamoDB table $TABLE (on-demand)"
aws dynamodb create-table --table-name "$TABLE" \
  --attribute-definitions AttributeName=order_id,AttributeType=S \
  --key-schema AttributeName=order_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST > /dev/null
aws dynamodb wait table-exists --table-name "$TABLE"

echo "2/6 Seed 3 orders"
for row in 1001:ramen:1200 1002:gyoza:600 1003:momo:900; do
  IFS=: read -r id item price <<< "$row"
  aws dynamodb put-item --table-name "$TABLE" \
    --item "{\"order_id\":{\"S\":\"$id\"},\"item\":{\"S\":\"$item\"},\"price_jpy\":{\"N\":\"$price\"}}"
done

echo "3/6 Create log group $LOG_GROUP (kept 1 day)"
aws logs create-log-group --log-group-name "$LOG_GROUP"
aws logs put-retention-policy --log-group-name "$LOG_GROUP" --retention-in-days 1

echo "4/6 Create role $ROLE with a logs-only policy"
aws iam create-role --role-name "$ROLE" \
  --assume-role-policy-document file://policies/trust-policy.json > /dev/null
sed "s/ACCOUNT_ID/$ACCOUNT/" policies/logs-only.json > /tmp/logs-only.json
aws iam put-role-policy --role-name "$ROLE" --policy-name logs-only \
  --policy-document file:///tmp/logs-only.json

echo "5/6 Package the function"
rm -f function.zip && zip -q function.zip handler.py

echo "6/6 Create the Lambda function (retries while the new role propagates)"
for attempt in 1 2 3 4 5 6; do
  if aws lambda create-function --function-name "$FN" --runtime python3.12 \
       --handler handler.lambda_handler --role "arn:aws:iam::$ACCOUNT:role/$ROLE" \
       --zip-file fileb://function.zip --timeout 10 \
       --environment "Variables={TABLE_NAME=$TABLE}" > /dev/null 2>/tmp/create-fn.err; then
    break
  fi
  echo "   role not ready yet (attempt $attempt), waiting 10s"; sleep 10
  [ "$attempt" = 6 ] && { cat /tmp/create-fn.err; exit 1; }
done
aws lambda wait function-active-v2 --function-name "$FN"
echo "Deployed. Run ./test.sh"
