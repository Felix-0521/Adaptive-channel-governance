"""Application service composing validation and domain engines."""

from __future__ import annotations

import pandas as pd

from .governance import classify_tier, detect_risks, evaluate_gates, governance_status, recommend
from .models import EvaluationResult, PartnerRecord
from .policy import PolicyRepository
from .scoring import score_partner
from .validation import require_valid_dataframe


def evaluate_partner(partner: PartnerRecord, policies: PolicyRepository) -> EvaluationResult:
    policy = policies.resolve(partner)
    score, confidence, pillar_scores, metric_scores = score_partner(partner, policy)
    risks = detect_risks(partner, policy)
    gates = evaluate_gates(partner)
    tier = classify_tier(score)
    status = governance_status(confidence, risks, gates, policy.thresholds["minimum_confidence"])
    return EvaluationResult(
        partner_id=partner.partner_id,
        policy_id=policy.policy_id,
        score=score,
        confidence=confidence,
        pillar_scores=pillar_scores,
        metric_scores=metric_scores,
        tier=tier,
        risks=risks,
        gate_codes=gates,
        governance_status=status,
        recommendations=recommend(partner, tier, risks, status),
    )


def evaluate_portfolio(frame: pd.DataFrame, policies: PolicyRepository) -> pd.DataFrame:
    severity_rank = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}
    rows = []
    for partner in require_valid_dataframe(frame):
        result = evaluate_partner(partner, policies)
        rows.append({
            "partner_id": partner.partner_id,
            "partner_name": partner.partner_name,
            "business_line": partner.business_line,
            "country_code": partner.country_code,
            "lifecycle_stage": partner.lifecycle_stage.value,
            "policy_id": result.policy_id,
            "score": result.score,
            "confidence": result.confidence,
            "tier": result.tier,
            "risk_level": max(
                (r.severity.value for r in result.risks),
                key=severity_rank.__getitem__,
                default="LOW",
            ),
            "governance_status": result.governance_status.value,
            "risk_codes": ", ".join(r.code for r in result.risks),
            "recommendation": " ".join(result.recommendations),
        })
    return pd.DataFrame(rows)
