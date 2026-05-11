"""Audit Log — centralized logging for all agent actions."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

AUDIT_LOG_DIR = Path("logs")
AUDIT_LOG_FILE = AUDIT_LOG_DIR / "audit.jsonl"

class AuditLog:
    def __init__(self, agent_id: str, ticket_id: str = None):
        self.agent_id = agent_id
        self.ticket_id = ticket_id or "no-ticket"
        AUDIT_LOG_DIR.mkdir(parents=True, exist_ok=True)

    def log(self, action: str, target: str = "", status: str = "success",
            detail: str = "", sha: str = None, pr_id: str = None,
            duration_ms: int = None, error: str = None):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent_id": self.agent_id,
            "ticket_id": self.ticket_id,
            "action": action,
            "target": target,
            "status": status,
            "detail": detail,
            "sha": sha,
            "pr_id": pr_id,
            "duration_ms": duration_ms,
            "error": error
        }
        with open(AUDIT_LOG_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")
        return entry

    def query(self, agent_id: str = None, action: str = None, limit: int = 50):
        """Query audit log entries. Returns list of dicts."""
        if not AUDIT_LOG_FILE.exists():
            return []
        results = []
        with open(AUDIT_LOG_FILE, "r") as f:
            for line in f:
                entry = json.loads(line.strip())
                if agent_id and entry.get("agent_id") != agent_id:
                    continue
                if action and entry.get("action") != action:
                    continue
                results.append(entry)
        return results[-limit:]
