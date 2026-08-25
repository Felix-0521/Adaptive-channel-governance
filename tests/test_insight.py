from channel_governance.evaluation import evaluate_partner
from channel_governance.insight import INSUFFICIENT_EVIDENCE, generate_deterministic_insight
from channel_governance.models import InsightSeverity, PartnerRecord


def partner(**changes) -> PartnerRecord:
    values = dict(
        partner_id="P-INSIGHT", partner_name="Synthetic Insight Partner",
        business_line="AGRICULTURE", country_code="DE", lifecycle_stage="MATURE",
        market_tier="HIGH_VALUE", partner_type="DISTRIBUTOR", annual_revenue=1_000_000,
        target_achievement_pct=100, yoy_growth_pct=20, new_product_contribution_pct=20,
        active_dealers=20, geographic_coverage_pct=75, inventory_days=60,
        sell_out_performance_pct=100, forecast_accuracy_pct=85, payment_on_time_pct=95,
        ar_overdue_90d_pct=5, certified_engineers=4, training_completion_pct=90,
        demo_capability=True, data_reporting_quality_pct=95, pricing_violations=0,
        unauthorized_sales_incidents=0, sanctions_match=False, material_contract_breach=False,
    )
    return PartnerRecord(**(values | changes))


def insight_for(record, policies):
    result = evaluate_partner(record, policies)
    return generate_deterministic_insight(record, result, policies.resolve(record))


def test_high_risk_is_prioritized(policies) -> None:
    insight = insight_for(partner(ar_overdue_90d_pct=35), policies)
    assert insight.severity == InsightSeverity.WARNING
    assert insight.key_drivers[0].metric == "OVERDUE_AR"


def test_critical_gate_is_prioritized(policies) -> None:
    insight = insight_for(partner(sanctions_match=True), policies)
    assert insight.severity == InsightSeverity.CRITICAL
    assert insight.key_drivers[0].metric == "GATE_SANCTIONS_REVIEW"


def test_low_confidence_warning(policies) -> None:
    record = partner(**{name: None for name in ["forecast_accuracy_pct", "payment_on_time_pct", "active_dealers", "certified_engineers", "training_completion_pct", "demo_capability"]})
    insight = insight_for(record, policies)
    assert insight.severity == InsightSeverity.WARNING
    assert any(driver.metric == "confidence" for driver in insight.key_drivers)


def test_strongest_negative_driver_uses_weighted_gap(policies) -> None:
    insight = insight_for(partner(target_achievement_pct=50, yoy_growth_pct=30), policies)
    negative = [driver for driver in insight.key_drivers if driver.direction == "NEGATIVE"]
    assert negative[0].metric == "target_achievement_pct"
    assert negative[0].benchmark == ">= 110"
    assert negative[0].impact < 0


def test_missing_evidence_is_explicit_and_never_fabricates_change(policies) -> None:
    record = partner(**{name: None for name in policies.resolve(partner()).metrics})
    insight = insight_for(record, policies)
    assert insight.management_attention == INSUFFICIENT_EVIDENCE
    assert "declined" not in insight.model_dump_json().lower()
    assert "increased" not in insight.model_dump_json().lower()


def test_insight_generation_requires_no_ai_key(policies, monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    insight = insight_for(partner(), policies)
    assert insight.source == "RULES_BASED"
