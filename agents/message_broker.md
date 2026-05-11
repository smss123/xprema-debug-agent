# Message Broker
**Role:** Inter-Agent Communication · Event Routing
**Version:** 1.0

## Event Types

| Event | Publisher | Subscribers | When |
|-------|-----------|------------|------|
| `bug_reported` | orchestrator | debug-agent | New bug received |
| `bug_fixed` | debug-agent | self-learn-engine, audit-log | Fix applied |
| `pattern_learned` | self-learn-engine | knowledge-store | New pattern committed |
| `rollback_needed` | debug-agent | rollback-playbook | Fix caused regression |
| `pipeline_blocked` | debug-agent | azure-devops-agent | PR/CI issue |

## Conflict Resolution
If two agents modify the same file:
1. First agent to commit wins
2. Second agent must rebase before pushing
3. Orchestrator detects conflicts via `git status` and re-queues
