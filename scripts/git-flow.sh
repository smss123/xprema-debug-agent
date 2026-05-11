#!/usr/bin/env bash
# Git Flow Manager for Debug Workflow
# Usage:
#   ./scripts/git-flow.sh start-fix <pattern-id> <title>
#   ./scripts/git-flow.sh start-learn <pattern-id> <title>
#   ./scripts/git-flow.sh finish-fix <pattern-id>
#   ./scripts/git-flow.sh finish-learn <pattern-id>
#   ./scripts/git-flow.sh status
#   ./scripts/git-flow.sh list-branches

set -euo pipefail

BRANCH_PREFIX_FIX="fix/debug"
BRANCH_PREFIX_LEARN="learn/debug"
DEFAULT_BRANCH="main"
COMMIT_MSG_FIX="fix(debug): "
COMMIT_MSG_LEARN="docs(learn): "

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info()  { echo -e "${BLUE}[GIT-FLOW]${NC} $1"; }
log_ok()    { echo -e "${GREEN}[GIT-FLOW]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[GIT-FLOW]${NC} $1"; }
log_error() { echo -e "${RED}[GIT-FLOW]${NC} $1"; }

validate_on_main() {
    local current
    current=$(git branch --show-current)
    if [ "$current" != "$DEFAULT_BRANCH" ]; then
        log_error "Must be on '$DEFAULT_BRANCH' to start a new branch. Current: $current"
        exit 1
    fi
}

ensure_clean() {
    local status
    status=$(git status --porcelain 2>/dev/null)
    if [ -n "$status" ]; then
        log_error "Working tree is not clean. Commit or stash changes first."
        git status --short
        exit 1
    fi
}

pull_latest() {
    log_info "Pulling latest from origin/$DEFAULT_BRANCH..."
    git pull origin "$DEFAULT_BRANCH" 2>/dev/null || log_warn "Could not pull from origin (remote may not exist)"
}

cmd_start_fix() {
    local pattern_id="$1"
    local title="$2"
    local branch="${BRANCH_PREFIX_FIX}-${pattern_id}"

    validate_on_main
    ensure_clean
    pull_latest

    if git show-ref --verify --quiet "refs/heads/$branch"; then
        log_error "Branch '$branch' already exists!"
        exit 1
    fi

    git checkout -b "$branch" "$DEFAULT_BRANCH"
    log_ok "Created and switched to: $branch"
    log_info "Pattern: $pattern_id — $title"
    log_info "Make your fixes, then run: ./scripts/git-flow.sh finish-fix $pattern_id"
}

cmd_start_learn() {
    local pattern_id="$1"
    local title="$2"
    local branch="${BRANCH_PREFIX_LEARN}-${pattern_id}"

    validate_on_main
    ensure_clean
    pull_latest

    if git show-ref --verify --quiet "refs/heads/$branch"; then
        log_error "Branch '$branch' already exists!"
        exit 1
    fi

    git checkout -b "$branch" "$DEFAULT_BRANCH"
    log_ok "Created and switched to: $branch"
    log_info "Pattern: $pattern_id — $title"
}

cmd_finish_fix() {
    local pattern_id="$1"
    local branch="${BRANCH_PREFIX_FIX}-${pattern_id}"

    local current
    current=$(git branch --show-current)
    if [ "$current" != "$branch" ]; then
        log_error "Not on branch '$branch'. Current: $current"
        exit 1
    fi

    # Check for uncommitted changes
    local status
    status=$(git status --porcelain 2>/dev/null)
    if [ -n "$status" ]; then
        log_warn "You have uncommitted changes:"
        git status --short
        log_info "Committing staged files..."
        git add -A
        git commit -m "fix(debug): ${pattern_id} — auto-committed remaining changes" || true
    fi

    log_info "Pushing $branch to origin..."
    git push -u origin "$branch" 2>/dev/null || log_warn "Could not push to origin"

    # Switch back to main
    git checkout "$DEFAULT_BRANCH"
    log_ok "Branch '$branch' pushed. Ready for PR merge."
    log_info "To create a PR, run: ./scripts/git-flow.sh create-pr $branch"
}

