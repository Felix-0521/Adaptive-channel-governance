"""Independent risk, gate, tier, status, and Recommended Action rules."""

from __future__ import annotations

from .models import (
    ActionPriority,
    GovernanceStatus,
    PartnerRecord,
    Policy,
    RecommendedAction,
    RecommendedActionType,
    RiskFlag,
    RiskSeverity,
)


def detect_risks(partner: PartnerRecord, policy: Policy) -> list[RiskFlag]:
    t = policy.thresholds
    risks: list[RiskFlag] = []
    if partner.inventory_days is not None and partner.inventory_days > t["inventory_days_high"]:
        risks.append(RiskFlag(code="EXCESS_INVENTORY", severity=RiskSeverity.HIGH,
                              message="Inventory is above the policy optimal band.",
                              evidence={"inventory_days": partner.inventory_days}))
    if partner.inventory_days is not None and partner.inventory_days < t["inventory_days_low"]:
        risks.append(RiskFlag(code="SUPPLY_COVERAGE", severity=RiskSeverity.MEDIUM,
                              message="Inventory is below the policy optimal band.",
                              evidence={"inventory_days": partner.inventory_days}))
    if partner.ar_overdue_90d_pct is not None and partner.ar_overdue_90d_pct >= t["ar_overdue_90d_high_pct"]:
        risks.append(RiskFlag(code="OVERDUE_AR", severity=RiskSeverity.HIGH,
                              message="Over-90-day receivables require finance review.",
                              evidence={"ar_overdue_90d_pct": partner.ar_overdue_90d_pct}))
    if partner.data_reporting_quality_pct is not None and partner.data_reporting_quality_pct < t["data_quality_low_pct"]:
        risks.append(RiskFlag(code="LOW_DATA_QUALITY", severity=RiskSeverity.MEDIUM,
                              message="Reported data quality is below the policy threshold.",
                              evidence={"data_reporting_quality_pct": partner.data_reporting_quality_pct}))
    if partner.pricing_violations is not None and partner.pricing_violations > 0:
        risks.append(RiskFlag(code="PRICING_DISCIPLINE", severity=RiskSeverity.HIGH,
                              message="A pricing-discipline signal requires human investigation.",
                              evidence={"pricing_violations": partner.pricing_violations}))
    if partner.unauthorized_sales_incidents is not None and partner.unauthorized_sales_incidents > 0:
        risks.append(RiskFlag(code="UNAUTHORIZED_SALES", severity=RiskSeverity.CRITICAL,
                              message="An unauthorized-sales signal requires compliance review.",
                              evidence={"incidents": partner.unauthorized_sales_incidents}))
    if partner.sanctions_match is True:
        risks.append(RiskFlag(code="SANCTIONS_MATCH", severity=RiskSeverity.CRITICAL,
                              message="A synthetic sanctions-match signal requires immediate review."))
    if partner.material_contract_breach is True:
        risks.append(RiskFlag(code="MATERIAL_CONTRACT_BREACH", severity=RiskSeverity.CRITICAL,
                              message="A material contract-breach signal requires legal review."))
    return risks


def evaluate_gates(partner: PartnerRecord) -> list[str]:
    gates: list[str] = []
    if partner.sanctions_match is True:
        gates.append("GATE_SANCTIONS_REVIEW")
    if partner.material_contract_breach is True:
        gates.append("GATE_CONTRACT_REVIEW")
    if (partner.unauthorized_sales_incidents or 0) > 0:
        gates.append("GATE_UNAUTHORIZED_SALES_REVIEW")
    return gates


def classify_tier(score: float | None, policy: Policy) -> str:
    if score is None:
        return "UNRATED"
    if score >= policy.tier_rules["STRATEGIC"]:
        return "STRATEGIC"
    if score >= policy.tier_rules["CORE"]:
        return "CORE"
    if score >= policy.tier_rules["DEVELOPMENT"]:
        return "DEVELOPMENT"
    return "WATCHLIST"


def governance_status(
    confidence: float, risks: list[RiskFlag], gates: list[str], minimum_confidence: float
) -> GovernanceStatus:
    if gates:
        return GovernanceStatus.HOLD
    severities = {risk.severity for risk in risks}
    if confidence < minimum_confidence or RiskSeverity.HIGH in severities or RiskSeverity.CRITICAL in severities:
        return GovernanceStatus.REVIEW
    if RiskSeverity.MEDIUM in severities:
        return GovernanceStatus.MONITOR
    return GovernanceStatus.ACTIVE


