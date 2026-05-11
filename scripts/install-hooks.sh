#!/usr/bin/env bash
# Install Git hooks for the debug workflow

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(git rev-parse --show-toplevel 2>/dev/null || echo ".")"
HOOKS_DIR="$PROJECT_DIR/.git/hooks"

echo "Installing Git hooks..."

# Copy hooks
cp "$SCRIPT_DIR/commit-msg-hook.sh" "$HOOKS_DIR/commit-msg" && chmod +x "$HOOKS_DIR/commit-msg"
echo "  [OK] commit-msg hook installed"

cp "$SCRIPT_DIR/pre-commit-hook.sh" "$HOOKS_DIR/pre-commit" && chmod +x "$HOOKS_DIR/pre-commit"
echo "  [OK] pre-commit hook installed"

echo ""
echo "All hooks installed. They will run automatically on git commit."
