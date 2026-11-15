# cost-check: find anything still costing money, in every region (SW-006)

**Script:** [`tools/cost-check`](../../tools/cost-check) · **Run it at every clock-out.**

A resource lives in exactly one region, and the console only shows the region you have selected. A disk in Osaka is invisible from Tokyo, but it still bills every hour. `cost-check` asks AWS which regions the account can use and checks each one for the things that keep billing.

## Usage
```bash
aws sso login --profile stratus
./tools/cost-check; echo $?
```
| Exit code | Meaning |
|---|---|
| `0` | Clean: nothing billable found |
| `1` | Something billable was found: clean up before clocking out |

Found rows print in red on a terminal (plain text when redirected to a file).

## What it checks
| Type | Why it costs money when forgotten |
|---|---|
| EBS volumes | billed per GB-month, attached or not (`available` = attached to nothing). Shows an estimate using the Tokyo gp3 price |
| EC2 instances (running or stopped) | running: per hour; stopped: its EBS disks still bill |
| Elastic IPs not attached | every public IPv4 address bills per hour |
| NAT gateways | per hour, even with zero traffic |
| Load balancers (ALB/NLB, Classic) | per hour plus usage |
| RDS instances | instance hours plus storage |
| Lambda functions | **listed as info only, not counted**: no cost when idle, but a forgotten function is a forgotten project |

Regions come from `aws ec2 describe-regions` at run time (no hard-coded list).

## Required IAM permissions (read-only)
`ec2:DescribeRegions`, `ec2:DescribeVolumes`, `ec2:DescribeInstances`, `ec2:DescribeAddresses`, `ec2:DescribeNatGateways`, `elasticloadbalancing:DescribeLoadBalancers`, `rds:DescribeDBInstances`, `lambda:ListFunctions`. Nothing is created or changed. Credentials come from the `stratus` SSO profile; there are no keys or account IDs in the script.

## Runtime
| Version | Time (17 regions) |
|---|---|
| Sequential, EBS check only | 29 s |
| Parallel (6 regions at a time), all checks: dirty run | 0m53.056s |
| Same, clean run | 0m53.879s |

Under the 60 s limit. The bonus goal of 20 s was **not** reached: each check starts a separate `aws` process (about 136 per run), and starting them is CPU-heavy on a laptop. Next step: rewrite in Python with boto3, so one process makes all the calls.

## Test (evidence/)
1. Created a 1 GiB gp3 volume `ghost-disk` in Osaka (ap-northeast-3).
2. Dirty run: the volume is listed with `~0.10 USD/month`, `Result: 1`, exit code 1 ([1-dirty-run.txt](evidence/1-dirty-run.txt)).
3. Deleted the volume, re-ran: `Result: 0`, exit code 0 ([2-clean-run.txt](evidence/2-clean-run.txt)).

## Problems I hit and how I fixed them
1. **`env: $'bash\r': No such file or directory`.** The file had Windows line endings (CRLF). Linux read the first line as `bash` plus a carriage return. Fixed with `sed -i 's/\r$//'`, set VS Code to LF, and added `.gitattributes` (`* text=auto eol=lf`).
2. **`Invalid endpoint: https://ec2..amazonaws.com`.** I ran a check outside the script, where `$r` was empty, so the region was missing from the URL. Lesson: set `r=ap-northeast-3` to test one command on its own.
3. **Counting broke when running in parallel.** Jobs started with `&` run in a copy of the script (a subshell), so `found=$((found+1))` never reached the main script. Fix: each region writes its rows to its own file, and the main script counts the lines after `wait`.
4. **The tool could never pass.** It counted 12 idle Lambda functions from another project, so a clean account still exited 1. A check that always fails gets ignored (alert fatigue). Fix: Lambda is listed as info and not counted.
5. **Parallel made it slower (64 s).** Starting all 17 regions × 8 checks at once overloaded the CPU (`user` time 6 min). Fix: at most 6 regions at a time (`MAX_JOBS`, `wait -n`).
6. **Cleanup used a stale volume ID.** I recreated ghost-disk, so it had a new ID, and deleting the old ID failed. Lesson: take the ID from the tool's own output, never from memory.

## How it was built
Core loop, region discovery, EBS check and exit code written by me. The other checks and the parallel version were drafted with AI help, then reviewed line by line and tested by me.
