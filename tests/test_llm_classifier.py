import pytest

from ai_ops_copilot import AIOpsCopilot, Incident
from ai_ops_copilot.llm_classifier import (
    ClassificationRequest,
    ClassificationValidationError,
    LLMIncidentClassifier,
)


class StaticProvider:
    def __init__(self, response: object) -> None:
        self.response = response
        self.requests: list[ClassificationRequest] = []

    def generate(self, request: ClassificationRequest) -> object:
        self.requests.append(request)
        return self.response


def incident() -> Incident:
    return Incident(
        id="inc-llm-1",
        title="Checkout API is unavailable",
        description="Production traffic is returning 5xx errors for all users.",
        service="checkout",
        signals=("5xx", "sev1"),
    )


def test_llm_classifier_accepts_valid_structured_output() -> None:
    provider = StaticProvider(
        {
            "category": "availability",
            "severity": "critical",
            "confidence": 0.96,
            "evidence": ["5xx", "all users"],
            "rationale": "Signals indicate a production availability incident.",
        }
    )

    analysis = LLMIncidentClassifier(provider).classify(incident())

    assert analysis.category == "availability"
    assert analysis.severity == "critical"
    assert analysis.confidence == 0.96
    assert analysis.evidence == ("5xx", "all users")
    assert len(provider.requests) == 1


def test_llm_classifier_accepts_strict_json_text() -> None:
    provider = StaticProvider(
        '{"category":"availability","severity":"high","confidence":0.88,"evidence":["5xx"],"rationale":"Availability signal detected."}'
    )

    analysis = LLMIncidentClassifier(provider).classify(incident())

    assert analysis.category == "availability"
    assert analysis.confidence == 0.88


def test_malformed_json_is_rejected() -> None:
    provider = StaticProvider("not-json")

    with pytest.raises(ClassificationValidationError, match="valid JSON"):
        LLMIncidentClassifier(provider).classify(incident())


def test_extra_model_fields_are_rejected() -> None:
    provider = StaticProvider(
        {
            "category": "availability",
            "severity": "critical",
            "confidence": 0.95,
            "evidence": ["5xx"],
            "rationale": "Outage detected.",
            "action": "restart-production",
        }
    )

    with pytest.raises(ClassificationValidationError, match="contain only"):
        LLMIncidentClassifier(provider).classify(incident())


def test_invalid_confidence_is_rejected() -> None:
    provider = StaticProvider(
        {
            "category": "availability",
            "severity": "critical",
            "confidence": 1.5,
            "evidence": ["5xx"],
            "rationale": "Outage detected.",
        }
    )

    with pytest.raises(ClassificationValidationError, match="between 0 and 1"):
        LLMIncidentClassifier(provider).classify(incident())


def test_model_classification_still_flows_through_policy_and_approval_gate() -> None:
    provider = StaticProvider(
        {
            "category": "availability",
            "severity": "critical",
            "confidence": 0.99,
            "evidence": ["5xx", "sev1"],
            "rationale": "Critical availability failure.",
        }
    )

    result = AIOpsCopilot(classifier=LLMIncidentClassifier(provider)).run(incident())

    assert result.status == "blocked"
    assert result.recommendation is not None
    assert result.recommendation.requires_approval is True
    assert result.approval is None
    assert any(event.event == "approval_required" for event in result.audit)
