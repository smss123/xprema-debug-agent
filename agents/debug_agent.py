#!/usr/bin/env python3
"""
Debug Agent — Main entry point for the debug workflow.

Implements the session startup protocol:
1. Load known patterns from references/debug-patterns.md
2. Classify bug
3. If known pattern → apply fix directly
4. If new → diagnose, fix, verify, audit, self-learn

Git Flow:
  - Creates fix branch: fix/debug-{pattern-id}
  - Commits fix with conventional commit message
  - Calls self-learn engine at end of session
"""

import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from audit_log import AuditLog

PATTERNS_FILE = Path("references/debug-patterns.md")
SESSION_ID = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")

# ── Session State ─────────────────────────────────────────────────────────────

audit = AuditLog(agent_id="debug-agent", ticket_id=SESSION_ID)
KNOWN_PATTERNS = {}
FIX_BRANCH = None

# ── Pattern Loading ───────────────────────────────────────────────────────────


def load_known_patterns():
    """STEP 1: Load patterns from knowledge base."""
    global KNOWN_PATTERNS
    if not PATTERNS_FILE.exists():
        print("[DEBUG-AGENT] No patterns file found — starting fresh")
        return

    content = PATTERNS_FILE.read_text()
    for match in re.finditer(
        r"### (DP-\w+-\w+)[^\n]*\n\n.*?Error Signal.*?`([^`]+)`",
        content,
        re.DOTALL,
    ):
        pattern_id = match.group(1)
        error_signal = match.group(2)
        KNOWN_PATTERNS[error_signal.lower().strip()] = pattern_id
    print(f"[DEBUG-AGENT] Loaded {len(KNOWN_PATTERNS)} known patterns")


# ── Bug Classification ────────────────────────────────────────────────────────


def classify_bug(error_signal: str, layer: str) -> dict:
    """STEP 2: Check if bug matches a known pattern."""
    norm = error_signal.lower().strip()
    for signal, pattern_id in KNOWN_PATTERNS.items():
        if norm in signal or signal in norm:
            return {
                "match": "KNOWN",
                "pattern_id": pattern_id,
                "layer": layer,
            }
    return {"match": "NEW", "layer": layer}


# ── Git Flow Operations ──────────────────────────────────────────────────────


def start_fix_branch(pattern_id: str):
    """Create a fix/debug-{pattern-id} branch off main."""
    global FIX_BRANCH
    branch = f"fix/debug-{pattern_id.lower()}"
    subprocess.run(["git", "checkout", "main"], check=True, capture_output=True)
    subprocess.run(["git", "checkout", "-b", branch, "main"], check=True, capture_output=True)
    FIX_BRANCH = branch
    print(f"[DEBUG-AGENT] Created fix branch: {branch}")


def commit_fix(pattern_id: str, description: str):
    """Commit fix with conventional commit message."""
    subprocess.run(["git", "add", "-A"], check=True, capture_output=True)
    msg = f"fix(debug): {pattern_id} — {description}"
    subprocess.run(["git", "commit", "-m", msg], check=True, capture_output=True)
    print(f"[DEBUG-AGENT] Committed: {msg}")
    return msg


def finish_fix_branch():
    """Push branch and switch back to main."""
    global FIX_BRANCH
    if not FIX_BRANCH:
        return
    try:
        subprocess.run(["git", "push", "-u", "origin", FIX_BRANCH], check=False, capture_output=True)
    except Exception:
        pass
    subprocess.run(["git", "checkout", "main"], check=True, capture_output=True)
    print(f"[DEBUG-AGENT] Branch {FIX_BRANCH} ready for PR")


# ── Main Debug Session ───────────────────────────────────────────────────────


def debug_session(error_signal: str, layer: str, description: str,
                  fix_files: list = None, fix_annotations: list = None):
    """
    Run a full debug session.

    Args:
        error_signal: The error message or symptom
        layer: ABP, Razor, Blazor, CSS, JS, ADO, EF Core
        description: Human-readable bug description
        fix_files: List of file paths that were fixed (optional)
        fix_annotations: List of (file, line, annotation) tuples (optional)
    """
    import time
    start = time.time()

    print(f"\n{'='*60}")
    print(f"  DEBUG SESSION — {SESSION_ID}")
    print(f"{'='*60}\n")

    # STEP 1: Load patterns
    print("[STEP 1] Loading known patterns...")
    load_known_patterns()

    # STEP 2: Classify
    print(f"[STEP 2] Classifying bug: '{error_signal}'")
    result = classify_bug(error_signal, layer)
    print(f"         Result: {result['match']} {result.get('pattern_id', '')}")

    if result["match"] == "KNOWN":
        print(f"         Known pattern: {result['pattern_id']} — applying documented fix")
        pattern_id = result["pattern_id"]
        audit.log(
            "debug_pattern_hit",
            detail=f"{pattern_id} matched for signal: {error_signal}",
        )
    else:
        print(f"         New bug — full diagnosis required")
        pattern_id = f"DP-{layer[:3].upper()}-NEW"

        # STEP 3: Diagnose (in real usage, this is where the agent analyzes the code)
        print(f"[STEP 3] Diagnosing... (manual or agent-driven)")
        print(f"         Layer: {layer}")
        print(f"         Signal: {error_signal}")

    # STEP 4: Fix & verify
    print(f"[STEP 4] Applying fix...")
    if fix_files:
        start_fix_branch(pattern_id)
        commit_fix(pattern_id, description)
        finish_fix_branch()

    elapsed_ms = int((time.time() - start) * 1000)

    # STEP 5: Audit
    audit.log(
        "debug_fix",
        target=f"{layer}::{description}",
        detail=f"[{pattern_id}] {description}",
        duration_ms=elapsed_ms,
    )

    # STEP 6: Self-learn
    if result["match"] == "NEW":
        print(f"[STEP 6] New pattern discovered — trigger self-learn engine")
        print(f"         Run: python agents/self_learn_engine.py <pattern.json>")
        audit.log(
            "debug_pattern_learned",
            detail=f"new pattern candidate: {pattern_id}",
        )

    print(f"\n{'='*60}")
    print(f"  Session complete — {elapsed_ms}ms")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python debug_agent.py <error_signal> <layer> [description]")
        print("Example: python debug_agent.py 'cannot resolve service' ABP 'DI error in MyAppModule'")
        sys.exit(1)

    error_signal = sys.argv[1]
    layer = sys.argv[2]
    description = sys.argv[3] if len(sys.argv) > 3 else error_signal

    debug_session(error_signal, layer, description)
