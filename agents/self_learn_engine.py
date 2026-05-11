#!/usr/bin/env python3
"""
Self-Learn Engine — Pattern Extraction, Deduplication, Git Commit, Knowledge Store Sync

Called by debug-agent at end of every debug session.
Writes to: references/debug-patterns.md (via Git commit)

Git Flow Branching:
  - New pattern: learn/debug-{pattern-id} branch off main
  - Update existing: learn/debug-{pattern-id}-update branch off main
  - NEVER commits directly to main
"""

import json
import hashlib
import datetime
import subprocess
import re
import os
import sys
from pathlib import Path

# ── Configuration ─────────────────────────────────────────────────────────────

PATTERNS_FILE = Path("references/debug-patterns.md")
KNOWLEDGE_STORE = Path("agents/team-leader/knowledge-store.md")
AUDIT_LOG_DIR = Path("logs")

LAYER_CODES = {
    "ABP": "ABP",
    "EF Core": "EFC",
    "Razor": "RZR",
    "Blazor": "BLZ",
    "CSS": "CSS",
    "JavaScript": "JS",
    "ADO": "ADO",
    "Full-Stack": "FSK",
}

# ── Helpers ────────────────────────────────────────────────────────────────────


def normalize_signal(signal: str) -> str:
    """Strip line numbers, stack frames, lowercase, trim."""
    signal = re.sub(r"\bat\s+\w[\w.]+\s*\(.*?\)", "", signal)
    signal = re.sub(r"line\s+\d+", "", signal, flags=re.IGNORECASE)
    return signal.lower().strip()


def generate_id(layer: str, error_signal: str) -> str:
    """Generate deterministic pattern ID: DP-{LAYER_CODE}-{HASH4}"""
    code = LAYER_CODES.get(layer, "GEN")
    raw = (layer + normalize_signal(error_signal)).encode()
    hash4 = hashlib.sha256(raw).hexdigest()[:4].upper()
    return f"DP-{code}-{hash4}"


def git_run(*args, check=True):
    """Run a git command and return stdout."""
    result = subprocess.run(
        ["git"] + list(args),
        capture_output=True,
        text=True,
        check=check,
    )
    return result.stdout.strip()


def az_run(*args, check=True):
    """Run an az CLI command and return stdout."""
    result = subprocess.run(
        ["az"] + list(args),
        capture_output=True,
        text=True,
        check=check,
    )
    return result.stdout.strip()


def audit_log(agent_id: str, action: str, target: str = "",
              status: str = "success", detail: str = "", error: str = None):
    """Write an audit log entry."""
    AUDIT_LOG_DIR.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.datetime.now(
            datetime.timezone.utc
        ).isoformat(),
        "agent_id": agent_id,
        "action": action,
        "target": target,
        "status": status,
        "detail": detail,
        "error": error,
    }
    log_file = AUDIT_LOG_DIR / "audit.jsonl"
    with open(log_file, "a") as f:
        f.write(json.dumps(entry) + "\n")
    print(f"[AUDIT] {action} | {status} | {detail}")


# ── Pattern Loading ───────────────────────────────────────────────────────────


def load_existing_patterns() -> dict:
    """
    Load all patterns from debug-patterns.md.
    Returns dict: normalized_signal -> pattern_id
    """
    if not PATTERNS_FILE.exists():
        return {}
    content = PATTERNS_FILE.read_text()
    index = {}
    for match in re.finditer(
        r"### (DP-\w+-\w+).*?Error Signal.*?`([^`]+)`",
        content,
        re.DOTALL,
    ):
        pid, sig = match.group(1), match.group(2)
        index[normalize_signal(sig)] = pid
    return index


# ── Pattern Writing ───────────────────────────────────────────────────────────


