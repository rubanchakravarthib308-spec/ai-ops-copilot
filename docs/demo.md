# Demo walkthrough

The demo simulates a Sev-1 production availability incident without connecting to any real monitoring or production system.

## Scenario

```text
Production checkout API returning 5xx errors
        ↓
Availability incident + critical severity
        ↓
Availability runbook retrieved
        ↓
Rollback / failover recommendation
        ↓
High-risk gate
        ↓
Human approval
        ↓
Completed decision-support workflow
```

## Run locally

```bash
python -m pip install -e . pytest
pytest -q
python -m ai_ops_copilot.demo
```

The final JSON output contains the incident classification, selected runbook, recommendation, approval decision, and ordered audit events.

## Safety boundary

The demo never executes a rollback, restart, scaling action, or other production mutation. It demonstrates how an AI-operations workflow can investigate, retrieve known guidance, classify risk, request human judgment, and preserve evidence before a human operator acts.
