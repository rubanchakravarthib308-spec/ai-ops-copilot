from __future__ import annotations

from collections.abc import Callable

from .classifier import classify_incident
from .models import ApprovalDecision, AuditEvent, Incident, WorkflowResult
from .policy import recommend_action
from .runbooks import retrieve_runbook

ApprovalProvider = Callable[[str, str], ApprovalDecision]


class AIOpsCopilot:
    def __init__(self, approval_provider: ApprovalProvider | None = None) -> None:
        self.approval_provider = approval_provider

    def run(self, incident: Incident) -> WorkflowResult:
        audit: list[AuditEvent] = [AuditEvent("incident_received", incident.title)]

        analysis = classify_incident(incident)
        audit.append(
            AuditEvent(
                "incident_classified",
                f"category={analysis.category}; severity={analysis.severity}",
            )
        )

        runbook = retrieve_runbook(analysis.category)
        if runbook is None:
            audit.append(AuditEvent("runbook_missing", analysis.category))
            return WorkflowResult(
                incident_id=incident.id,
                status="blocked",
                analysis=analysis,
                runbook=None,
                recommendation=None,
                approval=None,
                audit=audit,
            )

        audit.append(AuditEvent("runbook_retrieved", runbook.id))
        recommendation = recommend_action(analysis, runbook)
        if recommendation is None:
            audit.append(AuditEvent("recommendation_failed", "No safe recommendation available"))
            return WorkflowResult(
                incident_id=incident.id,
                status="failed",
                analysis=analysis,
                runbook=runbook,
                recommendation=None,
                approval=None,
                audit=audit,
            )

        audit.append(
            AuditEvent(
                "recommendation_created",
                f"risk={recommendation.risk}; action={recommendation.action}",
            )
        )

        approval = None
        if recommendation.requires_approval:
            if self.approval_provider is None:
                audit.append(AuditEvent("approval_required", "No approval provider configured"))
                return WorkflowResult(
                    incident_id=incident.id,
                    status="blocked",
                    analysis=analysis,
                    runbook=runbook,
                    recommendation=recommendation,
                    approval=None,
                    audit=audit,
                )

            approval = self.approval_provider(incident.id, recommendation.action)
            audit.append(
                AuditEvent(
                    "approval_decision",
                    f"approved={approval.approved}; reviewer={approval.reviewer}",
                )
            )
            if not approval.approved:
                return WorkflowResult(
                    incident_id=incident.id,
                    status="blocked",
                    analysis=analysis,
                    runbook=runbook,
                    recommendation=recommendation,
                    approval=approval,
                    audit=audit,
                )

        audit.append(AuditEvent("workflow_completed", "Recommendation is ready for operator action"))
        return WorkflowResult(
            incident_id=incident.id,
            status="completed",
            analysis=analysis,
            runbook=runbook,
            recommendation=recommendation,
            approval=approval,
            audit=audit,
        )
