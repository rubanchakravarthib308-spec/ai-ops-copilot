from __future__ import annotations

import json
from dataclasses import asdict

from .copilot import AIOpsCopilot
from .models import ApprovalDecision, Incident


def approve_demo(_incident_id: str, action: str) -> ApprovalDecision:
    return ApprovalDecision(
        approved=True,
        reviewer="demo-operator",
        note=f"Reviewed recommendation before operator action: {action}",
    )


def main() -> None:
    incident = Incident(
        id="inc-1001",
        title="Production checkout API returning 5xx errors",
        description="All users in one region are affected after a deployment.",
        service="checkout-api",
        signals=("5xx rate 38%", "health check failures", "sev1"),
    )

    result = AIOpsCopilot(approval_provider=approve_demo).run(incident)
    print(json.dumps(asdict(result), indent=2))


if __name__ == "__main__":
    main()
