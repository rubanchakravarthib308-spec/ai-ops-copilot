from __future__ import annotations

from .models import IncidentAnalysis, Recommendation, Runbook


def recommend_action(analysis: IncidentAnalysis, runbook: Runbook | None) -> Recommendation | None:
    if runbook is None:
        return None

    if analysis.severity in ("high", "critical") or runbook.destructive:
        risk = "high"
        requires_approval = True
    elif analysis.severity == "medium":
        risk = "medium"
        requires_approval = False
    else:
        risk = "low"
        requires_approval = False

    action = runbook.steps[-1]
    return Recommendation(
        action=action,
        risk=risk,
        rationale=(
            f"Selected from runbook '{runbook.title}' for a {analysis.severity} "
            f"{analysis.category} incident."
        ),
        requires_approval=requires_approval,
    )
