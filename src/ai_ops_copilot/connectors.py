from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .models import Incident


@dataclass(frozen=True)
class NormalizedEvidence:
    source: str
    kind: str
    value: str


class ConnectorError(RuntimeError):
    pass


class ObservabilityConnector(Protocol):
    def read_evidence(self, incident: Incident) -> tuple[NormalizedEvidence, ...]: ...


class IncidentConnector(Protocol):
    def read_evidence(self, incident: Incident) -> tuple[NormalizedEvidence, ...]: ...


@dataclass(frozen=True)
class FakeObservabilityConnector:
    evidence: tuple[NormalizedEvidence, ...] = ()
    fail: bool = False

    def read_evidence(self, incident: Incident) -> tuple[NormalizedEvidence, ...]:
        if self.fail:
            raise ConnectorError(f"observability read failed for {incident.id}")
        return self.evidence


@dataclass(frozen=True)
class FakeIncidentConnector:
    evidence: tuple[NormalizedEvidence, ...] = ()
    fail: bool = False

    def read_evidence(self, incident: Incident) -> tuple[NormalizedEvidence, ...]:
        if self.fail:
            raise ConnectorError(f"incident-system read failed for {incident.id}")
        return self.evidence
