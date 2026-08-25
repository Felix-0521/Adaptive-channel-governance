from channel_governance.evaluation import evaluate_partner
from channel_governance.models import ActionPriority, PartnerRecord, RecommendedActionType


def partner(**changes) -> PartnerRecord:
    values = dict(
        partner_id="P-ACTION",
        partner_name="Synthetic Action Partner",
        business_line="AGRICULTURE",
        country_code="DE",
        lifecycle_stage="MATURE",
        market_tier="HIGH_VALUE",
        partner_type="DISTRIBUTOR",
        annual_revenue=1_000_000,
        target_achievement_pct=110,
        yoy_growth_pct=30,
        new_product_contribution_pct=30,
        active_dealers=30,
        geographic_coverage_pct=90,
        inventory_days=60,
        sell_out_performance_pct=110,
        forecast_accuracy_pct=90,
        payment_on_time_pct=98,
        ar_overdue_90d_pct=0,
        certified_engineers=5,
        training_completion_pct=95,
        demo_capability=True,
        data_reporting_quality_pct=100,
        pricing_violations=0,
        unauthorized_sales_incidents=0,
        sanctions_match=False,
        material_contract_breach=False,
    )
    return PartnerRecord(**(values | changes))


def actions_by_type(result):
    return {action.action: action for action in result.recommended_actions}


def test_new_business_with_strong_technical_capability_prioritizes_market_actions(policies) -> None:
    result = evaluate_partner(
        partner(
            business_line="GEOSPATIAL",
            country_code="IT",
            lifecycle_stage="BUILD",
            market_tier="DEVELOPING",
            partner_type="DEALER",
            target_achievement_pct=55,
            yoy_growth_pct=0,
            new_product_contribution_pct=5,
            active_dealers=1,
            geographic_coverage_pct=20,
            demo_capability=False,
        ),
        policies,
    )
    actions = actions_by_type(result)
    assert actions[RecommendedActionType.CHANNEL_EXPANSION].priority == ActionPriority.HIGH
    assert actions[RecommendedActionType.DEMO_SUPPORT].priority == ActionPriority.HIGH
    assert RecommendedActionType.ENGINEER_SUPPORT not in actions


def test_mature_healthy_agriculture_partner_gets_new_product_action(policies) -> None:
    result = evaluate_partner(partner(new_product_contribution_pct=8), policies)
    actions = actions_by_type(result)
    assert actions[RecommendedActionType.NEW_PRODUCT_ENABLEMENT].priority == ActionPriority.HIGH
    assert actions[RecommendedActionType.BRANDING_MDF].priority == ActionPriority.MEDIUM
    assert actions[RecommendedActionType.NEW_PRODUCT_ENABLEMENT].evidence[
        "policy_benchmark_pct"
    ] == 20


def test_high_financial_risk_overrides_growth_actions(policies) -> None:
    result = evaluate_partner(
        partner(new_product_contribution_pct=8, ar_overdue_90d_pct=30),
        policies,
    )
    actions = actions_by_type(result)
    assert actions[RecommendedActionType.CREDIT_REVIEW].priority == ActionPriority.HIGH
    assert RecommendedActionType.NEW_PRODUCT_ENABLEMENT not in actions
    assert RecommendedActionType.BRANDING_MDF not in actions

