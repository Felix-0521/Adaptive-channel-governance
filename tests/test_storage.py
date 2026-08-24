import sqlite3

from channel_governance.models import Pillar, PolicyStatus
from channel_governance.policy import PolicyLifecycleManager
from channel_governance.storage import initialize_database


ROOT_POLICY = __import__("pathlib").Path(__file__).parents[1] / "config" / "scoring_rules.yaml"
CONTEXT = {
    "business_line": "AGRICULTURE", "lifecycle_stage": "GROWTH",
    "market_tier": "HIGH_VALUE", "partner_type": "DISTRIBUTOR", "country_code": "PL",
}


def test_database_schema_is_created(tmp_path) -> None:
    database = tmp_path / "governance.db"
    initialize_database(database)
    with sqlite3.connect(database) as connection:
        tables = {
            row[0]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }
    assert {
        "evaluation_runs", "evaluation_results", "policy_state", "audit_history", "app_metadata"
    }.issubset(tables)


def test_policy_and_audit_history_survive_restart(tmp_path) -> None:
    database = tmp_path / "app.db"
    manager = PolicyLifecycleManager.from_yaml_and_sqlite(ROOT_POLICY, database)
    active = manager.active_repository().resolve_context(CONTEXT)
    weights = dict(active.pillar_weights)
    weights[Pillar.COMMERCIAL_PERFORMANCE] -= 0.05
    weights[Pillar.OPERATIONAL_HEALTH] += 0.05
    draft = manager.save_draft(
        active, pillar_weights=weights, metrics=active.metrics,
        actor="Persistence Test", change_reason="Verify restart safety",
    )
    manager.mark_scenario_tested(draft.policy_id, draft.version)
    manager.activate(
        draft.policy_id, draft.version,
        actor="Persistence Test", change_reason="Verified scenario",
    )

    restarted = PolicyLifecycleManager.from_yaml_and_sqlite(ROOT_POLICY, database)
    resolved = restarted.active_repository().resolve_context(CONTEXT)
    assert resolved.version == draft.version
    assert restarted.get(active.policy_id, active.version).status == PolicyStatus.ARCHIVED
    assert [event.action for event in restarted.audit_records] == [
        "SAVE_DRAFT", "SCENARIO_TESTED", "ACTIVATE"
    ]


def test_country_override_and_weights_are_queryable_in_sqlite(tmp_path) -> None:
    database = tmp_path / "app.db"
    PolicyLifecycleManager.from_yaml_and_sqlite(ROOT_POLICY, database)
    with sqlite3.connect(database) as connection:
        row = connection.execute(
            "SELECT country_override, weights_json, activation_state FROM policy_state "
            "WHERE country_override = 'PL'"
        ).fetchone()
    assert row[0] == "PL"
    assert "pillar_weights" in row[1] and "metric_weights" in row[1]
    assert row[2] == "ACTIVE"
