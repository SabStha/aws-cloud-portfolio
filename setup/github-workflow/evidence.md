# SW-002 evidence

- Repo: https://github.com/SabStha/aws-cloud-portfolio
- Merged PR #1: https://github.com/SabStha/aws-cloud-portfolio/pull/1

## Criterion 3: direct push to main is rejected
```text
remote: error: GH013: Repository rule violations found for refs/heads/main.        
remote: Review all repository rules at https://github.com/SabStha/aws-cloud-portfolio/rules?ref=refs%2Fheads%2Fmain        
remote: 
remote: - Changes must be made through a pull request.        
remote: 
To github.com:SabStha/aws-cloud-portfolio.git
 ! [remote rejected] main -> main (push declined due to repository rule violations)
error: failed to push some refs to 'github.com:SabStha/aws-cloud-portfolio.git'
```

## Criterion 2: ruleset protect-main

![ruleset protect-main](ruleset.png)

## Criteria 4 and 5: PR #1 merged, commit messages
```text
cfd7ccd Merge pull request #1 from SabStha/setup-workstation
2e96d2f setup: add starter kit (gitignore, PR template, tools, docs)
9413942 setup: add wsl -l -v screenshot
c14a275 setup: add workstation README and screenshot
0b4799c setup: add workstation verification
c6bfcc5 docs: portfolio README
2f419fa Remove daily work log
cb23ef8 worklog: 2026-11-12
edd16f0 Initial commit
```

```text
PR #1 Setup workstation: MERGED, merged 2026-11-14T10:41:40Z, branch setup-workstation
```
