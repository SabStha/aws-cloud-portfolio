#!/usr/bin/env bash
# verify-account.sh — Stratus Works SW-003 check (read-only: it changes nothing)
# Usage:  aws sso login --profile stratus   then   bash tools/verify-account.sh [profile]
# The account ID is masked in the output, so you can paste it as evidence.

P="${1:-stratus}"
pass=0; fail=0
ok()  { printf '  PASS  %s\n' "$1"; pass=$((pass+1)); }
bad() { printf '  FAIL  %s\n' "$1"; [ -n "${2:-}" ] && printf '        -> %s\n' "$2"; fail=$((fail+1)); }
aw()  { aws --profile "$P" "$@" 2>/dev/null; }
command -v jq >/dev/null || { echo "jq is required (sudo apt install jq)"; exit 2; }

echo "Stratus Works · verify-account · profile '$P' · $(date '+%Y-%m-%d %H:%M %Z')"
echo

echo "[1] Who am I"
id=$(aw sts get-caller-identity --output json)
if [ -z "$id" ]; then
  bad "Can call AWS with profile '$P'" "run: aws sso login --profile $P   (or aws configure sso if the profile doesn't exist)"
  echo; echo "Result: $pass passed, $fail failed"; exit 1
fi
ACC=$(echo "$id" | jq -r .Account); ARN=$(echo "$id" | jq -r .Arn)
M="****${ACC: -4}"; ARNM=${ARN//$ACC/$M}
echo "        account $M · $ARNM"
case "$ARN" in *assumed-role/AWSReservedSSO_*) ok "Signed in through IAM Identity Center (AWSReservedSSO role)";;
  *:root) bad "Signed in through IAM Identity Center" "you are using ROOT. Stop: use the SSO profile";;
  *) bad "Signed in through IAM Identity Center" "this is an IAM user or other role, not SSO";; esac
grep -q "sso_" ~/.aws/config 2>/dev/null && ok "Profile uses SSO (sso settings in ~/.aws/config)" || bad "Profile uses SSO" "run: aws configure sso"
r=$(aws configure get region --profile "$P")
[ "$r" = "ap-northeast-1" ] && ok "Default region is ap-northeast-1" || bad "Default region is ap-northeast-1 (found: ${r:-none})"
if grep -qi 'aws_access_key_id' ~/.aws/credentials 2>/dev/null; then bad "No long-lived access keys on this machine" "~/.aws/credentials contains access keys"; else ok "No long-lived access keys on this machine"; fi

echo
echo "[2] Root user"
s=$(aw iam get-account-summary --output json)
if [ -n "$s" ]; then
  [ "$(echo "$s" | jq .SummaryMap.AccountMFAEnabled)" = "1" ] && ok "Root MFA enabled (AccountMFAEnabled=1)" || bad "Root MFA enabled (AccountMFAEnabled=1)"
  [ "$(echo "$s" | jq .SummaryMap.AccountAccessKeysPresent)" = "0" ] && ok "Root has no access keys (AccountAccessKeysPresent=0)" || bad "Root has no access keys" "delete them: Security credentials page while signed in as root"
else bad "Can read the IAM account summary" "permission set needs iam:GetAccountSummary (AdministratorAccess has it)"; fi

echo
echo "[3] IAM user access keys"
users=$(aw iam list-users --query 'Users[].UserName' --output text)
active=""
for u in $users; do
  k=$(aw iam list-access-keys --user-name "$u" --query "AccessKeyMetadata[?Status=='Active'].AccessKeyId" --output text)
  for key in $k; do active="$active $u(${key:0:4}****${key: -4})"; done
done
echo "        IAM users: ${users:-none}"
if [ -z "$active" ]; then ok "No active IAM user access keys"
elif [ "${SW_KEYS_JUSTIFIED:-}" = "1" ]; then ok "Active keys justified in README:$active"
else bad "No active IAM user access keys (found:$active)" "delete them, or justify each in the README and re-run with SW_KEYS_JUSTIFIED=1"; fi

echo
echo "[4] Budgets"
b=$(aws --profile "$P" --region us-east-1 budgets describe-budgets --account-id "$ACC" --output json 2>/dev/null)
if [ -z "$b" ]; then bad "Can read budgets" "permission set needs budgets:ViewBudget"; else
  echo "$b" | jq -r '.Budgets[]? | "        budget: \(.BudgetName) · \(.BudgetType) · \(.TimeUnit) · \(.BudgetLimit.Amount) \(.BudgetLimit.Unit)"'
  cost=$(echo "$b" | jq -r '[.Budgets[]? | select(.BudgetType=="COST" and .TimeUnit=="MONTHLY" and (.BudgetLimit.Amount|tonumber) >= 1 and (.BudgetLimit.Amount|tonumber) <= 5)][0].BudgetName // empty')
  if [ -n "$cost" ]; then
    ok "Monthly cost budget of 5 USD or less ($cost)"
    n=$(aws --profile "$P" --region us-east-1 budgets describe-notifications-for-budget --account-id "$ACC" --budget-name "$cost" --output json 2>/dev/null \
        | jq -r '[.Notifications[]? | "\(.NotificationType):\(.Threshold|floor)"] | join(" ")')
    echo "        alerts on '$cost': ${n:-none}"
    for need in ACTUAL:50 ACTUAL:80 ACTUAL:100 FORECASTED:100; do
      case " $n " in *" $need "*) ok "Alert at ${need#*:}% ${need%%:*}";; *) bad "Alert at ${need#*:}% ${need%%:*}";; esac
    done
  else bad "Monthly cost budget of 5 USD or less" "Billing → Budgets → Create budget → Monthly cost budget"; fi
  zero=$(echo "$b" | jq -r '[.Budgets[]? | select(.BudgetType=="COST" and (.BudgetLimit.Amount|tonumber) < 1)][0].BudgetName // empty')
  [ -n "$zero" ] && ok "Zero-spend budget ($zero)" || bad "Zero-spend budget" "Budgets → Create budget → template: Zero spend budget"
fi

echo
echo "[5] Cost Anomaly Detection"
mon=$(aws --profile "$P" --region us-east-1 ce get-anomaly-monitors --output json 2>/dev/null | jq '.AnomalyMonitors | length')
[ "${mon:-0}" -gt 0 ] 2>/dev/null && ok "Anomaly monitor exists ($mon)" || bad "Anomaly monitor exists" "Billing → Cost Anomaly Detection → Create monitor"
sub=$(aws --profile "$P" --region us-east-1 ce get-anomaly-subscriptions --output json 2>/dev/null | jq '[.AnomalySubscriptions[]?.Subscribers[]? | select(.Type=="EMAIL")] | length')
[ "${sub:-0}" -gt 0 ] 2>/dev/null && ok "Anomaly alerts go to an email address" || bad "Anomaly alerts go to an email address" "add an alert subscription with your email"

echo
echo "Result: $pass passed, $fail failed"
[ "$fail" -eq 0 ]
