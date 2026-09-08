from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from .classifier import classify_incident
from .models import ApprovalDecision, AuditEvent, Incident, IncidentAnalysis, WorkflowResult
from .policy import recommend_action
from .runbooks import retrieve_runbook
from .storage import IncidentStore

ApprovalProvider = Callable[[str, str], ApprovalDecision]


class IncidentClassifier(Protocol):
    def classify(self, incident: Incident) -> IncidentAnalysis: ...


ClassifierFunction = Callable[[Incident], IncidentAnalysis]
ClassifierLike = IncidentClassifier | ClassifierFunction


def _run_classifier(classifier: ClassifierLike, incident: Incident) -> IncidentAnalysis:
    if callable(classifier):
        return classifier(incident)
    return classifier.classify(incident)


class AIOpsCopilot:
    def __init__(
        self,
        approval_provider: ApprovalProvider | None = None,
        classifier: ClassifierLike = classify_incident,
        store: IncidentStore | None = None,
    ) -> None:
        self.approval_provider = approval_provider
        self.classifier = classifier
        self.store = store

    def _persist(self, incident: Incident, result: WorkflowResult) -> WorkflowResult:
        if self.store is None:
            return result
        self.store.save_incident(incident)
        for event in result.audit:
            self.store.append_audit_event(incident.id, event)
        self.store.save_result(result)
        return result

    def recover(self, incident_id: str) -> WorkflowResult | None:
        if self.store is None:
            return None
        return self.store.load_result(incident_id)

    def run(self, incident: Incident) -> WorkflowResult:
        audit: list[AuditEvent] = [AuditEvent("incident_received", incident.title)]

        analysis = _run_classifier(self.classifier, incident)
        audit.append(
            AuditEvent(
                "incident_classified",
                f"category={analysis.category}; severity={analysis.severity}; confidence={analysis.confidence:.4f}",
            )
        )

        runbook = retrieve_runbook(analysis.category)
        if runbook is None:
            audit.append(AuditEvent("runbook_missing", analysis.category))
            return self._persist(
                incident,
                WorkflowResult(
                    incident_id=incident.id,
                    status="blocked",
                    analysis=analysis,
                    runbook=None,
                    recommendation=None,
                    approval=None,
                    audit=audit,
                ),
            )

        audit.append(AuditEvent("runbook_retrieved", runbook.id))
        recommendation = recommend_action(analysis, runbook)
        if recommendation is None:
            audit.append(AuditEvent("recommendation_failed", "No safe recommendation available"))
            return self._persist(
                incident,
                WorkflowResult(
                    incident_id=incident.id,
                    status="failed",
                    analysis=analysis,
                    runbook=runbook,
                    recommendation=None,
                    approval=None,
                    audit=audit,
                ),
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
                return self._persist(
                    incident,
                    WorkflowResult(
                        incident_id=incident.id,
                        status="blocked",
                        analysis=analysis,
                        runbook=runbook,
                        recommendation=recommendation,
                        approval=None,
                        audit=audit,
                    ),
                )

            approval = self.approval_provider(incident.id, recommendation.action)
            audit.append(
                AuditEvent(
                    "approval_decision",
                    f"approved={approval.approved}; reviewer={approval.reviewer}",
                )
            )
            if not approval.approved:
                return self._persist(
                    incident,
                    WorkflowResult(
                        incident_id=incident.id,
                        status="blocked",
                        analysis=analysis,
                        runbook=runbook,
                        recommendation=recommendation,
                        approval=approval,
                        audit=audit,
                    ),
                )

        audit.append(AuditEvent("workflow_completed", "Recommendation is ready for operator action"))
        return self._persist(
            incident,
            WorkflowResult(
                incident_id=incident.id,
                status="completed",
                analysis=analysis,
                runbook=runbook,
                recommendation=recommendation,
                approval=approval,
                audit=audit,
            ),
        )
