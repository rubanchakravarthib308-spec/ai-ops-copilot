# Observability and incident connector adapters

External operational data is intentionally kept behind provider-neutral read interfaces.

## Interfaces

`ObservabilityConnector` and `IncidentConnector` both expose:

```python
def read_evidence(incident: Incident) -> tuple[NormalizedEvidence, ...]: ...
```

`NormalizedEvidence` gives the workflow one stable shape across metrics, logs, alerts, incident notes, and ticket systems:

```python
NormalizedEvidence(source="metrics", kind="signal", value="5xx outage")
```

The workflow converts normalized evidence into classifier signals, records an `external_read` audit event, and then continues through the normal classifier, runbook, policy, risk, and approval gates.

## Failure behavior

Configured connector reads fail closed. A `ConnectorError` produces an `external_read_failed` audit event and blocks the workflow before a recommendation is created. This prevents the system from silently acting as though required external evidence was available.

## Adding a provider

1. Implement either `ObservabilityConnector` or `IncidentConnector`.
2. Authenticate inside the adapter, not in workflow policy.
3. Convert provider-specific responses into `NormalizedEvidence`.
4. Raise `ConnectorError` for failed or unusable reads.
5. Add deterministic tests with representative provider responses.
6. Inject the adapter into `AIOpsCopilot`.

Adapters should remain read-only unless a future explicitly controlled action interface is introduced. External systems do not gain authority to bypass model validation, runbook selection, risk policy, or human approval.

The repository includes `FakeObservabilityConnector` and `FakeIncidentConnector` so connector behavior remains testable without network access or credentials.
