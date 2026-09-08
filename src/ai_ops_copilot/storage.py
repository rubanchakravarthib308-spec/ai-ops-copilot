from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from pathlib import Path
from typing import Protocol

from .models import ApprovalDecision, AuditEvent, Incident, IncidentAnalysis, Recommendation, WorkflowResult


class IncidentStore(Protocol):
    def save_incident(self, incident: Incident) -> None: ...
    def save_result(self, result: WorkflowResult) -> None: ...
    def append_audit_event(self, incident_id: str, event: AuditEvent) -> None: ...
    def load_result(self, incident_id: str) -> WorkflowResult | None: ...


class SQLiteIncidentStore:
    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        self._migrate()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _migrate(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                create table if not exists schema_migrations (
                    version integer primary key
                );

                create table if not exists incidents (
                    id text primary key,
                    title text not null,
                    description text not null,
                    service text not null,
                    signals_json text not null
                );

                create table if not exists workflow_results (
                    incident_id text primary key,
                    status text not null,
                    analysis_json text not null,
                    runbook_json text,
                    recommendation_json text,
                    approval_json text,
                    foreign key (incident_id) references incidents(id)
                );

                create table if not exists audit_events (
                    id integer primary key autoincrement,
                    incident_id text not null,
                    event text not null,
                    detail text not null,
                    foreign key (incident_id) references incidents(id)
                );
                """
            )
            connection.execute("insert or ignore into schema_migrations(version) values (1)")

    def save_incident(self, incident: Incident) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                insert into incidents(id, title, description, service, signals_json)
                values (?, ?, ?, ?, ?)
                on conflict(id) do update set
                    title=excluded.title,
                    description=excluded.description,
                    service=excluded.service,
                    signals_json=excluded.signals_json
                """,
                (incident.id, incident.title, incident.description, incident.service, json.dumps(incident.signals)),
            )

    def save_result(self, result: WorkflowResult) -> None:
        runbook_json = json.dumps(asdict(result.runbook)) if result.runbook is not None else None
        recommendation_json = json.dumps(asdict(result.recommendation)) if result.recommendation is not None else None
        approval_json = json.dumps(asdict(result.approval)) if result.approval is not None else None
        with self._connect() as connection:
            connection.execute(
                """
                insert into workflow_results(
                    incident_id, status, analysis_json, runbook_json, recommendation_json, approval_json
                ) values (?, ?, ?, ?, ?, ?)
                on conflict(incident_id) do update set
                    status=excluded.status,
                    analysis_json=excluded.analysis_json,
                    runbook_json=excluded.runbook_json,
                    recommendation_json=excluded.recommendation_json,
                    approval_json=excluded.approval_json
                """,
                (
                    result.incident_id,
                    result.status,
                    json.dumps(asdict(result.analysis)),
                    runbook_json,
                    recommendation_json,
                    approval_json,
                ),
            )

    def append_audit_event(self, incident_id: str, event: AuditEvent) -> None:
        with self._connect() as connection:
            connection.execute(
                "insert into audit_events(incident_id, event, detail) values (?, ?, ?)",
                (incident_id, event.event, event.detail),
            )

    def load_result(self, incident_id: str) -> WorkflowResult | None:
        with self._connect() as connection:
            row = connection.execute(
                "select * from workflow_results where incident_id = ?",
                (incident_id,),
            ).fetchone()
            if row is None:
                return None

            audit_rows = connection.execute(
                "select event, detail from audit_events where incident_id = ? order by id",
                (incident_id,),
            ).fetchall()

        analysis_data = json.loads(row["analysis_json"])
        recommendation_data = json.loads(row["recommendation_json"]) if row["recommendation_json"] else None
        approval_data = json.loads(row["approval_json"]) if row["approval_json"] else None
        runbook_data = json.loads(row["runbook_json"]) if row["runbook_json"] else None

        from .models import Runbook

        return WorkflowResult(
            incident_id=incident_id,
            status=row["status"],
            analysis=IncidentAnalysis(
                category=analysis_data["category"],
                severity=analysis_data["severity"],
                evidence=tuple(analysis_data["evidence"]),
                rationale=analysis_data["rationale"],
                confidence=float(analysis_data.get("confidence", 1.0)),
            ),
            runbook=Runbook(**{**runbook_data, "steps": tuple(runbook_data["steps"])}) if runbook_data else None,
            recommendation=Recommendation(**recommendation_data) if recommendation_data else None,
            approval=ApprovalDecision(**approval_data) if approval_data else None,
            audit=[AuditEvent(event=item["event"], detail=item["detail"]) for item in audit_rows],
        )
