# Durable incident and audit storage

`AIOpsCopilot` can be constructed with an `IncidentStore` implementation. The workflow remains storage-agnostic; persistence is behind a small repository/service boundary.

## Persisted state

The reference `SQLiteIncidentStore` persists:

- incident identity and source fields
- workflow status and incident analysis
- recommendation state
- approval state
- ordered audit events

Audit rows are append-only. Workflow snapshots are upserted so the latest durable state can be recovered after a process restart.

## Restart recovery

Create a new `AIOpsCopilot` process with a store pointing at the same SQLite database and call:

```python
recovered = copilot.recover("incident-id")
```

The recovered `WorkflowResult` includes analysis, recommendation, approval, status, and ordered audit events.

## Migration strategy

The SQLite adapter owns schema initialization and records applied versions in `schema_migrations`.

Version 1 creates:

- `incidents`
- `workflow_results`
- `audit_events`

Future schema changes should be added as numbered, forward-only migrations and recorded in `schema_migrations`. Migrations should be idempotent and covered by restart/persistence tests before release.

## Production boundary

SQLite is the deterministic reference adapter for local tests and demos. A production database adapter can implement the same `IncidentStore` protocol without changing workflow policy. Storage does not grant execution authority; it only preserves workflow evidence and state.
