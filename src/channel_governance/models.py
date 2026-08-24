"""Canonical input and output contracts."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class LifecycleStage(StrEnum):
    BUILD = "BUILD"
    EMERGING = "EMERGING"
    GROWTH = "GROWTH"
    MATURE = "MATURE"
    MAINTENANCE = "MAINTENANCE"


class PartnerType(StrEnum):
    DISTRIBUTOR = "DISTRIBUTOR"
    DEALER = "DEALER"


class MarketTier(StrEnum):
    HIGH_VALUE = "HIGH_VALUE"
    GROWTH_VALUE = "GROWTH_VALUE"
    DEVELOPING = "DEVELOPING"


class Pillar(StrEnum):
    COMMERCIAL_PERFORMANCE = "COMMERCIAL_PERFORMANCE"
    MARKET_CAPABILITY = "MARKET_CAPABILITY"
    OPERATIONAL_HEALTH = "OPERATIONAL_HEALTH"
    FINANCIAL_HEALTH = "FINANCIAL_HEALTH"
    SERVICE_TECH_CAPABILITY = "SERVICE_TECH_CAPABILITY"
    COMPLIANCE_GOVERNANCE = "COMPLIANCE_GOVERNANCE"


class RiskSeverity(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class GovernanceStatus(StrEnum):
    ACTIVE = "ACTIVE"
    MONITOR = "MONITOR"
    REVIEW = "REVIEW"
    HOLD = "HOLD"


class PolicyStatus(StrEnum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class PartnerRecord(BaseModel):
    """Synthetic partner observation. Optional metrics preserve missingness."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    partner_id: str = Field(min_length=1)
    partner_name: str = Field(min_length=1)
    business_line: str = Field(min_length=1)
    country_code: str = Field(min_length=2, max_length=2)
    lifecycle_stage: LifecycleStage
    market_tier: MarketTier
    partner_type: PartnerType
    annual_revenue: float | None = Field(default=None, ge=0)
    target_achievement_pct: float | None = Field(default=None, ge=0, le=300)
    yoy_growth_pct: float | None = Field(default=None, ge=-100, le=500)
    new_product_contribution_pct: float | None = Field(default=None, ge=0, le=100)
    active_dealers: int | None = Field(default=None, ge=0)
    geographic_coverage_pct: float | None = Field(default=None, ge=0, le=100)
    inventory_days: float | None = Field(default=None, ge=0, le=730)
    sell_out_performance_pct: float | None = Field(default=None, ge=0, le=200)
    forecast_accuracy_pct: float | None = Field(default=None, ge=0, le=100)
    payment_on_time_pct: float | None = Field(default=None, ge=0, le=100)
    ar_overdue_90d_pct: float | None = Field(default=None, ge=0, le=100)
    certified_engineers: int | None = Field(default=None, ge=0)
    training_completion_pct: float | None = Field(default=None, ge=0, le=100)
    demo_capability: bool | None = None
    data_reporting_quality_pct: float | None = Field(default=None, ge=0, le=100)
    pricing_violations: int | None = Field(default=None, ge=0)
    unauthorized_sales_incidents: int | None = Field(default=None, ge=0)
    sanctions_match: bool | None = None
    material_contract_breach: bool | None = None

    @field_validator("country_code")
    @classmethod
    def uppercase_country(cls, value: str) -> str:
        return value.upper()


class MetricRule(BaseModel):
    pillar: Pillar
    method: str
    weight: float = Field(gt=0, le=1)
    good: float | None = None
    bad: float | None = None
    low: float | None = None
    high: float | None = None
    hard_low: float | None = None
    hard_high: float | None = None


class Policy(BaseModel):
    policy_id: str
    version: int = Field(default=1, ge=1)
    status: PolicyStatus = PolicyStatus.ACTIVE
    scenario_tested: bool = False
    base_version: int | None = None
    priority: int = 0
    match: dict[str, str] = Field(default_factory=dict)
    pillar_weights: dict[Pillar, float] = Field(default_factory=dict)
    metrics: dict[str, MetricRule] = Field(default_factory=dict)
    thresholds: dict[str, float] = Field(default_factory=dict)
    tier_rules: dict[str, float] = Field(
        default_factory=lambda: {"STRATEGIC": 90, "CORE": 75, "DEVELOPMENT": 60}
    )
    source_label: str = ""
    selection_level: str = ""


class AuditRecord(BaseModel):
    timestamp: str
    policy_id: str
    old_version: int | None
    new_version: int
    actor: str
    change_reason: str


class RiskFlag(BaseModel):
    code: str
    severity: RiskSeverity
    message: str
    evidence: dict[str, Any] = Field(default_factory=dict)


class EvaluationResult(BaseModel):
    partner_id: str
    policy_id: str
    policy_version: int
    policy_source: str
    score: float | None
    confidence: float
    pillar_scores: dict[str, float | None]
    metric_scores: dict[str, float | None]
    tier: str
    risks: list[RiskFlag]
    gate_codes: list[str]
    governance_status: GovernanceStatus
    recommendations: list[str]
