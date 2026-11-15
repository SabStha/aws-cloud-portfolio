# AWS account guardrails (SW-003)

## What I set up
- **Root user:** MFA on, no access keys, not used for daily work.
- **IAM Identity Center** (Tokyo, ap-northeast-1, with AWS Organizations): user `sabin-admin` with MFA and the `AdministratorAccess` permission set.
- **CLI profile `stratus`** made with `aws configure sso`, default region ap-northeast-1. Logins are short-lived SSO sessions.
- **Budgets:** `stratus-monthly-5usd` (5 USD/month, email alerts at 50/80/100% actual and 100% forecasted) and a zero-spend budget (0.01 USD, alerts on any spend).
- **Cost Anomaly Detection:** one monitor with an email alert subscription.
- **Old access key:** the IAM user `sabin` key from earlier Lambda work is deactivated, and its copy was removed from `~/.aws/credentials`. It will be deleted once I confirm nothing depends on it.

## Why each guardrail exists
- Root can do anything, including closing the account. MFA and no keys mean a stolen password alone is not enough, and nothing on disk can act as root.
- SSO gives credentials that expire, so a leaked laptop or a file pushed to GitHub does not give permanent access. A permanent key does not expire, which is why I removed mine.
- Budgets and anomaly alerts warn me in hours, not at the end of the month. My free credits are used up, so every mistake costs real money.

## Admin access
`AdministratorAccess` is acceptable for a single-person training account. In a real company account I would use least-privilege permission sets per job, keep admin for break-glass use only, and require MFA on every user.

## How to verify
1. `aws sso login --profile stratus`
2. `bash tools/verify-account.sh` → 0 failed (see evidence.md).
3. Billing → Budgets: see budget-alerts.png.

## Problems I hit and how I fixed them
1. `aws configure sso` failed with "Found xterm-256color, while expecting a Windows console". Fix: ran it in a normal PowerShell window.
2. "Invalid start url provided": I used the IAM sign-in URL. The SSO start URL is the IAM Identity Center **access portal URL** (`https://d-xxxxxxxxxx.awsapps.com/start`), which only exists after Identity Center is enabled.
3. My zero-spend budget was set to 1.00 USD, so the check mistook it for the monthly budget. A zero-spend budget must be 0.01 USD.
4. The check failed on an old active IAM key, also saved in `~/.aws/credentials`. Fix: deactivated it first (safe to undo if something breaks), backed up and emptied the credentials file, and switched to `--profile stratus`.

## What I would tighten in a real company account
- No long-lived IAM user keys at all: SSO for people, IAM roles for programs.
- Least-privilege permission sets instead of AdministratorAccess.
- Organization-level guardrails (SCPs), CloudTrail in every region, and alerts sent to a team, not one person.
