from pathlib import Path

import pandas as pd
import pytest

from channel_governance.evaluation import evaluate_partner
from channel_governance.governance import classify_tier
from channel_governance.models import Pillar, PolicyStatus, RecommendedActionType, ScenarioScope
from channel_governance.scenario import ScenarioService
from channel_governance.validation import require_valid_dataframe


ROOT = Path(__file__).parents[1]
FRAME = pd.read_csv(ROOT / "data" / "sample_partners.csv")
RECORDS = require_valid_dataframe(FRAME)


def test_country_override_can_define_different_tier_rules(policies) -> None:
    poland = policies.resolve_context(
        {
            "business_line": "AGRICULTURE",
            "lifecycle_stage": "GROWTH",
            "market_tier": "HIGH_VALUE",
            "partner_type": "DISTRIBUTOR",
            "country_code": "PL",
        }
    )
    germany = policies.resolve_context(
        {
            "business_line": "AGRICULTURE",
            "lifecycle_stage": "GROWTH",
            "market_tier": "HIGH_VALUE",
            "partner_type": "DISTRIBUTOR",
            "country_code": "DE",
        }
    )
    assert classify_tier(89, poland) == "STRATEGIC"
    assert classify_tier(89, germany) == "CORE"


def test_new_country_override_activation_does_not_archive_parent(policy_manager) -> None:
    country_context = {
        "business_line": "AGRICULTURE",
        "lifecycle_stage": "MATURE",
        "market_tier": "HIGH_VALUE",
        "partner_type": "DISTRIBUTOR",
        "country_code": "DE",
    }
    parent = policy_manager.active_repository().resolve_context(country_context)
    draft = policy_manager.save_draft(
        parent,
        policy_id="POL-AGR-MATURE-HV-DIST-DE",
        match=country_context,
        pillar_weights=parent.pillar_weights,
        metrics=parent.metrics,
        actor="Felix-0521",
        change_reason="Create a Germany override",
    )
    policy_manager.mark_scenario_tested(draft.policy_id, draft.version)
    policy_manager.activate(
        draft.policy_id,
        draft.version,
        actor="Felix-0521",
        change_reason="Germany scenario reviewed",
    )
    assert policy_manager.get(parent.policy_id, parent.version).status == PolicyStatus.ACTIVE
    assert policy_manager.active_repository().resolve_context(country_context).policy_id == draft.policy_id


def test_weight_only_scenario_changes_score_not_risk(policy_manager) -> None:
    context = {
        "business_line": "GEOSPATIAL",
        "lifecycle_stage": "BUILD",
        "market_tier": "DEVELOPING",
        "partner_type": "DEALER",
        "country_code": "IT",
    }
    active = policy_manager.active_repository().resolve_context(context)
    weights = {
        Pillar.COMMERCIAL_PERFORMANCE: 0.50,
        Pillar.MARKET_CAPABILITY: 0.10,
        Pillar.OPERATIONAL_HEALTH: 0.10,
        Pillar.FINANCIAL_HEALTH: 0.10,
        Pillar.SERVICE_TECH_CAPABILITY: 0.10,
        Pillar.COMPLIANCE_GOVERNANCE: 0.10,
    }
    draft = policy_manager.save_draft(
        active,
        pillar_weights=weights,
        metrics=active.metrics,
        actor="Felix-0521",
        change_reason="Weight-only scenario",
    )
    report = ScenarioService.run(
        FRAME,
        policy_manager,
        draft_policy_id=draft.policy_id,
        draft_version=draft.version,
        scope=ScenarioScope.SINGLE_PARTNER,
        partner_id="P-008",
    )
    comparison = report.comparisons[0]
    assert comparison.score_change != 0
    assert comparison.baseline_risk == comparison.scenario_risk


def test_gate_yields_governance_actions_before_growth(policies) -> None:
    partner = next(record for record in RECORDS if record.partner_id == "P-001").model_copy(
        update={"unauthorized_sales_incidents": 1}
    )
    result = evaluate_partner(partner, policies)
    action_types = {action.action for action in result.recommended_actions}
    assert action_types == {
        RecommendedActionType.COMPLIANCE_REVIEW,
        RecommendedActionType.NO_ADDITIONAL_SUPPORT,
    }


def test_selected_market_with_no_matches_is_explicitly_rejected(policy_manager) -> None:
    active = policy_manager.active_repository().resolve_context(
        {
            "business_line": "GEOSPATIAL",
            "lifecycle_stage": "BUILD",
            "market_tier": "DEVELOPING",
            "partner_type": "DEALER",
            "country_code": "IT",
        }
    )
    draft = policy_manager.save_draft(
        active,
        pillar_weights=active.pillar_weights,
        metrics=active.metrics,
        actor="Felix-0521",
        change_reason="Empty-scope validation",
    )
    with pytest.raises(ValueError, match="selected no partners"):
        ScenarioService.run(
            FRAME,
            policy_manager,
            draft_policy_id=draft.policy_id,
            draft_version=draft.version,
            scope=ScenarioScope.SELECTED_MARKET,
            filters={"country_code": "ZZ"},
        )