def append_pattern(entry: dict):
    """Append a new pattern block to debug-patterns.md."""
    verification_md = "\n".join(
        f"{i + 1}. {v}" for i, v in enumerate(entry["verification"])
    )
    tags_md = ", ".join(f"`{t}`" for t in entry["tags"])
    lang = (
        "csharp"
        if entry["layer"] in ("ABP", "EF Core", "Razor", "Blazor")
        else "css"
        if entry["layer"] == "CSS"
        else "yaml"
        if entry["layer"] == "ADO"
        else "javascript"
    )

    block = f"""
---
### {entry['id']} — {entry['title']}

| Field | Value |
|-------|-------|
| Layer | {entry['layer']} |
| Error Signal | `{entry['error_signal']}` |
| ABP Version | {entry.get('abp_version', 'any')} |
| .NET Version | {entry.get('dotnet_version', 'any')} |
| Confidence | {entry['confidence']} |
| Hit Count | {entry['hit_count']} |
| First Seen | {entry['first_seen']} |
| Last Seen | {entry['last_seen']} |

**Root Cause:** {entry['root_cause']}

**Fix:**
```{lang}
{entry['fix_code']}
```

**Verification:**
{verification_md}

**Tags:** {tags_md}

"""
    with open(PATTERNS_FILE, "a") as f:
        f.write(block)


# ── Index Update ──────────────────────────────────────────────────────────────


def update_pattern_index(entry: dict):
    """Update the Pattern Index table at the top of debug-patterns.md."""
    if not PATTERNS_FILE.exists():
        return
    content = PATTERNS_FILE.read_text()
    # Find the last row of the index table (before the first --- separator for patterns)
    index_row = f"| {entry['id']} | {entry['layer']} | {entry['title']} | {entry['confidence']} | {entry['hit_count']} |"
    # Insert before the first pattern block
    marker = "\n---\n---\n###"
    if marker in content:
        content = content.replace(marker, f"\n{index_row}\n---\n---\n###", 1)
        PATTERNS_FILE.write_text(content)
    else:
        # If no patterns yet, append at end of index
        content += f"\n{index_row}\n"
        PATTERNS_FILE.write_text(content)


# ── Knowledge Store Sync ──────────────────────────────────────────────────────


def sync_knowledge_store(entry: dict, action: str):
    """Append entry to the knowledge store for cross-agent awareness."""
    today = datetime.date.today().isoformat()
    KNOWLEDGE_STORE.parent.mkdir(parents=True, exist_ok=True)
    line = f"- [{today}] {action}: {entry['id']} — {entry['title']} (Layer: {entry['layer']})\n"
    with open(KNOWLEDGE_STORE, "a") as f:
        f.write(line)


# ── Confidence Calculation ────────────────────────────────────────────────────


def calculate_confidence(hit_count: int) -> str:
    """Return confidence level based on hit count."""
    if hit_count >= 10:
        return "high"
    elif hit_count >= 3:
        return "medium"
    return "low"


# ── Main Learn Flow ───────────────────────────────────────────────────────────


def learn(pattern_input: dict, dry_run: bool = False):
    """
    Called by debug-agent with a PatternEntry dict.
    Handles both NEW and INCREMENT flows.

    Args:
        pattern_input: dict with keys: layer, error_signal, root_cause, fix_template,
                       fix_code, verification, tags, abp_version, dotnet_version, title
        dry_run: if True, don't actually commit to git
    """
    today = datetime.date.today().isoformat()
    existing = load_existing_patterns()
    norm_signal = normalize_signal(pattern_input["error_signal"])

    if norm_signal in existing:
        # ── INCREMENT flow ──
        pattern_id = existing[norm_signal]
        _increment_hit(pattern_id, today, dry_run=dry_run)
        sync_knowledge_store(
            {
                "id": pattern_id,
                "title": "existing pattern",
                "layer": pattern_input["layer"],
            },
            "hit",
        )
    else:
        # ── NEW PATTERN flow ──
        pattern_id = generate_id(
            pattern_input["layer"], pattern_input["error_signal"]
        )
        entry = {
            **pattern_input,
            "id": pattern_id,
            "hit_count": 1,
            "confidence": "low",
            "first_seen": today,
            "last_seen": today,
            "author": "debug-agent",
        }
        branch = f"learn/debug-{pattern_id.lower()}"

        if not dry_run:
            try:
                git_run("checkout", "-b", branch, "main")
                append_pattern(entry)
                update_pattern_index(entry)
                git_run("add", str(PATTERNS_FILE))
                git_run(
                    "commit",
                    "-m",
                    f"docs(learn): add debug pattern {pattern_id} [{entry['layer']}] {entry['title']}",
                )
                git_run("push", "origin", branch)

                # Try to create PR (may fail if az not configured)
                try:
                    az_run(
                        "repos", "pr", "create",
                        "--title", f"Learn: {pattern_id} — {entry['title']}",
                        "--description",
                        f"Auto-generated by debug-agent self-learn engine.\n"
                        f"Layer: {entry['layer']}\nSignal: {entry['error_signal']}",
                        "--source-branch", branch,
                        "--target-branch", "main",
                        "--auto-complete", "true",
                        "--delete-source-branch", "true",
                    )
                except (subprocess.CalledProcessError, FileNotFoundError):
                    print(f"[LEARN] az CLI not available — PR not created. Branch: {branch}")

                audit_log(
                    "self-learn-engine",
                    "debug_pattern_learned",
                    target=str(PATTERNS_FILE),
                    detail=f"new pattern {pattern_id}: {entry['title']}",
                )
                sync_knowledge_store(entry, "learned")
                print(f"[LEARN] New pattern committed: {pattern_id}")

            except subprocess.CalledProcessError as e:
                audit_log(
                    "self-learn-engine",
                    "debug_pattern_learned",
                    target=str(PATTERNS_FILE),
                    status="failed",
                    error=str(e),
                )
                print(f"[LEARN] Failed to commit pattern: {e}")
        else:
            print(f"[LEARN] [DRY RUN] Would create pattern {pattern_id} on branch {branch}")


