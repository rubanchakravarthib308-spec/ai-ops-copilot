# AI Ops Copilot

> **A production-minded incident triage copilot — classify, investigate, retrieve runbooks, assess risk, request human approval, and preserve an audit trail.**

Most AI-operations demos jump straight from an alert to a suggested fix. Real operational systems need stronger boundaries: **evidence, known runbooks, explicit risk, human judgment for consequential actions, and a record of why the recommendation was made.**

This project is a compact reference implementation of that workflow.

## Core flow

```text
Incident
  ↓
Classification + severity
  ↓
Evidence extraction
  ↓
Runbook retrieval
  ↓
Recommendation
  ↓
Risk gate
  ↓
Human approval when required
  ↓
Audited recommendation ready for operator action
```

## What this demonstrates

- Incident classification with explicit evidence
- Runbook retrieval from a controlled registry
- Severity-aware recommendation policy
- Human approval for high-risk operations
- Explicit blocked / failed / completed states
- Audit events for important decisions
- Deterministic offline demo — no API key required
- Automated tests for safety boundaries
- GitHub Actions CI

## Important boundary

This repository **does not autonomously mutate production systems**.

A `completed` workflow means the recommendation has passed the configured decision gates and is ready for a human operator. Unknown incidents or missing runbooks are blocked rather than answered with unsupported advice.

That boundary is deliberate.

## Example incident

```text
Checkout API returning 5xx errors
        ↓
Category: availability
Severity: critical
        ↓
Availability runbook retrieved
        ↓
Prepare rollback / failover recommendation
        ↓
Risk: high
        ↓
Human approval required
        ↓
Recommendation + audit evidence
```

## Project structure

```text
src/ai_ops_copilot/
  classifier.py   # deterministic incident classification
  runbooks.py     # controlled runbook registry + retrieval
  policy.py       # recommendation and risk policy
  copilot.py      # workflow orchestration and approval gate
  models.py       # typed domain model
  demo.py         # deterministic end-to-end scenario

tests/
  test_copilot.py

docs/
  architecture.md
  demo.md
```

## Run locally

Requirements: Python 3.11+

```bash
python -m pip install -e . pytest
pytest -q
python -m ai_ops_copilot.demo
```

No API key or production access is required.

## Design principles

1. **Evidence before recommendation** — classification exposes signals rather than hiding the reasoning path.
2. **Known guidance before improvisation** — recommendations are grounded in registered runbooks.
3. **Block when knowledge is missing** — an unknown category does not receive invented operational advice.
4. **Risk changes the workflow** — high-risk recommendations require approval.
5. **Humans remain accountable** — this version produces decision support, not autonomous production mutations.
6. **Every important transition is auditable** — the workflow records why it reached its final state.

## Current maturity

**v0.1 — incident triage and control workflow**

Implemented:

- deterministic incident classification
- severity assessment
- runbook retrieval
- recommendation risk policy
- human approval gate
- explicit blocked and completed states
- audit trail
- safety-focused tests
- CI
- architecture and demo documentation

Next:

- pluggable LLM classifier with structured output validation
- semantic runbook retrieval
- observability / telemetry adapters
- incident timeline summarization
- recommendation confidence and evidence coverage
- time-bound approval fingerprints
- durable incident and audit persistence
- ServiceNow / PagerDuty-style connector abstractions

## Why I built this

My background is in enterprise technology, and I’m transitioning deeper into AI engineering. Operations is a useful place to connect both worlds: the AI has to understand messy real signals, respect business risk, interact with known procedures, and know when a person must make the final call.

This repository is public engineering proof of that transition — focused on **Agentic AI, enterprise automation, workflow orchestration, human-in-the-loop controls, and reliable decision support**.

---

Built by **Ruban Chakravarthi** as part of a hands-on AI engineering portfolio.
