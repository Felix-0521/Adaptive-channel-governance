"""SQLite persistence for policy state, audit history, and evaluation runs."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

from .models import AuditRecord, Policy


SCHEMA = """
CREATE TABLE IF NOT EXISTS evaluation_runs (
    run_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    policy_version TEXT NOT NULL,
    source_label TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS evaluation_results (
    run_id TEXT NOT NULL,
    partner_id TEXT NOT NULL,
    result_json TEXT NOT NULL,
    PRIMARY KEY (run_id, partner_id),
    FOREIGN KEY (run_id) REFERENCES evaluation_runs(run_id)
);
CREATE TABLE IF NOT EXISTS policy_state (
    policy_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    status TEXT NOT NULL,
    country_override TEXT,
    weights_json TEXT NOT NULL,
    scenario_tested INTEGER NOT NULL,
    activation_state TEXT NOT NULL,
    policy_json TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (policy_id, version)
);
CREATE TABLE IF NOT EXISTS audit_history (
    audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    audit_key TEXT NOT NULL UNIQUE,
    timestamp TEXT NOT NULL,
    actor TEXT NOT NULL,
    action TEXT NOT NULL,
    entity TEXT NOT NULL,
    old_value TEXT NOT NULL,
    new_value TEXT NOT NULL,
    reason TEXT NOT NULL,
    version INTEGER,
    audit_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS app_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


def initialize_database(path: str | Path) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(destination) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(SCHEMA)


class SQLitePolicyStore:
    """Transactional snapshot store; YAML remains the first-run seed."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        initialize_database(self.path)

    def has_policy_state(self) -> bool:
        with sqlite3.connect(self.path) as connection:
            return connection.execute("SELECT EXISTS(SELECT 1 FROM policy_state)").fetchone()[0] == 1

    def save(self, document_version: str, policies: list[Policy], audits: list[AuditRecord]) -> None:
        updated_at = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.path) as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("BEGIN IMMEDIATE")
            connection.execute("DELETE FROM policy_state")
            for policy in policies:
                weights = {
                    "pillar_weights": policy.model_dump(mode="json")["pillar_weights"],
                    "metric_weights": {
                        metric: rule.weight for metric, rule in policy.metrics.items()
                    },
                }
                connection.execute(
                    """INSERT INTO policy_state (
                        policy_id, version, status, country_override, weights_json,
                        scenario_tested, activation_state, policy_json, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        policy.policy_id,
                        policy.version,
                        policy.status.value,
                        policy.match.get("country_code"),
                        json.dumps(weights, sort_keys=True),
                        int(policy.scenario_tested),
                        "ACTIVE" if policy.status.value == "ACTIVE" else "INACTIVE",
                        policy.model_dump_json(),
                        updated_at,
                    ),
                )
            connection.execute(
                "INSERT OR REPLACE INTO app_metadata(key, value) VALUES ('policy_document_version', ?)",
                (document_version,),
            )
            for audit in audits:
                payload = audit.model_dump_json()
                audit_key = sha256(payload.encode("utf-8")).hexdigest()
                connection.execute(
                    """INSERT OR IGNORE INTO audit_history (
                        audit_key, timestamp, actor, action, entity, old_value,
                        new_value, reason, version, audit_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        audit_key,
                        audit.timestamp,
                        audit.actor,
                        audit.action,
                        audit.entity,
                        json.dumps(audit.old_value, sort_keys=True),
                        json.dumps(audit.new_value, sort_keys=True),
                        audit.reason or audit.change_reason,
                        audit.version or audit.new_version,
                        payload,
                    ),
                )

    def load(self) -> tuple[str, list[Policy], list[AuditRecord]]:
        with sqlite3.connect(self.path) as connection:
            version_row = connection.execute(
                "SELECT value FROM app_metadata WHERE key = 'policy_document_version'"
            ).fetchone()
            policies = [
                Policy.model_validate_json(row[0])
                for row in connection.execute(
                    "SELECT policy_json FROM policy_state ORDER BY policy_id, version"
                )
            ]
            audits = [
                AuditRecord.model_validate_json(row[0])
                for row in connection.execute(
                    "SELECT audit_json FROM audit_history ORDER BY audit_id"
                )
            ]
        return (version_row[0] if version_row else "sqlite", policies, audits)
