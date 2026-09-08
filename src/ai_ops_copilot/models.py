from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Severity = Literal["low", "medium", "high", "critical"]
RiskLevel = Literal["low", "medium", "high"]
WorkflowStatus = Literal["completed", "blocked", "failed"]


@dataclass(frozen=True)
class Incident:
    id: str
    title: str
    description: str
    service: str
    signals: tuple[str, ...] = ()


@dataclass(frozen=True)
class IncidentAnalysis:
    category: str
    severity: Severity
    evidence: tuple[str, ...]
    rationale: str
    confidence: float = 1.0


@dataclass(frozen=True)
class Runbook:
    id: str
    title: str
    category: str
    steps: tuple[str, ...]
    destructive: bool = False


@dataclass(frozen=True)
class Recommendation:
    action: str
    risk: RiskLevel
    rationale: str
    requires_approval: bool


@dataclass(frozen=True)
class ApprovalDecision:
    approved: bool
    reviewer: str
    note: str = ""


@dataclass(frozen=True)
class AuditEvent:
    event: str
    detail: str


@dataclass
class WorkflowResult:
    incident_id: str
    status: WorkflowStatus
    analysis: IncidentAnalysis
    runbook: Runbook | None
    recommendation: Recommendation | None
    approval: ApprovalDecision | None
    audit: list[AuditEvent] = field(default_factory=list)
