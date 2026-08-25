from pathlib import Path

import pandas as pd

from channel_governance.models import ScenarioScope
from channel_governance.scenario import ScenarioService


ROOT = Path(__file__).parents[1]
FRAME = pd.read_csv(ROOT / "data" / "sample_partners.csv")
GLOBAL_CONTEXT = {
    "business_line": "GEOSPATIAL",
    "lifecycle_stage": "BUILD",
    "market_tier": "DEVELOPING",
    "partner_type": "DEALER",
    "country_code": "IT",
}


def scenario_draft(policy_manager):
    active = policy_manager.active_repository().resolve_context(GLOBAL_CONTEXT)
    return policy_manager.save_draft(
        active,
        pillar_weights=active.pillar_weights,
        metrics=active.metrics,
        tier_rules={"STRATEGIC": 70, "CORE": 55, "DEVELOPMENT": 40},
        actor="Felix-0521",
        change_reason="Test a different tier policy",
    )


def test_single_partner_scope(policy_manager) -> None:
    draft = scenario_draft(policy_manager)
    report = ScenarioService.run(
        FRAME,
        policy_manager,
        draft_policy_id=draft.policy_id,
        draft_version=draft.version,
        scope=ScenarioScope.SINGLE_PARTNER,
        partner_id="P-008",
    )
    assert [item.partner_id for item in report.comparisons] == ["P-008"]


def test_selected_market_scope_supports_required_filters(policy_manager) -> None:
    draft = scenario_draft(policy_manager)
    report = ScenarioService.run(
        FRAME,
        policy_manager,
        draft_policy_id=draft.policy_id,
        draft_version=draft.version,
        scope=ScenarioScope.SELECTED_MARKET,
        filters={
            "country_code": "PL",
            "business_line": "AGRICULTURE",
            "market_tier": "HIGH_VALUE",
            "lifecycle_stage": "GROWTH",
        },
    )
    assert [item.partner_id for item in report.comparisons] == ["P-001"]


def test_full_portfolio_scope(policy_manager) -> None:
    draft = scenario_draft(policy_manager)
    report = ScenarioService.run(
        FRAME,
        policy_manager,
        draft_policy_id=draft.policy_id,
        draft_version=draft.version,
        scope=ScenarioScope.FULL_PORTFOLIO,
    )
    assert len(report.comparisons) == len(FRAME)


def test_scenario_never_mutates_active_policy(policy_manager) -> None:
    before = policy_manager.active_repository().resolve_context(GLOBAL_CONTEXT)
    draft = scenario_draft(policy_manager)
    ScenarioService.run(
        FRAME,
        policy_manager,
        draft_policy_id=draft.policy_id,
        draft_version=draft.version,
        scope=ScenarioScope.FULL_PORTFOLIO,
    )
    after = policy_manager.active_repository().resolve_context(GLOBAL_CONTEXT)
    assert after.version == before.version
    assert after.tier_rules == before.tier_rules


def test_tier_migration_and_risk_comparison_are_calculated(policy_manager) -> None:
    draft = scenario_draft(policy_manager)
    report = ScenarioService.run(
        FRAME,
        policy_manager,
        draft_policy_id=draft.policy_id,
        draft_version=draft.version,
        scope=ScenarioScope.FULL_PORTFOLIO,
    )
    assert report.summary.partners_upgraded > 0
    assert sum(report.summary.tier_counts_before.values()) == len(FRAME)
    assert sum(report.summary.tier_counts_after.values()) == len(FRAME)
    assert report.summary.tier_migration
    assert all(item.baseline_risk == item.scenario_risk for item in report.comparisons)