def recommended_actions(
    partner: PartnerRecord,
    policy: Policy,
    pillar_scores: dict[str, float | None],
    metric_scores: dict[str, float | None],
    risks: list[RiskFlag],
    gates: list[str],
    status: GovernanceStatus,
    tier: str,
) -> list[RecommendedAction]:
    """Bridge evaluation to human action without mapping directly from total score."""
    actions: list[RecommendedAction] = []
    risk_codes = {risk.code for risk in risks}

    def add(action, priority, reason, evidence=None):
        actions.append(
            RecommendedAction(
                action=action,
                priority=priority,
                reason=reason,
                evidence=evidence or {},
                human_review_required=True,
            )
        )

    if gates:
        add(
            RecommendedActionType.COMPLIANCE_REVIEW,
            ActionPriority.HIGH,
            "A critical gate requires specialist review before any growth action.",
            {"gate_codes": gates},
        )
        add(
            RecommendedActionType.NO_ADDITIONAL_SUPPORT,
            ActionPriority.HIGH,
            "Discretionary support should pause until the gate is reviewed by a human.",
            {"governance_status": status.value},
        )
        return actions

    if "OVERDUE_AR" in risk_codes:
        add(
            RecommendedActionType.CREDIT_REVIEW,
            ActionPriority.HIGH,
            "Material overdue receivables take priority over growth support.",
            {
                "ar_overdue_90d_pct": partner.ar_overdue_90d_pct,
                "policy_threshold_pct": policy.thresholds["ar_overdue_90d_high_pct"],
            },
        )
    if "EXCESS_INVENTORY" in risk_codes:
        add(
            RecommendedActionType.INVENTORY_OPTIMIZATION,
            ActionPriority.HIGH,
            "Inventory exceeds the configured optimal band and requires a sell-out-led plan.",
            {
                "inventory_days": partner.inventory_days,
                "policy_high_days": policy.thresholds["inventory_days_high"],
            },
        )
    if "PRICING_DISCIPLINE" in risk_codes:
        add(
            RecommendedActionType.COMPLIANCE_REVIEW,
            ActionPriority.HIGH,
            "The pricing-discipline signal requires investigation without presuming a legal finding.",
            {"pricing_violations": partner.pricing_violations},
        )
    if any(action.priority == ActionPriority.HIGH for action in actions):
        return actions

    if "LOW_DATA_QUALITY" in risk_codes:
        add(
            RecommendedActionType.DATA_QUALITY_IMPROVEMENT,
            ActionPriority.MEDIUM,
            "Reporting quality is below the configured threshold.",
            {
                "data_reporting_quality_pct": partner.data_reporting_quality_pct,
                "policy_threshold_pct": policy.thresholds["data_quality_low_pct"],
            },
        )

    commercial = pillar_scores.get("COMMERCIAL_PERFORMANCE")
    market = pillar_scores.get("MARKET_CAPABILITY")
    operational = pillar_scores.get("OPERATIONAL_HEALTH")
    financial = pillar_scores.get("FINANCIAL_HEALTH")
    service = pillar_scores.get("SERVICE_TECH_CAPABILITY")

    if partner.lifecycle_stage.value in {"BUILD", "EMERGING"}:
        if market is not None and market < 60:
            add(
                RecommendedActionType.CHANNEL_EXPANSION,
                ActionPriority.HIGH,
                "Early-stage market coverage is below the capability benchmark.",
                {"market_capability_score": market, "benchmark": 60},
            )
        if partner.demo_capability is False:
            add(
                RecommendedActionType.DEMO_SUPPORT,
                ActionPriority.HIGH,
                "The partner lacks demo capability required for early market creation.",
                {"demo_capability": False},
            )
        if service is not None and service < 60:
            if (partner.certified_engineers or 0) < 2:
                add(
                    RecommendedActionType.ENGINEER_SUPPORT,
                    ActionPriority.HIGH,
                    "Technical staffing is insufficient for the current lifecycle stage.",
                    {"certified_engineers": partner.certified_engineers, "benchmark": 2},
                )
            if (partner.training_completion_pct or 0) < 70:
                add(
                    RecommendedActionType.TRAINING_CERTIFICATION,
                    ActionPriority.MEDIUM,
                    "Training completion is below the enablement benchmark.",
                    {"training_completion_pct": partner.training_completion_pct, "benchmark_pct": 70},
                )

    new_product = partner.new_product_contribution_pct
    new_product_benchmark = policy.thresholds["new_product_benchmark_pct"]
    mature_and_healthy = (
        partner.lifecycle_stage.value == "MATURE"
        and partner.business_line == "AGRICULTURE"
        and all(value is not None and value >= 70 for value in (commercial, operational, financial))
    )
    if mature_and_healthy and new_product is not None and new_product < new_product_benchmark:
        add(
            RecommendedActionType.NEW_PRODUCT_ENABLEMENT,
            ActionPriority.HIGH,
            "A healthy mature partner has new-product contribution below the policy benchmark.",
            {
                "new_product_contribution_pct": new_product,
                "policy_benchmark_pct": new_product_benchmark,
                "normalized_metric_score": metric_scores.get("new_product_contribution_pct"),
            },
        )
        add(
            RecommendedActionType.BRANDING_MDF,
            ActionPriority.MEDIUM,
            "Brand activation can support the reviewed new-product enablement plan.",
            {"commercial_performance_score": commercial},
        )

    if not actions and tier in {"STRATEGIC", "CORE"}:
        add(
            RecommendedActionType.JOINT_BUSINESS_PLANNING,
            ActionPriority.LOW,
            "No overriding risk or capability gap is present; maintain a reviewed joint plan.",
            {"tier": tier, "governance_status": status.value},
        )
    if not actions:
        add(
            RecommendedActionType.CORRECTIVE_ACTION_PLAN,
            ActionPriority.MEDIUM,
            "No targeted growth action is justified; define measurable improvement priorities.",
            {"tier": tier, "governance_status": status.value},
        )
    return actions
