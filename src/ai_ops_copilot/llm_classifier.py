from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Protocol

from .models import Incident, IncidentAnalysis, Severity

_ALLOWED_SEVERITIES: tuple[Severity, ...] = ("low", "medium", "high", "critical")
_ALLOWED_CATEGORIES = {"database", "latency", "availability", "capacity", "unknown"}


class ClassificationValidationError(ValueError):
    """Raised when model-proposed incident analysis violates the classifier contract."""


@dataclass(frozen=True)
class ClassificationRequest:
    system_prompt: str
    user_prompt: str


class ClassificationModelProvider(Protocol):
    """Provider-neutral boundary for any LLM-backed incident classifier."""

    def generate(self, request: ClassificationRequest) -> object: ...


def validate_analysis(candidate: object) -> IncidentAnalysis:
    if not isinstance(candidate, dict):
        raise ClassificationValidationError("Classifier output must be a JSON object")

    allowed_keys = {"category", "severity", "confidence", "evidence", "rationale"}
    if set(candidate) != allowed_keys:
        raise ClassificationValidationError("Classifier output must contain only category, severity, confidence, evidence, and rationale")

    category = candidate.get("category")
    severity = candidate.get("severity")
    confidence = candidate.get("confidence")
    evidence = candidate.get("evidence")
    rationale = candidate.get("rationale")

    if not isinstance(category, str) or category not in _ALLOWED_CATEGORIES:
        raise ClassificationValidationError("Classifier returned an unsupported category")
    if not isinstance(severity, str) or severity not in _ALLOWED_SEVERITIES:
        raise ClassificationValidationError("Classifier returned an unsupported severity")
    if not isinstance(confidence, (int, float)) or isinstance(confidence, bool) or not 0.0 <= float(confidence) <= 1.0:
        raise ClassificationValidationError("Classifier confidence must be between 0 and 1")
    if not isinstance(evidence, list) or not all(isinstance(item, str) and item.strip() for item in evidence):
        raise ClassificationValidationError("Classifier evidence must be a non-empty string list")
    if not isinstance(rationale, str) or not rationale.strip():
        raise ClassificationValidationError("Classifier rationale must be a non-empty string")

    return IncidentAnalysis(
        category=category,
        severity=severity,
        confidence=round(float(confidence), 4),
        evidence=tuple(dict.fromkeys(item.strip() for item in evidence)),
        rationale=rationale.strip(),
    )


class LLMIncidentClassifier:
    """Model-backed classifier that can propose analysis but cannot control workflow policy."""

    def __init__(self, provider: ClassificationModelProvider) -> None:
        self._provider = provider

    def classify(self, incident: Incident) -> IncidentAnalysis:
        raw = self._provider.generate(
            ClassificationRequest(
                system_prompt=self._system_prompt(),
                user_prompt=(
                    f"Incident ID: {incident.id}\n"
                    f"Service: {incident.service}\n"
                    f"Title: {incident.title}\n"
                    f"Description: {incident.description}\n"
                    f"Signals: {', '.join(incident.signals) if incident.signals else 'none'}"
                ),
            )
        )

        candidate = raw
        if isinstance(raw, str):
            try:
                candidate = json.loads(raw)
            except json.JSONDecodeError as error:
                raise ClassificationValidationError("Classifier response was not valid JSON") from error

        return validate_analysis(candidate)

    @staticmethod
    def _system_prompt() -> str:
        return (
            "You are an incident classification component. You may propose category, severity, confidence, evidence, and rationale, "
            "but you have no authority to select runbooks, approve actions, or execute production changes. "
            "Return strict JSON only with exactly these fields: category, severity, confidence, evidence, rationale. "
            "Allowed categories: database, latency, availability, capacity, unknown. "
            "Allowed severities: low, medium, high, critical. Confidence must be between 0 and 1."
        )
