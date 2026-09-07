from __future__ import annotations

from .models import Incident, IncidentAnalysis


CATEGORY_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("database", ("database", "db", "postgres", "mysql", "connection pool", "deadlock")),
    ("latency", ("latency", "slow", "timeout", "response time")),
    ("availability", ("down", "unavailable", "5xx", "outage", "health check")),
    ("capacity", ("cpu", "memory", "disk", "queue", "saturation")),
)


def classify_incident(incident: Incident) -> IncidentAnalysis:
    text = " ".join((incident.title, incident.description, *incident.signals)).lower()
    category = "unknown"
    evidence: list[str] = []

    for candidate, keywords in CATEGORY_RULES:
        hits = [keyword for keyword in keywords if keyword in text]
        if hits:
            category = candidate
            evidence.extend(hits)
            break

    severity = "low"
    if any(token in text for token in ("critical", "sev1", "production down", "all users")):
        severity = "critical"
    elif any(token in text for token in ("high", "sev2", "5xx", "outage")):
        severity = "high"
    elif any(token in text for token in ("degraded", "slow", "timeout", "warning")):
        severity = "medium"

    return IncidentAnalysis(
        category=category,
        severity=severity,
        evidence=tuple(dict.fromkeys(evidence)),
        rationale=f"Deterministic rules classified the incident as {category} with {severity} severity.",
    )
