# GitHub PR workflow (SW-002)

## What I set up
- This repo, `aws-cloud-portfolio`, is my public portfolio. All ticket work arrives through pull requests.
- Starter kit: `.gitignore` (blocks secrets, Terraform state, build output), a PR template, `tools/verify-workstation.sh`, and `docs/POSTMORTEM_TEMPLATE.md`.
- A ruleset called `protect-main` on the default branch: requires a pull request before merging (0 approvals). The bypass list is empty, so it applies to me as admin too. Required approvals is 0 because I am the only engineer.

## Why
Nothing reaches `main` without a pull request. Every change gets a branch, a description and a reviewable diff, the same habit a real team expects. The `.gitignore` is a second safety net against committing keys.

## How to verify
1. Try `git push origin main` with a local commit: GitHub refuses with `GH013 ... Changes must be made through a pull request` (full output in evidence.md).
2. Settings → Rules → Rulesets → `protect-main`: see ruleset.png.
3. PR #1 (`setup-workstation`) was merged through the PR flow: https://github.com/SabStha/aws-cloud-portfolio/pull/1

## Problems I hit and how I fixed them
1. I didn't understand that Git on my PC and GitHub are separate. Nothing is uploaded until I commit and push, and a PR is how a branch gets into `main`.
2. `gh auth login` couldn't open a browser from WSL. Fix: I opened github.com/login/device in Windows and typed the one-time code.
3. My first SW-001 push had an empty folder, so nothing was committed. Git does not track empty folders; it needs at least one file.
4. To prove the rule, I made a test commit on `main`, watched the push get rejected, then removed it with `git reset --hard origin/main` so my local `main` matched GitHub again.

## What I learned
Branch → commit → push → pull request → merge. Branch protection only proves something when the bypass list is empty.
