# Architecture

AI Ops Copilot is intentionally designed as a **decision-support and control workflow**, not an autonomous production operator.

```text
Incident
   ↓
Deterministic classification
   ↓
Evidence + severity
   ↓
Runbook retrieval
   ↓
Recommendation
   ↓
Risk policy
   ↓
Human approval when required
   ↓
Audited recommendation ready for operator action
```

## Design boundaries

### Classification
The initial implementation uses deterministic keyword rules so reviewers can inspect exactly why an incident was categorized and test the workflow without model or API credentials.

### Runbook retrieval
Runbooks are typed records with categories, steps, and a destructive-action flag. Retrieval returns only a matching registered runbook. Missing runbooks block the workflow rather than generating unsupported advice.

### Risk policy
High- and critical-severity incidents, plus destructive runbooks, require human approval. Lower-risk recommendations can proceed to a completed decision-support result without approval.

### Execution boundary
This repository does **not** execute production changes. A completed workflow means the recommendation has passed the configured decision gates and is ready for an operator to act on.

### Audit evidence
Every important transition is recorded as an audit event: receipt, classification, retrieval, recommendation creation, approval decision, and completion or blocking.

## Why this matters

A useful operations copilot must be able to say more than “here is a likely fix.” It should preserve evidence, show why a runbook was selected, expose risk, stop when evidence is insufficient, and make human responsibility explicit before consequential actions.
