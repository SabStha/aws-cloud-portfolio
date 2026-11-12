# AWS Cloud Portfolio · Sabin Shrestha

Hands-on AWS infrastructure work: designing, building, securing, troubleshooting and documenting systems on my own AWS account. My focus is cloud infrastructure and operations, moving toward cloud security.

AWS Certified Cloud Practitioner · Studying for AWS Solutions Architect – Associate (SAA-C03) · Based in Japan (JLPT N2) · [LinkedIn](https://www.linkedin.com/in/sabinshrestha-sec/)

## What's here

| Folder | What you'll find |
|---|---|
| [`projects/`](projects/) | Infrastructure I built end to end: architecture, code (AWS CLI, Terraform, Python), security decisions, cost, verification and teardown |
| [`incidents/`](incidents/) | Troubleshooting write-ups: symptom, misleading clue, key observation, root cause, fix, and the rule I took from it |
| [`notes/`](notes/) | Technical notes from hands-on experiments, with the commands and evidence behind each conclusion |

## How I work

- **Evidence over claims.** Every conclusion is backed by command output, logs or a test, not just "it works".
- **Least privilege.** IAM policies scoped to specific actions and resources. AWS access through IAM Identity Center with short-lived credentials; no access keys in Git.
- **Cost-aware.** Each project states what it costs to run, and billable resources are torn down when not in use.
- **Reviewable.** Changes go through pull requests with a description of what changed and how it was verified.

## Status

This portfolio started in November 2026. Projects, incident write-ups and notes are added as each one is finished and verified.
