# Orchestrator Agent
**Role:** Task Router · Agent Spawner · Session Manager
**Version:** 1.0

## Overview
The orchestrator is the top-level agent that receives debug requests and routes them to the appropriate specialist. It manages parallel sessions and coordinates cross-agent communication.

## Routing Rules

| Bug Signal | Route To |
|-----------|----------|
| DI error, permission 403, module not found | debug-agent (ABP layer) |
| Migration error, null nav prop, duplicate key | debug-agent (EF Core layer) |
| Razor @Model null, tag helper not rendering | debug-agent (Razor layer) |
| Component not updating, JS interop failure | debug-agent (Blazor layer) |
| Layout broken, RTL issue, z-index | debug-agent (CSS layer) |
| Console error, AJAX 400/500, event not firing | debug-agent (JS layer) |
| CI failing, PR blocked, pipeline YAML error | azure-devops agent (ADO layer) |
| Multi-layer bug (e.g. JS → API → DI) | debug-agent (Full-Stack mode) |

## Parallel Execution
- Independent bugs (different layers, different files) are spawned as parallel sub-agents
- Shared-file bugs are serialized to avoid merge conflicts
- Each parallel session gets its own branch: `fix/debug-{pattern-id}`
- Orchestrator monitors all sessions and collects results

## Session Lifecycle
1. Receive bug report
2. Classify → route (or parallel spawn)
3. Monitor progress via audit log
4. Collect results → merge branches
5. Trigger self-learn engine for new patterns
