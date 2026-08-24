"""Read-only scenario comparison across partner, market, and portfolio scopes."""

from __future__ import annotations

from collections import Counter

import pandas as pd

from .evaluation import evaluate_partner
from .models import (
    RiskSeverity,
    ScenarioComparison,
    ScenarioReport,
    ScenarioScope,
    ScenarioSummary,
)
from .policy import PolicyLifecycleManager
from .validation import require_valid_dataframe


TIER_RANK = {"UNRATED": 0, "WATCHLIST": 1, "DEVELOPMENT": 2, "CORE": 3, "STRATEGIC": 4}
SEVERITY_RANK = {
    RiskSeverity.LOW: 0,
    RiskSeverity.MEDIUM: 1,
    RiskSeverity.HIGH: 2,
    RiskSeverity.CRITICAL: 3,
}
DISPLAY_TIERS = ("STRATEGIC", "CORE", "DEVELOPMENT", "WATCHLIST", "UNRATED")


def _risk_level(risks) -> str:
    return max((risk.severity for risk in risks), key=SEVERITY_RANK.__getitem__, default=RiskSeverity.LOW).value


class ScenarioService:
    @staticmethod
    def run(
        frame: pd.DataFrame,
        manager: PolicyLifecycleManager,
        *,
        draft_policy_id: str,
        draft_version: int,
        scope: ScenarioScope,
        partner_id: str | None = None,
        filters: dict[str, str] | None = None,
    ) -> ScenarioReport:
        records = require_valid_dataframe(frame)
        if scope == ScenarioScope.SINGLE_PARTNER:
            if not partner_id:
                raise ValueError("partner_id is required for SINGLE_PARTNER scope")
            records = [record for record in records if record.partner_id == partner_id]
        elif scope == ScenarioScope.SELECTED_MARKET:
            filters = filters or {}
            allowed = {"country_code", "business_line", "market_tier", "lifecycle_stage"}
            unknown = set(filters) - allowed
            if unknown:
                raise ValueError(f"unsupported market filters: {sorted(unknown)}")
            records = [
                record
                for record in records
                if all(str(record.model_dump(mode="json").get(key)) == str(value) for key, value in filters.items())
            ]
        elif scope != ScenarioScope.FULL_PORTFOLIO:
            raise ValueError(f"unsupported scenario scope: {scope}")
        if not records:
            raise ValueError("scenario scope selected no partners")

        baseline_repository = manager.active_repository()
        scenario_repository = manager.scenario_repository(draft_policy_id, draft_version)
        comparisons: list[ScenarioComparison] = []
        for partner in records:
            baseline = evaluate_partner(partner, baseline_repository)
            scenario = evaluate_partner(partner, scenario_repository)
            change = (
                round(scenario.score - baseline.score, 2)
                if scenario.score is not None and baseline.score is not None
                else None
            )
            comparisons.append(
                ScenarioComparison(
                    partner_id=partner.partner_id,
                    partner_name=partner.partner_name,
                    baseline_score=baseline.score,
                    scenario_score=scenario.score,
                    score_change=change,
                    baseline_tier=baseline.tier,
                    scenario_tier=scenario.tier,
                    baseline_risk=_risk_level(baseline.risks),
                    scenario_risk=_risk_level(scenario.risks),
                    baseline_governance_status=baseline.governance_status.value,
                    scenario_governance_status=scenario.governance_status.value,
                )
            )

        changes = [item for item in comparisons if item.score_change is not None]
        migrations = Counter(
            f"{item.baseline_tier} → {item.scenario_tier}"
            for item in comparisons
            if item.baseline_tier != item.scenario_tier
        )
        before = Counter(item.baseline_tier for item in comparisons)
        after = Counter(item.scenario_tier for item in comparisons)
        positive = max(changes, key=lambda item: item.score_change, default=None)
        negative = min(changes, key=lambda item: item.score_change, default=None)
        summary = ScenarioSummary(
            average_score_change=round(
                sum(item.score_change for item in changes) / len(changes), 2
            ) if changes else 0.0,
            partners_upgraded=sum(
                TIER_RANK[item.scenario_tier] > TIER_RANK[item.baseline_tier]
                for item in comparisons
            ),
            partners_downgraded=sum(
                TIER_RANK[item.scenario_tier] < TIER_RANK[item.baseline_tier]
                for item in comparisons
            ),
            tier_migration=dict(migrations),
            largest_positive_impact=(
                {"partner_id": positive.partner_id, "score_change": positive.score_change}
                if positive else None
            ),
            largest_negative_impact=(
                {"partner_id": negative.partner_id, "score_change": negative.score_change}
                if negative else None
            ),
            tier_counts_before={tier: before[tier] for tier in DISPLAY_TIERS},
            tier_counts_after={tier: after[tier] for tier in DISPLAY_TIERS},
        )
        return ScenarioReport(
            scope=scope,
            draft_policy_id=draft_policy_id,
            draft_version=draft_version,
            comparisons=comparisons,
            summary=summary,
        )

