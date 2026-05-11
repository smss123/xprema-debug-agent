#!/usr/bin/env bash
# Git commit-msg hook — enforces conventional commit format for debug workflow
# Install: cp scripts/commit-msg-hook.sh .git/hooks/commit-msg

COMMIT_MSG_FILE="$1"
COMMIT_MSG=$(cat "$COMMIT_MSG_FILE")

# Allowed prefixes for this project:
#   fix(debug): ...  — bug fix
#   docs(learn): ... — pattern learning
#   chore: ...       — maintenance
#   refactor: ...    — code cleanup

ALLOWED_PREFIXES="^(fix\(debug\)|docs\(learn\)|chore|refactor|feat|docs|style|test|ci|perf|build)(\(.+\))?: .+"

if ! echo "$COMMIT_MSG" | head -1 | grep -qE "$ALLOWED_PREFIXES"; then
    echo ""
    echo "ERROR: Commit message does not follow conventional commit format."
    echo ""
    echo "Allowed formats:"
    echo "  fix(debug): pattern-id — description"
    echo "  docs(learn): add pattern DP-XXX-XXXX"
    echo "  chore: update configuration"
    echo "  feat: add new feature"
    echo ""
    echo "Your message: $COMMIT_MSG"
    echo ""
    exit 1
fi

# Warn if committing to main directly
BRANCH=$(git branch --show-current)
if [ "$BRANCH" = "main" ]; then
    echo ""
    echo "WARNING: You are committing directly to 'main'!"
    echo "Debug workflow requires branches: fix/debug-* or learn/debug-*"
    echo "Use: ./scripts/git-flow.sh start-fix <pattern-id>"
    echo ""
    # Not blocking, just warning
fi
