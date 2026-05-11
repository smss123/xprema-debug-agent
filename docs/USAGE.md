# Debug Workflow Usage Guide

## Overview

This guide explains how to use the debug workflow tools in this repository.

The workflow includes:

- `agents/debug_agent.py` — run debug sessions and classify bug signals
- `agents/self_learn_engine.py` — write new or update existing debug patterns
- `scripts/git-flow.sh` — branch and PR workflow helpers
- `scripts/install-hooks.sh` — install Git hooks for commit and branch discipline
- `references/debug-patterns.md` — living debug pattern knowledge base

## Install Git Hooks

Run:

```bash
./scripts/install-hooks.sh
```

This installs Git hooks that:

- enforce commit message formatting
- warn on commits directly to `main`

## Fix Workflow

### Start a fix branch

```bash
./scripts/git-flow.sh start-fix <pattern-id> "<title>"
```

Example:

```bash
./scripts/git-flow.sh start-fix ABP-A3F1 "Fix DI module dependency"
```

### Work on the fix

- Make the code changes required to resolve the bug
- Commit with a conventional message, for example:

```bash
git commit -m "fix(debug): ABP-A3F1 — fix DI module dependency"
```

### Finish the fix branch

```bash
./scripts/git-flow.sh finish-fix <pattern-id>
```

Example:

```bash
./scripts/git-flow.sh finish-fix ABP-A3F1
```

This command:

- commits any remaining staged changes
- pushes the branch to `origin`
- switches back to `main`

### Create a PR

```bash
./scripts/git-flow.sh create-pr fix/debug-<pattern-id>
```

If `az` CLI is installed, it will try to create the PR automatically.

## Learn Workflow

Use the learn workflow when a bug is new or when you want to add a new pattern entry.

### Start a learn branch

```bash
./scripts/git-flow.sh start-learn <pattern-id> "<title>"
```

Example:

```bash
./scripts/git-flow.sh start-learn ABP-A3F1 "Document DI module dependency bug"
```

### Add or update pattern metadata

Edit or add entries under `references/debug-patterns.md`, or run `python agents/self_learn_engine.py` with a JSON file.

### Finish the learn branch

```bash
./scripts/git-flow.sh finish-learn <pattern-id>
```

Example:

```bash
./scripts/git-flow.sh finish-learn ABP-A3F1
```

### Create a PR

Use `./scripts/git-flow.sh create-pr <branch>` or create a PR manually.

## Running the Debug Agent

### Debug Agent command

```bash
python agents/debug_agent.py "<error_signal>" <layer> "<description>"
```

### Debug Agent example

```bash
python agents/debug_agent.py "cannot resolve service for type" ABP "DI error in MyAppModule"
```

### What happens

- Loads known patterns from `references/debug-patterns.md`
- Attempts to classify the bug as a known pattern
- If known, logs the hit and reports the matched pattern
- If new, signals a full diagnosis and suggests using the self-learn engine

## Running the Self-Learn Engine

### Self-Learn engine command

```bash
python agents/self_learn_engine.py <pattern.json> [--dry-run]
```

### Self-Learn engine example

```bash
python agents/self_learn_engine.py new-pattern.json --dry-run
```

### Pattern payload format

Create a JSON file with keys like these:

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

### What the learn engine does

- Checks if an existing pattern already matches the normalized error signal
- If existing: increments `hit_count`, updates confidence, and pushes a learn-update branch
- If new: generates a `DP-<layer>-<hash4>` ID, appends a new entry to `references/debug-patterns.md`, and pushes a learn branch
- Optionally attempts to create a PR using `az repos pr create`

## Pattern Knowledge Base

- `references/debug-patterns.md` contains the living set of debug patterns
- Each entry includes error signals, root cause, fix details, verification steps, and metadata
- The debug agent uses this file to fast-path known issues

## Commit Message Rules

Accepted prefixes include:

- `fix(debug): ...`
- `docs(learn): ...`
- `chore: ...`
- `refactor: ...`
- `feat: ...`
- `docs: ...`
- `style: ...`
- `test: ...`
- `ci: ...`
- `perf: ...`
- `build: ...`

The commit message hook warns if you commit directly to `main`.

## Audit Log

Audit entries are written to `logs/audit.jsonl` by `agents/audit_log.py`.

Use the log for:

- tracking debug session activity
- verifying self-learn operations
- auditing branch actions
