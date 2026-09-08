from ai_ops_copilot import (
    AIOpsCopilot,
    FakeIncidentConnector,
    FakeObservabilityConnector,
    Incident,
    NormalizedEvidence,
)


def test_external_evidence_enriches_incident_before_classification() -> None:
    incident = Incident(
        id="inc-connector-1",
        title="Checkout warning",
        description="Customer impact is under investigation.",
        service="checkout",
    )
    observability = FakeObservabilityConnector(
        evidence=(
            NormalizedEvidence(source="metrics", kind="signal", value="5xx outage"),
            NormalizedEvidence(source="metrics", kind="scope", value="all users"),
        )
    )

    result = AIOpsCopilot(observability_connector=observability).run(incident)

    assert result.analysis.category == "availability"
    assert result.analysis.severity == "critical"
    assert any(event.event == "external_read" for event in result.audit)


def test_incident_connector_reads_are_audited() -> None:
    incident = Incident(
        id="inc-connector-2",
        title="Checkout latency degraded",
        description="Response time is slow.",
        service="checkout",
    )
    connector = FakeIncidentConnector(
        evidence=(NormalizedEvidence(source="ticket", kind="note", value="timeout warning"),)
    )

    result = AIOpsCopilot(incident_connector=connector).run(incident)

    assert result.status == "completed"
    assert any(
        event.event == "external_read" and "incident_system" in event.detail
        for event in result.audit
    )


def test_connector_failure_blocks_workflow_fail_closed() -> None:
    incident = Incident(
        id="inc-connector-3",
        title="Checkout latency degraded",
        description="Response time is slow.",
        service="checkout",
    )

    result = AIOpsCopilot(
        observability_connector=FakeObservabilityConnector(fail=True)
    ).run(incident)

    assert result.status == "blocked"
    assert result.runbook is None
    assert result.recommendation is None
    assert any(event.event == "external_read_failed" for event in result.audit)
    assert result.audit[-1].event == "workflow_blocked"
