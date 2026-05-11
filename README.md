# Debug Workflow Repository

A lightweight workflow for debugging, documenting, and self-learning patterns across ABP, Razor, Blazor, CSS, JavaScript, EF Core, and pipeline issues.

This repository contains:

- `agents/debug_agent.py` — the main debug session runner that classifies bugs and starts fix workflows.
- `agents/self_learn_engine.py` — the self-learn engine that adds or updates known bug patterns in the knowledge base.
- `references/debug-patterns.md` — the living knowledge base of debug patterns.
- `scripts/git-flow.sh` — branch management helpers for `fix/debug-*` and `learn/debug-*` workflows.
- `scripts/install-hooks.sh` and `scripts/commit-msg-hook.sh` — Git hook support for conventional commit and branch discipline.
- `agents/audit_log.py` — centralized audit logging for agent actions.

## Goals

- Capture and reuse recurring debugging patterns.
- Standardize branch naming and commit messages for fixes and learning.
- Keep all new knowledge in a versioned, reviewable knowledge base.
- Support both known-pattern fixes and new pattern discovery.

## Repository Structure

- `agents/`
  - `debug_agent.py`
  - `self_learn_engine.py`
  - `audit_log.py`
  - `team-leader/knowledge-store.md`
- `fixes/` — sample fix artifacts.
- `references/debug-patterns.md` — documented patterns.
- `scripts/` — Git workflow helpers and hook installers.

## Getting Started

### Prerequisites

- Python 3 installed
- Git repository initialized
- Optional: Azure CLI (`az`) if you want automated PR creation from the learn engine

### Install Git Hooks

Run:

```bash
./scripts/install-hooks.sh
```

This installs:

- `.git/hooks/commit-msg`
- `.git/hooks/pre-commit`

The commit hook enforces conventional commit formatting and warns if you commit directly to `main`.

## How to Use

### Fix Workflow

1. Start a fix branch:

```bash
./scripts/git-flow.sh start-fix <pattern-id> "<short title>"
```

1. Fix the code in your working tree.
1. Finish the fix branch:

```bash
./scripts/git-flow.sh finish-fix <pattern-id>
```

1. Create a PR:

```bash
./scripts/git-flow.sh create-pr fix/debug-<pattern-id>
```

### Learn Workflow

1. Start a learn branch when you want to capture a new or updated debug pattern:

```bash
./scripts/git-flow.sh start-learn <pattern-id> "<short title>"
```

1. Add or update pattern metadata.
1. Finish the learn branch:

```bash
./scripts/git-flow.sh finish-learn <pattern-id>
```

1. Create a PR if desired.

### Run the Debug Agent

The debug agent is the main session runner:

```bash
python agents/debug_agent.py "<error_signal>" <layer> "<description>"
```

Example:

```bash
python agents/debug_agent.py "cannot resolve service for type" ABP "DI error in MyAppModule"
```

- If the error signal matches an existing pattern in `references/debug-patterns.md`, the agent identifies it as a known pattern.
- If the signal is new, the agent flags it for full diagnosis and triggers the self-learn engine.

### Best Practice Prompt

When running the debug agent or documenting a new bug, keep prompts concise but informative:

- Use the exact error text or exception message for `<error_signal>`.
- Specify the targeted layer clearly (`ABP`, `Blazor`, `Razor`, `CSS`, `JavaScript`, `EF Core`, `ADO`).
- Add a short description of the failing scenario and the affected module or file.
- Prefer complete and specific symptoms over vague terms like "something broke." Example:
  - Good: `"cannot resolve service for type 'IMyService'" ABP "DI error in MyAppModule during startup"`
  - Better: `"AuthorizationException: Forbidden" ABP "Policy name mismatch in AccountController"`

This improves pattern matching, reduces false negatives, and helps the self-learn engine generate consistent debug documentation.

### Run the Self-Learn Engine

```bash
python agents/self_learn_engine.py <pattern.json> [--dry-run]
```

Example JSON payload:

```json
{
  "layer": "ABP",
  "error_signal": "cannot resolve service for type 'IMyService'",
  "root_cause": "Service module was not included in the consuming module's DependsOn list.",
  "fix_template": "Add missing module dependency.",
  "fix_code": "[DependsOn(typeof(MyServiceModule))]\\npublic class MyAppModule : AbpModule { }",
  "verification": [
    "dotnet build passes",
    "repro steps no longer throw the DI exception"
  ],
  "tags": ["di", "module", "abp"],
  "abp_version": "any",
  "dotnet_version": "any",
  "title": "DI service registration missing module dependency"
}
```

Use `--dry-run` to preview changes without committing.

## Pattern Knowledge Base

Patterns are stored in `references/debug-patterns.md`.

Each entry includes:

- `ID` and `Title`
- `Layer`
- `Error Signal`
- `ABP Version` / `.NET Version`
- `Confidence`
- `Hit Count`
- `Root Cause`
- `Fix`
- `Verification`
- `Tags`

The debug agent reads this file at startup to match known errors automatically.

## Branch and Commit Rules

- Fix branches: `fix/debug-<pattern-id>`
- Learn branches: `learn/debug-<pattern-id>`
- Commit messages should follow conventional commits, for example:
  - `fix(debug): DP-ABP-A3F1 — fix DI module registration`
  - `docs(learn): add debug pattern DP-ABP-A3F1`

## Audit Logs

Agent actions are logged to `logs/audit.jsonl`.

Use `agents/audit_log.py` to inspect log entries programmatically.

## Documentation

Detailed usage instructions are available in `docs/USAGE.md`.

## Notes

- This repository is designed for debugging workflows and pattern learning, not for production application logic.
- Keep `references/debug-patterns.md` as the single source of truth for learned debug patterns.
- Avoid committing directly to `main`; use the branch helpers and follow the branch naming conventions.
