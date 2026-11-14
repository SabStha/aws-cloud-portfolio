# Postmortem: INC-0001 order lookup returns AccessDeniedException

**Date:** 14 Nov 2026 (lab reproduction) · **Author:** Sabin Shrestha · **Status:** resolved

## Summary
The order-lookup Lambda could not read from DynamoDB. Its execution role only allowed writing CloudWatch Logs, so every `GetItem` call was denied and every lookup failed. Fixed by attaching a policy that allows only `dynamodb:GetItem` on the `sw-orders` table.

## Impact
Every request with an `order_id` failed with an unhandled error (100% of real lookups). Requests without an `order_id` still returned 400, because the code returns before calling DynamoDB. No data was lost or exposed.

## Timeline (JST, 14 Nov 2026)
- **21:58** Deployed with the logs-only role. First invoke fails: `AccessDeniedException ... dynamodb:GetItem ... because no identity-based policy allows the dynamodb:GetItem action`. Same error confirmed in CloudWatch with `aws logs tail`.
- **22:02** First fix attempt: attached the GetItem policy, waited 15 s, tested once. Still denied. The script then tore everything down, so the fix could not be confirmed.
- **22:05:27** Redeployed (bug reproduced again), attached the fix.
- **22:05:53 to 22:10:35** Re-tested every 10 s: still denied.
- **22:10:46** Order 1001 returns 200. Missing ID returns 404, no ID returns 400.
- **~22:11** Teardown: function, role, both policies, log group and table all confirmed gone.

## Root cause
IAM denies every action that no policy allows. The role `sw-order-lookup-role` had only one policy, which allowed `logs:CreateLogStream` and `logs:PutLogEvents`. Nothing allowed `dynamodb:GetItem`, so DynamoDB refused the read.

The error message held the whole diagnosis: **who** (`assumed-role/sw-order-lookup-role`), **what** (`dynamodb:GetItem`), **which resource** (the table ARN) and **why** (`no identity-based policy allows`). The trust policy was fine: the function did assume the role.

## Fix
Before (only policy on the role):
```json
{ "Effect": "Allow", "Action": ["logs:CreateLogStream", "logs:PutLogEvents"],
  "Resource": "arn:aws:logs:ap-northeast-1:<account>:log-group:/aws/lambda/sw-order-lookup:*" }
```
After (added):
```json
{ "Effect": "Allow", "Action": "dynamodb:GetItem",
  "Resource": "arn:aws:dynamodb:ap-northeast-1:<account>:table/sw-orders" }
```

## What made recovery slower
The correct policy took about **5 minutes 19 seconds** (22:05:27 to 22:10:46) before the function could use it. IAM changes are eventually consistent: they reach every part of AWS over time, not instantly. Lambda may also keep using a warm execution environment for a while; I did not confirm whether that played a part. A fixed 15 s wait was not enough, and my first attempt tore down before checking the result.

Lesson: when a correct fix still fails right after you apply it, don't change the fix. Wait and re-test, and don't clean up until a test passes.

## Action items
1. Replace the fixed `sleep` in `fix.sh` with a wait-and-retest loop that stops when an invoke succeeds (or after a timeout).
2. Make teardown a separate, manual step: never tear down in the same command as a test whose result hasn't been checked.
3. Test whether forcing a new Lambda execution environment (for example, updating an environment variable) makes the new permission apply sooner.
4. Add a CloudWatch alarm on the function's `Errors` metric, so a permission problem pages someone instead of waiting for a customer report.
