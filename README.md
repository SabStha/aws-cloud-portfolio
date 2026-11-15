# AWS Cloud Portfolio · Sabin Shrestha

Hands-on AWS infrastructure work on my own AWS account: designing, building, securing, troubleshooting and documenting. My focus is cloud infrastructure and operations, moving toward cloud security.

AWS Certified Cloud Practitioner · Studying for AWS Solutions Architect – Associate (SAA-C03) · Based in Japan (JLPT N2) · [LinkedIn](https://www.linkedin.com/in/sabinshrestha-sec/)

## Start here

| | Work | What it shows |
|---|---|---|
| 🔥 | [INC-0001: Lambda AccessDeniedException](projects/lambda-dynamodb-least-privilege/POSTMORTEM.md) | Reproduced an IAM failure on purpose, fixed it with one action on one table, and found that the correct fix took **5 min 19 s** to apply (IAM eventual consistency). Full postmortem. |
| 💸 | [cost-check](projects/aws-cost-check/) | One command that finds anything still billing, in every enabled region, and exits 1 so it can block a clock-out. Includes what went wrong: parallel runs got *slower* (29 s → 64 s) and why. |
| 🔐 | [Account guardrails](projects/aws-account-guardrails/) | Root locked down, IAM Identity Center with short-lived credentials, 5 USD budget with 4 alerts, zero-spend budget, anomaly detection. |

## Work log

| Ticket | Work | Skills | Status |
|---|---|---|---|
| SW-001 | [Engineering workstation](setup/workstation/): WSL2, AWS CLI v2, Terraform, verification script (20/20) | Linux, WSL, tooling | ✅ Reviewed |
| SW-002 | [PR workflow](setup/github-workflow/): `main` protected by a ruleset, direct push rejected | Git, GitHub | ✅ Reviewed |
| SW-003 | [Account guardrails](projects/aws-account-guardrails/) | IAM, IAM Identity Center, Budgets | ✅ Reviewed |
| SW-005 | [INC-0001 least-privilege fix](projects/lambda-dynamodb-least-privilege/) | Lambda, DynamoDB, IAM, CloudWatch Logs, AWS CLI | ✅ Reviewed |
| SW-006 | cost-check ([PR #5](https://github.com/SabStha/aws-cloud-portfolio/pull/5)) | Bash, AWS CLI, cost management | 🔍 In review |
| SW-101 | 2-AZ VPC built by hand, public vs private subnets proven from route tables | VPC, networking | ⏳ Next |

Coming up: a private EC2 host reached only through SSM Session Manager, then the same network in Terraform with remote state, then CloudWatch alarms.

## How this repo is run

The work follows **Stratus Works**, a self-directed training programme I run like a real cloud operations team: each piece of work is a ticket with acceptance criteria, it arrives as a pull request, it gets reviewed and scored, and incidents get a written postmortem. Stratus Works is a training structure, not an employer.

## How I work
- **Evidence over claims.** Every conclusion is backed by command output, logs or a test, not just "it works".
- **Least privilege.** IAM policies scoped to specific actions and resources. AWS access through IAM Identity Center with short-lived credentials; no access keys in Git.
- **Cost-aware.** Each project states what it costs, and billable resources are torn down and checked with `cost-check`.
- **Reviewable.** Changes go through pull requests with a description of what changed and how it was verified.
- **Honest about AI.** I use AI as a colleague for drafts and lookups; each README says what I wrote, what AI helped with, and how I tested it.

## Repository layout
| Folder | Contents |
|---|---|
| [`projects/`](projects/) | AWS work built end to end: scripts, policies, evidence, README and postmortems |
| [`setup/`](setup/) | Workstation and GitHub workflow setup |
| [`tools/`](tools/) | Scripts I use every day (`cost-check`, verification scripts) |