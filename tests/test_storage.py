from __future__ import annotations

from pathlib import Path

from ai_ops_copilot import AIOpsCopilot, Incident, SQLiteIncidentStore
from ai_ops_copilot.models import ApprovalDecision


def test_completed_workflow_survives_restart(tmp_path: Path) -> None:
    database = tmp_path / "ai-ops.db"
    incident = Incident(
        id="inc-storage-1",
        title="Production service outage",
        description="All users are affected.",
        service="checkout",
        signals=("5xx", "sev1"),
    )

    def approve(_incident_id: str, _action: str) -> ApprovalDecision:
        return ApprovalDecision(True, "on-call", "Reviewed")

    first = AIOpsCopilot(
        approval_provider=approve,
        store=SQLiteIncidentStore(database),
    )
    result = first.run(incident)

    assert result.status == "completed"

    restarted = AIOpsCopilot(store=SQLiteIncidentStore(database))
    recovered = restarted.recover(incident.id)

    assert recovered is not None
    assert recovered.status == "completed"
    assert recovered.analysis.category == "availability"
    assert recovered.recommendation is not None
    assert recovered.approval is not None
    assert recovered.approval.approved is True
    assert [event.event for event in recovered.audit] == [
        "incident_received",
        "incident_classified",
        "runbook_retrieved",
        "recommendation_created",
        "approval_decision",
        "workflow_completed",
    ]


def test_blocked_state_and_missing_approval_are_durable(tmp_path: Path) -> None:
    database = tmp_path / "ai-ops.db"
    incident = Incident(
        id="inc-storage-2",
        title="Production service outage",
        description="All users are affected.",
        service="checkout",
        signals=("5xx", "sev1"),
    )

    copilot = AIOpsCopilot(store=SQLiteIncidentStore(database))
    result = copilot.run(incident)
    recovered = AIOpsCopilot(store=SQLiteIncidentStore(database)).recover(incident.id)

    assert result.status == "blocked"
    assert recovered is not None
    assert recovered.status == "blocked"
    assert recovered.recommendation is not None
    assert recovered.approval is None
    assert recovered.audit[-1].event == "approval_required"


def test_audit_events_are_append_only_records(tmp_path: Path) -> None:
    database = tmp_path / "ai-ops.db"
    store = SQLiteIncidentStore(database)
    incident = Incident(
        id="inc-storage-3",
        title="Checkout latency degraded",
        description="Response time is slow and timeout warnings are increasing.",
        service="checkout",
    )

    AIOpsCopilot(store=store).run(incident)
    recovered = store.load_result(incident.id)

    assert recovered is not None
    assert len(recovered.audit) >= 4
    assert recovered.audit[0].event == "incident_received"
    assert recovered.audit[-1].event == "workflow_completed"
