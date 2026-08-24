"""Fact-bound, deterministic management explanations."""

from __future__ import annotations

from .models import (
    DriverDirection,
    EvaluationResult,
    InsightDriver,
    InsightSeverity,
    ManagementInsight,
    MetricRule,
    PartnerRecord,
    Policy,
    RiskSeverity,
)


INSUFFICIENT_EVIDENCE = "Insufficient evidence to determine the primary cause."


def _benchmark(rule: MetricRule) -> str:
    if rule.method == "linear":
        return f">= {rule.good:g}" if rule.good is not None else "configured upper benchmark"
    if rule.method == "inverse_linear":
        return f"<= {rule.good:g}" if rule.good is not None else "configured lower benchmark"
    if rule.method == "optimal_band":
        return f"{rule.low:g}–{rule.high:g}" if rule.low is not None and rule.high is not None else "configured optimal band"
    if rule.method == "boolean":
        return "True"
    return "configured policy benchmark"


def _metric_drivers(
    partner: PartnerRecord, result: EvaluationResult, policy: Policy
) -> tuple[list[InsightDriver], list[InsightDriver]]:
    negative: list[InsightDriver] = []
    positive: list[InsightDriver] = []
    for metric, normalized in result.metric_scores.items():
        if normalized is None:
            continue
        rule = policy.metrics[metric]
        effective_weight = policy.pillar_weights[rule.pillar] * rule.weight
        contribution = round(normalized / 100 * effective_weight * 100, 2)
        gap = round((100 - normalized) / 100 * effective_weight * 100, 2)
        common = dict(
            rank=1,
            category="METRIC",
            metric=metric,
            current_value=getattr(partner, metric),
            benchmark=_benchmark(rule),
        )
        negative.append(
            InsightDriver(
                **common,
                direction=DriverDirection.NEGATIVE,
                impact=-gap,
                explanation=(
                    f"{metric} is {gap:.2f} weighted score points below its configured benchmark."
                ),
            )
        )
        positive.append(
            InsightDriver(
                **common,
                direction=DriverDirection.POSITIVE,
                impact=contribution,
                explanation=f"{metric} contributes {contribution:.2f} weighted score points.",
            )
        )
    negative.sort(key=lambda item: item.impact or 0)
    positive.sort(key=lambda item: item.impact or 0, reverse=True)
    return negative, positive


def _severity(result: EvaluationResult, minimum_confidence: float) -> InsightSeverity:
    if result.gate_codes or any(r.severity == RiskSeverity.CRITICAL for r in result.risks):
        return InsightSeverity.CRITICAL
    if any(r.severity == RiskSeverity.HIGH for r in result.risks):
        return InsightSeverity.WARNING
    if result.confidence < minimum_confidence:
        return InsightSeverity.WARNING
    if any(value is not None and value < 60 for value in result.metric_scores.values()):
        return InsightSeverity.ATTENTION
    return InsightSeverity.INFO


def generate_deterministic_insight(
    partner: PartnerRecord, result: EvaluationResult, policy: Policy
) -> ManagementInsight:
    """Explain an existing evaluation without recalculating or mutating it."""
    drivers: list[InsightDriver] = []
    for gate in result.gate_codes:
        drivers.append(
            InsightDriver(
                rank=1,
                category="GATE",
                direction=DriverDirection.GOVERNANCE,
                metric=gate,
                current_value=True,
                benchmark="Not triggered",
                explanation=f"{gate} is triggered and requires specialist review.",
            )
        )
    severity_order = {RiskSeverity.CRITICAL: 0, RiskSeverity.HIGH: 1, RiskSeverity.MEDIUM: 2, RiskSeverity.LOW: 3}
    for risk in sorted(result.risks, key=lambda item: severity_order[item.severity]):
        drivers.append(
            InsightDriver(
                rank=1,
                category="RISK",
                direction=DriverDirection.GOVERNANCE,
                metric=risk.code,
                current_value=risk.evidence or True,
                benchmark="No policy risk signal",
                explanation=risk.message,
            )
        )
    if result.confidence < policy.thresholds["minimum_confidence"]:
        drivers.append(
            InsightDriver(
                rank=1,
                category="CONFIDENCE",
                direction=DriverDirection.GOVERNANCE,
                metric="confidence",
                current_value=result.confidence,
                benchmark=f">= {policy.thresholds['minimum_confidence']:.0%}",
                impact=round(result.confidence - policy.thresholds["minimum_confidence"], 3),
                explanation="Missing scored observations reduce the reliability of the evaluation.",
            )
        )

    negative, positive = _metric_drivers(partner, result, policy)
    if negative and (negative[0].impact or 0) < 0:
        drivers.append(negative[0])
    if positive and (positive[0].impact or 0) > 0:
        drivers.append(positive[0])
    drivers = drivers[:6]
    for rank, driver in enumerate(drivers, start=1):
        driver.rank = rank

    score_text = f"{result.score:.1f}" if result.score is not None else "unavailable"
    summary = (
        f"{partner.partner_name} is classified as {result.tier} with a score of {score_text}. "
        f"Governance status is {result.governance_status.value} under {result.policy_source}."
    )
    if result.gate_codes:
        attention = "A triggered governance gate takes precedence over commercial support review."
    elif result.risks:
        strongest = sorted(result.risks, key=lambda item: severity_order[item.severity])[0]
        attention = f"Management should review {strongest.code}: {strongest.message}"
    elif negative and (negative[0].impact or 0) < -0.01:
        attention = f"The largest observable weakness is {negative[0].metric} relative to policy."
    else:
        attention = INSUFFICIENT_EVIDENCE

    next_step = (
        result.recommended_actions[0].reason
        if result.recommended_actions
        else "No new action is generated; management should review the existing evaluation."
    )
    missing = [metric for metric, score in result.metric_scores.items() if score is None]
    limitations = []
    if missing:
        limitations.append(f"Missing observations: {', '.join(missing)}.")
    limitations.append(f"Overall score confidence is {result.confidence:.0%}.")
    limitations.append("No historical observations were supplied; this insight does not claim period-over-period change.")

    return ManagementInsight(
        severity=_severity(result, policy.thresholds["minimum_confidence"]),
        executive_summary=summary,
        key_drivers=drivers,
        management_attention=attention,
        recommended_next_step=next_step,
        data_limitations=limitations,
    )
