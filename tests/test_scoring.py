import pytest

from channel_governance.models import MetricRule, PartnerRecord, Pillar
from channel_governance.scoring import normalize, score_partner


def test_linear_normalization_is_bounded() -> None:
    rule = MetricRule(pillar=Pillar.COMMERCIAL_PERFORMANCE, method="linear", bad=0, good=10, weight=1)
    assert normalize(-5, rule) == 0
    assert normalize(5, rule) == 50
    assert normalize(15, rule) == 100


def test_optimal_inventory_band_is_not_lower_is_better() -> None:
    rule = MetricRule(pillar=Pillar.OPERATIONAL_HEALTH, method="optimal_band", low=45, high=90, hard_low=0, hard_high=180, weight=1)
    assert normalize(60, rule) == 100
    assert normalize(0, rule) == 0
    assert normalize(180, rule) == 0


def test_missing_metric_reduces_confidence_not_score(policies) -> None:
    complete = PartnerRecord(
        partner_id="P-1", partner_name="Complete", business_line="AGRICULTURE", country_code="PL",
        lifecycle_stage="GROWTH", market_tier="HIGH_VALUE", partner_type="DISTRIBUTOR",
        target_achievement_pct=110, yoy_growth_pct=30, new_product_contribution_pct=30,
        active_dealers=30, geographic_coverage_pct=90, inventory_days=60, sell_out_performance_pct=110,
        forecast_accuracy_pct=90, payment_on_time_pct=98, ar_overdue_90d_pct=0,
        certified_engineers=5, training_completion_pct=95, demo_capability=True,
        data_reporting_quality_pct=100, pricing_violations=0, unauthorized_sales_incidents=0,
    )
    partial = complete.model_copy(update={"inventory_days": None})
    policy = policies.resolve(complete)
    complete_score, complete_confidence, *_ = score_partner(complete, policy)
    partial_score, partial_confidence, *_ = score_partner(partial, policy)
    assert complete_score == pytest.approx(100)
    assert partial_score == pytest.approx(100)
    assert partial_confidence < complete_confidence


def test_all_metrics_missing_returns_unrated_not_zero(policies) -> None:
    partner = PartnerRecord(
        partner_id="P-2", partner_name="Unknown", business_line="AGRICULTURE", country_code="PL",
        lifecycle_stage="GROWTH", market_tier="HIGH_VALUE", partner_type="DISTRIBUTOR",
    )
    score, confidence, *_ = score_partner(partner, policies.resolve(partner))
    assert score is None
    assert confidence == 0
