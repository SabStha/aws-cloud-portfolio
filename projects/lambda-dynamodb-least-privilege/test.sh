#!/usr/bin/env bash
# Invoke the function three ways: existing order, missing order, no order_id.
cd "$(dirname "$0")" && source ./config.sh
for payload in '{"order_id":"1001"}' '{"order_id":"9999"}' '{}'; do
  echo "== payload: $payload"
  aws lambda invoke --function-name "$FN" --cli-binary-format raw-in-base64-out \
    --payload "$payload" /tmp/out.json --query 'FunctionError' --output text
  cat /tmp/out.json; echo; echo
done
