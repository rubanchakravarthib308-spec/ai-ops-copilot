# Classifier adapters

The incident classifier is intentionally separated from runbook selection, recommendation policy, approval, and execution authority.

A model-backed classifier may propose only:

- incident category
- severity
- confidence
- evidence
- rationale

The workflow validates that proposal before it can influence downstream policy.

## Provider-neutral boundary

Implement `ClassificationModelProvider`:

```python
from ai_ops_copilot import ClassificationRequest

class MyProvider:
    def generate(self, request: ClassificationRequest) -> object:
        # Call your chosen model here and return either a Python object
        # or strict JSON text matching the classifier schema.
        ...
```

Then inject it:

```python
from ai_ops_copilot import AIOpsCopilot, LLMIncidentClassifier

classifier = LLMIncidentClassifier(MyProvider())
copilot = AIOpsCopilot(classifier=classifier)
```

## Strict model response

```json
{
  "category": "availability",
  "severity": "critical",
  "confidence": 0.96,
  "evidence": ["5xx", "all users"],
  "rationale": "Signals indicate a production availability incident."
}
```

Allowed categories are `database`, `latency`, `availability`, `capacity`, and `unknown`.
Allowed severities are `low`, `medium`, `high`, and `critical`.
Confidence must be between `0` and `1`.
Extra fields are rejected so a model cannot smuggle in execution instructions such as `restart-production`.

## Safety chain

```text
Incident
  ↓
Model classification proposal
  ↓
Structured validation
  ↓
Controlled runbook lookup
  ↓
Deterministic recommendation policy
  ↓
Risk gate
  ↓
Human approval when required
  ↓
Audited recommendation for operator action
```

The model never chooses an approval outcome and never executes a production change. The deterministic rule classifier remains the default and requires no API key, so tests and demos stay fully offline.