cmd_finish_learn() {
    local pattern_id="$1"
    local branch="${BRANCH_PREFIX_LEARN}-${pattern_id}"

    local current
    current=$(git branch --show-current)
    if [ "$current" != "$branch" ]; then
        log_error "Not on branch '$branch'. Current: $current"
        exit 1
    fi

    local status
    status=$(git status --porcelain 2>/dev/null)
    if [ -n "$status" ]; then
        log_warn "You have uncommitted changes:"
        git status --short
        git add -A
        git commit -m "docs(learn): ${pattern_id} — auto-committed remaining changes" || true
    fi

    log_info "Pushing $branch to origin..."
    git push -u origin "$branch" 2>/dev/null || log_warn "Could not push to origin"

    git checkout "$DEFAULT_BRANCH"
    log_ok "Branch '$branch' pushed. Ready for PR merge."
}

cmd_create_pr() {
    local branch="$1"
    local title="${2:-Merge $branch}"

    # Try az CLI
    if command -v az &>/dev/null; then
        az repos pr create \
            --title "$title" \
            --source-branch "$branch" \
            --target-branch "$DEFAULT_BRANCH" \
            --auto-complete true \
            --delete-source-branch true 2>/dev/null && \
            log_ok "PR created for $branch" || \
            log_warn "Failed to create PR via az CLI"
    else
        log_info "az CLI not available. Create PR manually at your Git hosting provider."
        log_info "Branch: $branch → $DEFAULT_BRANCH"
    fi
}

cmd_status() {
    echo ""
    log_info "=== Git Flow Status ==="
    echo ""

    log_info "Current branch: $(git branch --show-current)"
    echo ""

    log_info "Fix branches:"
    git branch --list "${BRANCH_PREFIX_FIX}-*" 2>/dev/null | sed 's/^/  /' || echo "  (none)"
    echo ""

    log_info "Learn branches:"
    git branch --list "${BRANCH_PREFIX_LEARN}-*" 2>/dev/null | sed 's/^/  /' || echo "  (none)"
    echo ""

    log_info "Recent commits on $(git branch --show-current):"
    git log --oneline -5 2>/dev/null | sed 's/^/  /'
    echo ""
}

cmd_list_branches() {
    echo ""
    log_info "=== All Debug Branches ==="
    echo ""
    echo "Fix branches:"
    git branch -a --list "*${BRANCH_PREFIX_FIX}-*" 2>/dev/null | sed 's/^/  /' || echo "  (none)"
    echo ""
    echo "Learn branches:"
    git branch -a --list "*${BRANCH_PREFIX_LEARN}-*" 2>/dev/null | sed 's/^/  /' || echo "  (none)"
    echo ""
}

# ── Main ──────────────────────────────────────────────────────────

case "${1:-help}" in
    start-fix)
        [ -z "${2:-}" ] && log_error "Usage: git-flow.sh start-fix <pattern-id> <title>" && exit 1
        cmd_start_fix "$2" "${3:-}"
        ;;
    start-learn)
        [ -z "${2:-}" ] && log_error "Usage: git-flow.sh start-learn <pattern-id> <title>" && exit 1
        cmd_start_learn "$2" "${3:-}"
        ;;
    finish-fix)
        [ -z "${2:-}" ] && log_error "Usage: git-flow.sh finish-fix <pattern-id>" && exit 1
        cmd_finish_fix "$2"
        ;;
    finish-learn)
        [ -z "${2:-}" ] && log_error "Usage: git-flow.sh finish-learn <pattern-id>" && exit 1
        cmd_finish_learn "$2"
        ;;
    create-pr)
        [ -z "${2:-}" ] && log_error "Usage: git-flow.sh create-pr <branch> [title]" && exit 1
        cmd_create_pr "$2" "${3:-}"
        ;;
    status)
        cmd_status
        ;;
    list-branches)
        cmd_list_branches
        ;;
    help|*)
        echo ""
        echo "Git Flow Manager for Debug Workflow"
        echo ""
        echo "Usage: ./scripts/git-flow.sh <command> [args]"
        echo ""
        echo "Commands:"
        echo "  start-fix <pattern-id> <title>    Create a new fix branch"
        echo "  start-learn <pattern-id> <title>  Create a new learn branch"
        echo "  finish-fix <pattern-id>           Push fix branch and switch to main"
        echo "  finish-learn <pattern-id>         Push learn branch and switch to main"
        echo "  create-pr <branch> [title]        Create a PR (via az CLI)"
        echo "  status                            Show current flow status"
        echo "  list-branches                     List all debug branches"
        echo "  help                              Show this help"
        echo ""
        ;;
esac
