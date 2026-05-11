# Rollback Playbook
**Triggered by:** debug-agent when a fix causes a regression
**Version:** 1.0

## Rules
- NEVER rollback without logging a `rollback` audit entry
- ALWAYS identify the exact commit SHA that introduced the regression
- ALWAYS verify the system works after rollback

## Rollback Procedures

### Git Rollback (Preferred)
```bash
# Find the bad commit:
git log --oneline -10

# Revert the specific commit (creates new commit):
git revert <bad-sha> --no-edit

# Or reset to before the fix (destructive):
git reset --hard <good-sha>
git push origin <branch> --force-with-lease
```

### Branch Deletion
```bash
# Delete fix branch if fix was wrong:
git branch -D fix/debug-{pattern-id}
git push origin --delete fix/debug-{pattern-id}
```

### PR Closure
```bash
# Close PR if fix was incorrect:
az repos pr update --id {pr-id} --status "abandoned"
```

## Audit Entry
Every rollback must log:
- action: "rollback"
- target: the file/commit that was rolled back
- detail: reason for rollback
- sha: the reverted commit
