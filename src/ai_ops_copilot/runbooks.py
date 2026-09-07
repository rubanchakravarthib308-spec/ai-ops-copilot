from __future__ import annotations

from .models import Runbook


DEFAULT_RUNBOOKS: tuple[Runbook, ...] = (
    Runbook(
        id="rb-db-pool",
        title="Database connection saturation",
        category="database",
        steps=(
            "Inspect active and waiting connections.",
            "Compare pool usage with configured limits.",
            "Check recent deploys and query error rates.",
            "If saturation persists, prepare a controlled pool-capacity change.",
        ),
    ),
    Runbook(
        id="rb-latency",
        title="Application latency investigation",
        category="latency",
        steps=(
            "Confirm the latency increase across service metrics.",
            "Inspect downstream dependency latency.",
            "Compare current traces with a healthy baseline.",
            "Recommend rollback or mitigation only after evidence review.",
        ),
    ),
    Runbook(
        id="rb-availability",
        title="Service availability incident",
        category="availability",
        steps=(
            "Confirm failed health checks and affected regions.",
            "Inspect deployment and dependency health.",
            "Prepare a rollback or failover recommendation.",
        ),
        destructive=True,
    ),
    Runbook(
        id="rb-capacity",
        title="Capacity saturation investigation",
        category="capacity",
        steps=(
            "Confirm the saturated resource and trend window.",
            "Identify the top consuming process or workload.",
            "Prepare a reversible scaling recommendation.",
        ),
    ),
)


def retrieve_runbook(category: str, runbooks: tuple[Runbook, ...] = DEFAULT_RUNBOOKS) -> Runbook | None:
    return next((runbook for runbook in runbooks if runbook.category == category), None)
