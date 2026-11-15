# INC-0001: Lambda gets AccessDeniedException from DynamoDB (SW-005)

An order-lookup Lambda failed with `AccessDeniedException` on `dynamodb:GetItem`. I rebuilt the system with the AWS CLI only, reproduced the failure on purpose, fixed it with a least-privilege policy, proved the fix, and tore everything down. Full write-up: [POSTMORTEM.md](POSTMORTEM.md).

## The system
| Part | Name | Notes |
|---|---|---|
| DynamoDB table | `sw-orders` | on-demand, key `order_id` (string), 3 seeded orders |
| Lambda function | `sw-order-lookup` | Python 3.12, `handler.py`: 200 found, 404 not found, 400 no `order_id` |
| IAM role | `sw-order-lookup-role` | trust policy: only `lambda.amazonaws.com` may assume it |
| Log group | `/aws/lambda/sw-order-lookup` | created up front, 1-day retention |

## Scripts
| Script | What it does |
|---|---|
| `deploy.sh` | builds everything with a **logs-only** role (reproduces the incident) |
| `test.sh` | invokes the function with an existing ID, a missing ID and no ID |
| `fix.sh` | attaches `policies/dynamodb-getitem.json` (the fix) |
| `break.sh` | removes the fix again |
| `teardown.sh` | deletes everything, then checks each resource is gone |

All scripts use the SSO profile `stratus` (`config.sh`). The account ID is filled in at run time and never stored in the repo.

## The fix (least privilege)
```json
{ "Effect": "Allow", "Action": "dynamodb:GetItem",
  "Resource": "arn:aws:dynamodb:ap-northeast-1:<account>:table/sw-orders" }
```
One action, one table. No `*` in Action or Resource, no `AmazonDynamoDBFullAccess`. If this function were ever compromised, it could only read single orders from this one table.

## How to verify
```bash
aws sso login --profile stratus
./deploy.sh && ./test.sh      # 1001 and 9999 fail with AccessDeniedException; {} returns 400
./fix.sh && ./test.sh         # may need a few minutes, see POSTMORTEM; then 200 / 404 / 400
./teardown.sh                 # four GONE lines
```
Evidence from my run is in [`evidence/`](evidence/) (account ID masked).

## Cost and cleanup
Near 0 USD: a few Lambda invocations, a few DynamoDB on-demand reads, a few KB of logs. `teardown.sh` removes all of it; evidence/5-teardown.txt shows each resource GONE.

## Problems I hit
1. Running `deploy.sh` twice fails with `Table already exists`. The script builds from an empty account, so run `teardown.sh` first.
2. A brand-new role can't be used by Lambda for a few seconds ("role cannot be assumed"). `deploy.sh` retries instead of failing.
3. After attaching the fix, the function was still denied for about 5 minutes. My first attempt waited only 15 s, tested once and tore down. See POSTMORTEM.md.
