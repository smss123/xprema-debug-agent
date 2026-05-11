#!/usr/bin/env bash
# Git pre-commit hook — checks for // FIX: annotations on changed lines
# Install: cp scripts/pre-commit-hook.sh .git/hooks/pre-commit

STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM)

if [ -z "$STAGED_FILES" ]; then
    exit 0
fi

ERRORS=0

for FILE in $STAGED_FILES; do
    # Skip non-code files
    case "$FILE" in
        *.md|*.json|*.yaml|*.yml|*.txt|*.sh|*.py) continue ;;
    esac

    # Check if file has changes that look like bug fixes (heuristic)
    # but lack FIX: annotations
    ADDED_LINES=$(git diff --cached "$FILE" | grep "^+" | grep -v "^+++" | grep -v "// FIX:" | grep -v "// DEBUG FIX:" | head -20)

    if [ -n "$ADDED_LINES" ]; then
        # This is a soft check — just warn
        echo "[HOOK] $FILE: Consider adding // FIX: annotations to changed lines"
    fi
done

exit $ERRORS
