"""Independent risk, gate, tier, status, and recommendation rules."""

from __future__ import annotations

from .models import GovernanceStatus, PartnerRecord, Policy, RiskFlag, RiskSeverity


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


def classify_tier(score: float | None) -> str:
    if score is None:
        return "UNRATED"
    if score >= 90:
        return "STRATEGIC"
    if score >= 75:
        return "CORE"
    if score >= 60:
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


def recommend(
    partner: PartnerRecord, tier: str, risks: list[RiskFlag], status: GovernanceStatus
) -> list[str]:
    if status == GovernanceStatus.HOLD:
        return ["Pause discretionary support and route the case to human compliance/legal review."]
    by_code = {risk.code for risk in risks}
    actions: list[str] = []
    if "EXCESS_INVENTORY" in by_code:
        actions.append("Review sell-in assumptions and agree a sell-out-led inventory recovery plan.")
    if "OVERDUE_AR" in by_code:
        actions.append("Run a joint Finance and Sales Operations receivables review.")
    if "LOW_DATA_QUALITY" in by_code:
        actions.append("Complete missing reporting controls before expanding discretionary support.")
    if "PRICING_DISCIPLINE" in by_code:
        actions.append("Investigate the pricing-discipline signal; do not infer a legal conclusion.")
    if partner.lifecycle_stage.value == "EMERGING" and (partner.certified_engineers or 0) < 2:
        actions.append("Prioritize technical certification and demo enablement.")
    if not actions and tier in {"STRATEGIC", "CORE"}:
        actions.append("Maintain support and review co-marketing or launch enablement through human approval.")
    if not actions:
        actions.append("Create a 90-day capability improvement plan and schedule a governance review.")
    return actions
