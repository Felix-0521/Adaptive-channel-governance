"""Lifecycle-sensitive evidence check for proposed targets; never target setting."""

from __future__ import annotations

from .models import Policy, RiskSeverity, TargetAssessment, TargetRationale, TargetRationaleInput


EVIDENCE_WEIGHTS = {
    "historical_growth_pct": 0.15,
    "current_sell_out_pct": 0.15,
    "market_capability_score": 0.15,
    "pipeline_value": 0.20,
    "new_customer_plan": 0.10,
    "coverage_pct": 0.10,
    "new_product_potential_pct": 0.075,
    "resource_commitment": 0.075,
}


def _confidence(inputs: TargetRationaleInput) -> float:
    return round(sum(weight for field, weight in EVIDENCE_WEIGHTS.items() if getattr(inputs, field) is not None), 3)


def assess_target(inputs: TargetRationaleInput, policy: Policy) -> TargetRationale:
    """Assess evidence consistency without recommending or approving a target."""
    thresholds = policy.thresholds
    confidence = _confidence(inputs)
    required_growth = None
    target_multiple = None
    if inputs.current_revenue is not None and inputs.current_revenue > 0 and inputs.proposed_target is not None:
        target_multiple = inputs.proposed_target / inputs.current_revenue
        required_growth = (target_multiple - 1) * 100
    pipeline_coverage = (
        inputs.pipeline_value / inputs.proposed_target
        if inputs.pipeline_value is not None and inputs.proposed_target
        else None
    )
    sell_out_growth_proxy = (
        inputs.current_sell_out_pct - 100 if inputs.current_sell_out_pct is not None else None
    )
    target_vs_sell_out = (
        required_growth - sell_out_growth_proxy
        if required_growth is not None and sell_out_growth_proxy is not None
        else None
    )

    supporting: list[str] = []
    constraining: list[str] = []
    assumptions: list[str] = []
    if pipeline_coverage is not None:
        if pipeline_coverage >= thresholds["pipeline_coverage_supported"]:
            supporting.append(f"Pipeline coverage is {pipeline_coverage:.2f}x, above the supported threshold.")
        elif pipeline_coverage >= thresholds["pipeline_coverage_stretch"]:
            supporting.append(f"Pipeline coverage is {pipeline_coverage:.2f}x, providing partial support.")
        else:
            constraining.append(f"Pipeline coverage is only {pipeline_coverage:.2f}x of the proposed target.")
    if inputs.market_capability_score is not None:
        (supporting if inputs.market_capability_score >= 70 else constraining).append(
            f"Market capability score is {inputs.market_capability_score:.1f}."
        )
    if (inputs.new_customer_plan or 0) > 0:
        supporting.append(f"The plan includes {inputs.new_customer_plan} new customers.")
    if inputs.resource_commitment is True:
        supporting.append("Required resources are recorded as committed.")
    elif inputs.resource_commitment is False:
        constraining.append("Required resources are not recorded as committed.")

    governance_conflict = bool(inputs.gate_codes) or inputs.risk_level in {RiskSeverity.HIGH, RiskSeverity.CRITICAL}
    if governance_conflict:
        constraining.append("High-priority governance signals require review before relying on growth assumptions.")
    if inputs.inventory_days is not None and inputs.inventory_days > thresholds["inventory_days_high"]:
        constraining.append("Inventory is above the configured operating band.")
    if inputs.ar_overdue_90d_pct is not None and inputs.ar_overdue_90d_pct >= thresholds["ar_overdue_90d_high_pct"]:
        constraining.append("Over-90-day receivables are above the configured risk threshold.")

    minimum_confidence = thresholds["minimum_target_confidence"]
    early_stage = inputs.lifecycle_stage.value in {"ENTRY", "BUILD", "EMERGING"}
    if inputs.proposed_target is None or inputs.current_revenue is None or confidence < minimum_confidence:
        assessment = TargetAssessment.INSUFFICIENT_EVIDENCE
        review = "The proposed target lacks enough observed evidence for a reliable sanity check."
    elif governance_conflict:
        assessment = TargetAssessment.REVIEW_REQUIRED
        review = "The target requires management review because governance constraints conflict with growth execution."
    elif early_stage:
        if pipeline_coverage is not None and pipeline_coverage >= thresholds["pipeline_coverage_supported"] and ((inputs.new_customer_plan or 0) > 0 or (inputs.market_capability_score or 0) >= 70):
            assessment = TargetAssessment.SUPPORTED
            review = "Early-stage evidence supports the proposed target, subject to execution of the stated market-building plan."
        elif (pipeline_coverage or 0) >= thresholds["pipeline_coverage_stretch"] or (inputs.market_capability_score or 0) >= 70:
            assessment = TargetAssessment.STRETCH
            assumptions.append("Pipeline conversion and planned footprint expansion must be delivered.")
            review = "The early-stage target is a stretch supported by capability or pipeline evidence, not by the low historical base."
        else:
            assessment = TargetAssessment.REVIEW_REQUIRED
            review = "The early-stage target needs review because market-building evidence is weak."
    elif inputs.lifecycle_stage.value == "DECLINE" and (required_growth or 0) > max(inputs.historical_growth_pct or 0, 0):
        assessment = TargetAssessment.REVIEW_REQUIRED
        review = "An aggressive growth target conflicts with the decline lifecycle context and requires management review."
    else:
        reference = inputs.historical_growth_pct if inputs.historical_growth_pct is not None else sell_out_growth_proxy
        deviation = required_growth - reference if required_growth is not None and reference is not None else None
        material_conflict = (
            inputs.lifecycle_stage.value == "MATURE"
            and deviation is not None
            and deviation > thresholds["max_historical_growth_deviation"]
            and (pipeline_coverage or 0) < thresholds["pipeline_coverage_stretch"]
        ) or any("Inventory" in item or "receivables" in item for item in constraining)
        if material_conflict:
            assessment = TargetAssessment.REVIEW_REQUIRED
            review = "The proposed growth conflicts with mature-business capacity or operating constraints."
        elif deviation is not None and deviation <= thresholds["max_historical_growth_deviation"] and (pipeline_coverage is None or pipeline_coverage >= thresholds["pipeline_coverage_stretch"]):
            assessment = TargetAssessment.SUPPORTED
            review = "Observable trend and capacity evidence are broadly consistent with the proposed target."
        else:
            assessment = TargetAssessment.STRETCH
            assumptions.append("Incremental pipeline conversion must close the gap above the historical trend.")
            if inputs.resource_commitment is not True:
                assumptions.append("Management must confirm the resources required for execution.")
            review = "The target is plausible only if the listed execution assumptions are achieved."

    if not supporting:
        supporting.append("No material supporting driver was observed in the supplied fields.")
    if not constraining:
        constraining.append("No material constraint was observed in the supplied fields.")
    if assessment == TargetAssessment.STRETCH and not assumptions:
        assumptions.append("Management must validate the incremental growth assumptions.")

    return TargetRationale(
        proposed_target=inputs.proposed_target,
        required_growth_pct=None if required_growth is None else round(required_growth, 2),
        historical_growth_reference_pct=inputs.historical_growth_pct,
        pipeline_coverage_ratio=None if pipeline_coverage is None else round(pipeline_coverage, 2),
        target_vs_current_revenue=None if target_multiple is None else round(target_multiple, 2),
        target_vs_sell_out_trend_pct=None if target_vs_sell_out is None else round(target_vs_sell_out, 2),
        assessment=assessment,
        confidence=confidence,
        supporting_drivers=supporting,
        constraining_drivers=constraining,
        required_assumptions=assumptions,
        management_review=review,
    )
