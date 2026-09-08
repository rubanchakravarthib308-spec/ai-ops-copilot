# AI Ops Copilot

> **A production-minded incident triage copilot — classify, investigate, retrieve runbooks, assess risk, request human approval, and preserve an audit trail.**

Most AI-operations demos jump straight from an alert to a suggested fix. Real operational systems need stronger boundaries: **evidence, known runbooks, explicit risk, human judgment for consequential actions, and a record of why the recommendation was made.**

This project is a compact reference implementation of that workflow.

## Core flow

```text
Incident
  ↓
Classification + severity + confidence
  ↓
Structured validation
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

- Deterministic incident classification with explicit evidence
- Provider-neutral LLM classifier adapter with strict structured-output validation
- Classification confidence and evidence fields
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

A model-backed classifier may propose only category, severity, confidence, evidence, and rationale. It cannot select an approval outcome or execute a change. The proposal must pass strict validation before the existing controlled runbook, recommendation policy, risk gate, and human-approval workflow continue.

A `completed` workflow means the recommendation has passed the configured decision gates and is ready for a human operator. Unknown incidents or missing runbooks are blocked rather than answered with unsupported advice.

That boundary is deliberate.

## Example incident

```text
Checkout API returning 5xx errors
        ↓
Category: availability
Severity: critical
Confidence: 0.96
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

## Pluggable classifier

The default classifier remains deterministic and offline. A real model can be introduced through the provider-neutral `ClassificationModelProvider` interface and `LLMIncidentClassifier` adapter.

Strict model output:

```json
{
  "category": "availability",
  "severity": "critical",
  "confidence": 0.96,
  "evidence": ["5xx", "all users"],
  "rationale": "Signals indicate a production availability incident."
}
```

Malformed JSON, unsupported categories/severities, invalid confidence, empty evidence items, and extra fields are rejected before downstream workflow policy runs. See [`docs/classifier-adapters.md`](docs/classifier-adapters.md).

## Project structure

```text
src/ai_ops_copilot/
  classifier.py       # deterministic incident classification
  llm_classifier.py   # provider-neutral model adapter + strict validation
  runbooks.py         # controlled runbook registry + retrieval
  policy.py           # recommendation and risk policy
  copilot.py          # workflow orchestration and approval gate
  models.py           # typed domain model
  demo.py             # deterministic end-to-end scenario

tests/
  test_copilot.py
  test_llm_classifier.py

docs/
  architecture.md
  classifier-adapters.md
  demo.md
```

## Run locally

Requirements: Python 3.11+

```bash
python -m pip install -e . pytest
pytest -q
python -m ai_ops_copilot.demo
```

No API key or production access is required for the default demo or tests.

## Design principles

1. **Evidence before recommendation** — classification exposes signals rather than hiding the reasoning path.
2. **Model proposals are not authority** — LLM output is validated and cannot bypass workflow policy.
3. **Known guidance before improvisation** — recommendations are grounded in registered runbooks.
4. **Block when knowledge is missing** — an unknown category does not receive invented operational advice.
5. **Risk changes the workflow** — high-risk recommendations require approval.
6. **Humans remain accountable** — this version produces decision support, not autonomous production mutations.
7. **Every important transition is auditable** — the workflow records why it reached its final state.

## Current maturity

**v0.2 — pluggable classification boundary**

Implemented:

- deterministic incident classification
- provider-neutral LLM classifier adapter
- strict structured-output validation
- classification confidence and evidence
- severity assessment
- runbook retrieval
- recommendation risk policy
- human approval gate
- explicit blocked and completed states
- audit trail
- safety-focused tests
- CI
- architecture and classifier adapter documentation

Next:

- durable incident and audit persistence
- observability / telemetry adapters
- semantic runbook retrieval
- incident timeline summarization
- recommendation confidence and evidence coverage
- time-bound approval fingerprints
- ServiceNow / PagerDuty-style connector abstractions

## Why I built this

My background is in enterprise technology, and I’m transitioning deeper into AI engineering. Operations is a useful place to connect both worlds: the AI has to understand messy real signals, respect business risk, interact with known procedures, and know when a person must make the final call.

This repository is public engineering proof of that transition — focused on **Agentic AI, enterprise automation, workflow orchestration, human-in-the-loop controls, and reliable decision support**.

---

Built by **Ruban Chakravarthi** as part of a hands-on AI engineering portfolio.