def _increment_hit(pattern_id: str, today: str, dry_run: bool = False):
    """Update hit_count and last_seen in-place in the markdown file."""
    content = PATTERNS_FILE.read_text()

    # Find the block for this pattern_id and extract hit_count
    block_pattern = re.compile(
        rf"(### {re.escape(pattern_id)}.*?)(Hit Count \| )(\d+)(.*?Last Seen \| )([^\n]+)",
        re.DOTALL,
    )
    match = block_pattern.search(content)
    if not match:
        print(f"[LEARN] Cannot find block for {pattern_id} — skipping increment")
        return

    old_count = int(match.group(3))
    new_count = old_count + 1
    confidence = calculate_confidence(new_count)

    new_content = block_pattern.sub(
        lambda m: m.group(1) + m.group(2) + str(new_count) + m.group(4) + today,
        content,
        count=1,
    )
    # Also update confidence
    new_content = re.sub(
        rf"(### {re.escape(pattern_id)}.*?Confidence \| )\w+",
        lambda m: m.group(1) + confidence,
        new_content,
        count=1,
        flags=re.DOTALL,
    )

    if not dry_run:
        PATTERNS_FILE.write_text(new_content)
        branch = f"learn/debug-{pattern_id.lower()}-update"
        try:
            git_run("checkout", "-b", branch, "main")
            git_run("add", str(PATTERNS_FILE))
            git_run(
                "commit",
                "-m",
                f"docs(learn): update hit_count for {pattern_id} (now {new_count})",
            )
            git_run("push", "origin", branch)
            audit_log(
                "self-learn-engine",
                "debug_pattern_hit",
                detail=f"{pattern_id} hit_count={new_count}",
            )
            print(f"[LEARN] hit_count updated for {pattern_id}: {new_count} (confidence: {confidence})")
        except subprocess.CalledProcessError as e:
            audit_log(
                "self-learn-engine",
                "debug_pattern_hit",
                status="failed",
                error=str(e),
            )
            print(f"[LEARN] Failed to update hit_count: {e}")
    else:
        print(f"[LEARN] [DRY RUN] Would update {pattern_id}: hit_count={new_count}, confidence={confidence}")


# ── CLI Entry Point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python self_learn_engine.py <pattern.json> [--dry-run]")
        print("  pattern.json: JSON file with pattern entry data")
        print("  --dry-run: simulate without git commits")
        sys.exit(1)

    pattern_file = sys.argv[1]
    dry_run = "--dry-run" in sys.argv

    with open(pattern_file) as f:
        pattern_input = json.load(f)

    print(f"[LEARN] Processing pattern: {pattern_input.get('title', 'unknown')}")
    learn(pattern_input, dry_run=dry_run)
