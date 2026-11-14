#!/usr/bin/env bash
# verify-workstation.sh — Stratus Works SW-001 check
# Run inside Ubuntu (WSL):  bash verify-workstation.sh
# Prints PASS/FAIL for each item and a summary. Safe: it only reads, it changes nothing.

pass=0; fail=0
ok()  { printf '  PASS  %s\n' "$1"; pass=$((pass+1)); }
bad() { printf '  FAIL  %s\n' "$1"; [ -n "$2" ] && printf '        -> %s\n' "$2"; fail=$((fail+1)); }
have() { command -v "$1" >/dev/null 2>&1; }

echo "Stratus Works · verify-workstation · $(date '+%Y-%m-%d %H:%M %Z')"
echo

echo "[1] WSL and Ubuntu"
if grep -qi microsoft /proc/version 2>/dev/null; then
  if grep -qi 'WSL2' /proc/version || [ -d /run/WSL ] || uname -r | grep -qi 'microsoft-standard'; then
    ok "Running in WSL2"
  else bad "Running in WSL, but not WSL 2" "In PowerShell: wsl --set-version Ubuntu-24.04 2"; fi
else bad "Not running inside WSL" "Open Ubuntu from the Start menu and run this again"; fi
. /etc/os-release 2>/dev/null
if [ "${VERSION_ID%%.*}" -ge 24 ]; then ok "Ubuntu 24.04 or newer ($PRETTY_NAME)"; else bad "Ubuntu 24.04 (found: ${PRETTY_NAME:-unknown})"; fi
case "$PWD" in /mnt/*) bad "Working in the Linux file system" "You are under $PWD. Work in ~/ instead";; *) ok "Working in the Linux file system ($PWD)";; esac

echo
echo "[2] Tools"
for t in git jq zip unzip curl make; do
  if have "$t"; then ok "$t ($($t --version 2>&1 | head -n1))"; else bad "$t is installed" "sudo apt install $t"; fi
done
if have dig; then ok "dig ($(dig -v 2>&1 | head -n1))"; else bad "dig is installed" "it is in the dnsutils package"; fi
if have aws; then
  v=$(aws --version 2>&1)
  case "$v" in aws-cli/2.*) ok "AWS CLI v2 ($v)";; *) bad "AWS CLI is version 2 (found: $v)" "use the official installer zip from AWS";; esac
else bad "AWS CLI v2 is installed"; fi
if have terraform; then ok "terraform ($(terraform version 2>/dev/null | head -n1))"; else bad "terraform is installed" "use HashiCorp's apt repository"; fi
if have python3; then
  ok "python3 ($(python3 --version 2>&1))"
  tmp=$(mktemp -d)
  if python3 -m venv "$tmp/v" >/dev/null 2>&1; then ok "python3 venv works"; else bad "python3 venv works" "sudo apt install python3-venv"; fi
  rm -rf "$tmp"
else bad "python3 is installed"; fi

echo
echo "[3] VS Code"
if have code; then ok "'code' command is available inside WSL"; else bad "'code' command is available inside WSL" "install the WSL extension in VS Code, then run 'code .' once"; fi

echo
echo "[4] Git identity"
n=$(git config --global user.name); e=$(git config --global user.email); b=$(git config --global init.defaultBranch)
[ -n "$n" ] && ok "user.name is set ($n)" || bad "user.name is set"
[ -n "$e" ] && ok "user.email is set" || bad "user.email is set"
[ "$b" = "main" ] && ok "init.defaultBranch = main" || bad "init.defaultBranch = main (found: ${b:-not set})"

echo
echo "[5] GitHub SSH"
if ls ~/.ssh/id_ed25519.pub >/dev/null 2>&1; then ok "ed25519 key exists (~/.ssh/id_ed25519.pub)"; else bad "ed25519 key exists" "ssh-keygen -t ed25519"; fi
echo "        (if asked, type your SSH key passphrase)"
out=$(ssh -T -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 git@github.com 2>&1)
if echo "$out" | grep -q "successfully authenticated"; then ok "GitHub authenticates: $(echo "$out" | grep -o 'Hi [^!]*!')"
else bad "GitHub authenticates over SSH" "$(echo "$out" | tail -n1)"; fi

echo
echo "Result: $pass passed, $fail failed"
[ "$fail" -eq 0 ]
