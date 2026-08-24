from channel_governance.models import LifecycleStage, RiskSeverity, TargetAssessment, TargetRationaleInput
from channel_governance.target_rationale import assess_target


def target(**changes) -> TargetRationaleInput:
    values = dict(
        current_revenue=1_000_000, proposed_target=1_150_000, historical_growth_pct=15,
        current_sell_out_pct=108, lifecycle_stage=LifecycleStage.MATURE,
        market_capability_score=80, pipeline_value=1_800_000, new_customer_plan=2,
        coverage_pct=80, new_product_potential_pct=15, resource_commitment=True,
        inventory_days=70, ar_overdue_90d_pct=5, risk_level=RiskSeverity.LOW,
    )
    return TargetRationaleInput(**(values | changes))


def assess(inputs, policies):
    return assess_target(inputs, policies.resolve_context({}))


def test_supported_case(policies) -> None:
    result = assess(target(), policies)
    assert result.assessment == TargetAssessment.SUPPORTED
    assert result.required_growth_pct == 15


def test_stretch_case(policies) -> None:
    result = assess(target(proposed_target=1_500_000, pipeline_value=1_500_000), policies)
    assert result.assessment == TargetAssessment.STRETCH
    assert result.required_assumptions


def test_review_required_case(policies) -> None:
    result = assess(target(proposed_target=1_500_000, inventory_days=140), policies)
    assert result.assessment == TargetAssessment.REVIEW_REQUIRED


def test_insufficient_evidence_case(policies) -> None:
    result = assess(TargetRationaleInput(current_revenue=1_000_000, proposed_target=1_100_000, lifecycle_stage="MATURE"), policies)
    assert result.assessment == TargetAssessment.INSUFFICIENT_EVIDENCE


def test_entry_stage_does_not_penalize_low_historical_base(policies) -> None:
    result = assess(target(current_revenue=10_000, proposed_target=100_000, historical_growth_pct=None, lifecycle_stage="ENTRY", pipeline_value=250_000, new_customer_plan=5), policies)
    assert result.assessment == TargetAssessment.SUPPORTED


def test_mature_unrealistic_growth_requires_review(policies) -> None:
    result = assess(target(proposed_target=2_000_000, pipeline_value=300_000), policies)
    assert result.assessment == TargetAssessment.REVIEW_REQUIRED


def test_high_governance_risk_constrains_rationale(policies) -> None:
    result = assess(target(risk_level=RiskSeverity.HIGH), policies)
    assert result.assessment == TargetAssessment.REVIEW_REQUIRED
    assert any("governance" in item.lower() for item in result.constraining_drivers)


def test_missing_data_reduces_confidence(policies) -> None:
    complete = assess(target(), policies)
    incomplete = assess(target(pipeline_value=None, coverage_pct=None, new_customer_plan=None), policies)
    assert incomplete.confidence < complete.confidence
