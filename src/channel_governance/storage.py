"""Small SQLite boundary for later audit and evaluation persistence."""

from __future__ import annotations

import sqlite3
from pathlib import Path


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
"""


def initialize_database(path: str | Path) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(destination) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(SCHEMA)

