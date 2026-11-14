# Workstation setup (SW-001)

## What I set up
- WSL2 with Ubuntu 26.04.1 LTS (newer LTS than the 24.04 in the ticket; accepted by my manager)
- Inside Ubuntu: git, AWS CLI v2 (official installer), Terraform (HashiCorp apt repo), python3 with venv, jq, zip, unzip, dig (dnsutils), curl, make
- VS Code connected to WSL (`code .` opens folders from Ubuntu)
- Git identity set globally, default branch `main`
- ed25519 SSH key added to GitHub; I work in ~/ (Linux file system), not /mnt/c

## How to verify
Run `bash ~/tools/verify-workstation.sh`. Result on 14 Nov 2026: 20 passed, 0 failed (see evidence.md).
`wsl -l -v` from PowerShell: see wsl-version.png.

## Problems I hit and how I fixed them
1. `ssh -T git@github.com` gave "Permission denied (publickey)" in PowerShell.
   Cause: my SSH key was created inside Ubuntu, so Windows does not have it. Fix: run Git and SSH commands only in Ubuntu.
2. `ssh -T <my email>` hung. Cause: I used my email as the host. The correct target is `git@github.com`; GitHub identifies me by my key.
3. The verify script failed on jq, zip, make, dig and python3-venv. Fix: installed them with apt; dig comes from the dnsutils package.
4. The script failed on "Ubuntu 24.04" because I have 26.04 LTS. My manager accepted it and the check now allows 24.04 or newer LTS.
5. `wsl -l -v` inside Ubuntu ran a different tool called wsl. It must be run in PowerShell.

## What I learned
Git on my machine and GitHub are separate. Nothing is uploaded until I commit and push, and the SSH key only proves who I am.
