from ai_ops_copilot import AIOpsCopilot, Incident
from ai_ops_copilot.models import ApprovalDecision


def test_unknown_incident_is_blocked_without_runbook() -> None:
    incident = Incident(
        id="inc-1",
        title="Unexpected business rule warning",
        description="A non-standard condition was detected.",
        service="billing",
    )

    result = AIOpsCopilot().run(incident)

    assert result.status == "blocked"
    assert result.runbook is None
    assert result.recommendation is None


def test_high_risk_incident_requires_approval() -> None:
    incident = Incident(
        id="inc-2",
        title="Production service outage",
        description="All users are affected and health checks are failing.",
        service="checkout",
        signals=("5xx", "sev1"),
    )

    result = AIOpsCopilot().run(incident)

    assert result.status == "blocked"
    assert result.recommendation is not None
    assert result.recommendation.requires_approval is True
    assert result.approval is None


def test_denied_approval_blocks_workflow() -> None:
    incident = Incident(
        id="inc-3",
        title="Production service outage",
        description="All users are affected.",
        service="checkout",
        signals=("5xx", "outage"),
    )

    def deny(_incident_id: str, _action: str) -> ApprovalDecision:
        return ApprovalDecision(False, "on-call", "Need more evidence")

    result = AIOpsCopilot(approval_provider=deny).run(incident)

    assert result.status == "blocked"
    assert result.approval is not None
    assert result.approval.approved is False


def test_approved_high_risk_incident_completes() -> None:
    incident = Incident(
        id="inc-4",
        title="Production service outage",
        description="All users are affected.",
        service="checkout",
        signals=("5xx", "sev1"),
    )

    def approve(_incident_id: str, _action: str) -> ApprovalDecision:
        return ApprovalDecision(True, "on-call", "Reviewed")

    result = AIOpsCopilot(approval_provider=approve).run(incident)

    assert result.status == "completed"
    assert result.approval is not None
    assert result.approval.approved is True
    assert any(event.event == "workflow_completed" for event in result.audit)


def test_medium_risk_latency_incident_can_complete_without_approval() -> None:
    incident = Incident(
        id="inc-5",
        title="Checkout latency degraded",
        description="Response time is slow and timeout warnings are increasing.",
        service="checkout",
    )

    result = AIOpsCopilot().run(incident)

    assert result.status == "completed"
    assert result.recommendation is not None
    assert result.recommendation.risk == "medium"
    assert result.recommendation.requires_approval is False
