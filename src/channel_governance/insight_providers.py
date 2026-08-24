"""Optional explanation providers with deterministic failure containment."""

from __future__ import annotations

import json
import os
from importlib.util import find_spec
from typing import Protocol

from .insight import generate_deterministic_insight
from .models import (
    DriverDirection,
    EvaluationResult,
    ManagementInsight,
    PartnerRecord,
    Policy,
    RiskSeverity,
    StructuredManagementContext,
)


class InsightProvider(Protocol):
    @property
    def available(self) -> bool: ...

    def generate(self, context: StructuredManagementContext) -> ManagementInsight: ...


def build_management_context(
    partner: PartnerRecord,
    result: EvaluationResult,
    deterministic: ManagementInsight,
) -> StructuredManagementContext:
    severity_rank = {RiskSeverity.LOW: 0, RiskSeverity.MEDIUM: 1, RiskSeverity.HIGH: 2, RiskSeverity.CRITICAL: 3}
    risk_level = max(
        (risk.severity for risk in result.risks),
        key=severity_rank.__getitem__,
        default=RiskSeverity.LOW,
    )
    negatives = tuple(
        driver.model_dump(mode="json")
        for driver in deterministic.key_drivers
        if driver.direction == DriverDirection.NEGATIVE
    )
    positives = tuple(
        driver.model_dump(mode="json")
        for driver in deterministic.key_drivers
        if driver.direction == DriverDirection.POSITIVE
    )
    return StructuredManagementContext(
        partner_name=partner.partner_name,
        business_line=partner.business_line,
        lifecycle_stage=partner.lifecycle_stage.value,
        score=result.score,
        confidence=result.confidence,
        tier=result.tier,
        risk_level=risk_level.value,
        governance_status=result.governance_status.value,
        policy_source=result.policy_source,
        gate_codes=tuple(result.gate_codes),
        key_negative_drivers=negatives,
        key_positive_drivers=positives,
        recommended_actions=tuple(
            action.model_dump(mode="json") for action in result.recommended_actions
        ),
        deterministic_insight=deterministic.model_dump(mode="json"),
    )


def generate_management_insight(
    partner: PartnerRecord,
    result: EvaluationResult,
    policy: Policy,
    provider: InsightProvider | None = None,
) -> ManagementInsight:
    """Return AI wording only when valid; every failure preserves the rule-based result."""
    fallback = generate_deterministic_insight(partner, result, policy)
    if provider is None or not provider.available:
        return fallback
    try:
        enhanced = provider.generate(build_management_context(partner, result, fallback))
        return enhanced.model_copy(update={"source": "AI_ENHANCED"})
    except Exception:
        return fallback


class OpenAIInsightProvider:
    """Lazy optional adapter for the OpenAI Responses API."""

    def __init__(self, api_key: str | None = None, model: str | None = None, client=None):
        self._api_key = api_key or os.getenv("OPENAI_API_KEY")
        self._model = model or os.getenv("OPENAI_MODEL", "gpt-5-mini")
        self._client = client

    @property
    def available(self) -> bool:
        return bool(self._api_key and (self._client is not None or find_spec("openai") is not None))

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI

            self._client = OpenAI(api_key=self._api_key, timeout=10.0, max_retries=0)
        return self._client

    def generate(self, context: StructuredManagementContext) -> ManagementInsight:
        if not self.available:
            raise RuntimeError("OpenAI insight provider is not configured")
        response = self._get_client().responses.create(
            model=self._model,
            store=False,
            instructions=(
                "Use only supplied facts. Explain, summarize, compare, highlight, or rephrase. "
                "Do not change scores, risks, tiers, gates, actions, or policy; do not invent causes, "
                "legal conclusions, or company policy. State uncertainty explicitly. Return only JSON "
                "matching the schema."
            ),
            input=context.model_dump_json(),
            text={
                "format": {
                    "type": "json_schema",
                    "name": "management_insight",
                    "strict": True,
                    "schema": ManagementInsight.model_json_schema(),
                }
            },
        )
        payload = json.loads(response.output_text)
        return ManagementInsight.model_validate(payload)
