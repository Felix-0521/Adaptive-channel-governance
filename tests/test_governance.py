from channel_governance.evaluation import evaluate_partner
from channel_governance.governance import classify_tier
from channel_governance.models import GovernanceStatus, PartnerRecord


def healthy(**changes) -> PartnerRecord:
    values = dict(
        partner_id="P-1", partner_name="Synthetic", business_line="AGRICULTURE", country_code="PL",
        lifecycle_stage="GROWTH", market_tier="HIGH_VALUE", partner_type="DISTRIBUTOR",
        target_achievement_pct=110, yoy_growth_pct=30, new_product_contribution_pct=30,
        active_dealers=30, geographic_coverage_pct=90, inventory_days=60, sell_out_performance_pct=110,
        forecast_accuracy_pct=90, payment_on_time_pct=98, ar_overdue_90d_pct=0,
        certified_engineers=5, training_completion_pct=95, demo_capability=True,
        data_reporting_quality_pct=100, pricing_violations=0, unauthorized_sales_incidents=0,
        sanctions_match=False, material_contract_breach=False,
    )
    return PartnerRecord(**(values | changes))


def test_tier_boundaries(policies) -> None:
    policy = policies.resolve(healthy(country_code="DE"))
    assert classify_tier(None, policy) == "UNRATED"
    assert classify_tier(90, policy) == "STRATEGIC"
    assert classify_tier(75, policy) == "CORE"
    assert classify_tier(60, policy) == "DEVELOPMENT"
    assert classify_tier(59.99, policy) == "WATCHLIST"


def test_critical_gate_does_not_overwrite_high_score_or_tier(policies) -> None:
    result = evaluate_partner(healthy(unauthorized_sales_incidents=1), policies)
    assert result.score > 90
    assert result.tier == "STRATEGIC"
    assert result.governance_status == GovernanceStatus.HOLD
    assert "GATE_UNAUTHORIZED_SALES_REVIEW" in result.gate_codes


def test_high_risk_requires_review_without_gate(policies) -> None:
    result = evaluate_partner(healthy(inventory_days=150), policies)
    assert result.governance_status == GovernanceStatus.REVIEW
    assert result.gate_codes == []
    assert any(risk.code == "EXCESS_INVENTORY" for risk in result.risks)


def test_low_confidence_requires_review(policies) -> None:
    sparse = PartnerRecord(
        partner_id="P-2", partner_name="Sparse", business_line="AGRICULTURE", country_code="PL",
        lifecycle_stage="GROWTH", market_tier="HIGH_VALUE", partner_type="DISTRIBUTOR",
        target_achievement_pct=100,
    )
    result = evaluate_partner(sparse, policies)
    assert result.confidence < 0.70
    assert result.governance_status == GovernanceStatus.REVIEW
