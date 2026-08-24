"""Policy configuration, explicit inheritance, lifecycle, and audit services."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from .models import AuditRecord, MetricRule, PartnerRecord, Pillar, Policy, PolicyStatus


EXACT_CONTEXT = frozenset(
    {"business_line", "lifecycle_stage", "market_tier", "partner_type"}
)
COUNTRY_CONTEXT = EXACT_CONTEXT | {"country_code"}
BUSINESS_LIFECYCLE_CONTEXT = frozenset({"business_line", "lifecycle_stage"})
LIFECYCLE_CONTEXT = frozenset({"lifecycle_stage"})
ALLOWED_MATCH_SHAPES = {
    frozenset(),
    LIFECYCLE_CONTEXT,
    BUSINESS_LIFECYCLE_CONTEXT,
    EXACT_CONTEXT,
    COUNTRY_CONTEXT,
}


def validate_policy_configuration(policy: Policy) -> None:
    """Reject incomplete or mathematically invalid two-level configurations."""
    if set(policy.pillar_weights) != set(Pillar):
        raise ValueError(f"{policy.policy_id} must configure all six pillar weights")
    if abs(sum(policy.pillar_weights.values()) - 1.0) > 1e-9:
        raise ValueError(f"{policy.policy_id} pillar weights must sum to 1.0")

    metric_totals = {pillar: 0.0 for pillar in Pillar}
    for rule in policy.metrics.values():
        metric_totals[rule.pillar] += rule.weight
    for pillar, total in metric_totals.items():
        if abs(total - 1.0) > 1e-9:
            raise ValueError(
                f"{policy.policy_id} metric weights for {pillar.value} must sum to 1.0"
            )

    if set(policy.match) not in ALLOWED_MATCH_SHAPES:
        raise ValueError(
            f"{policy.policy_id} has unsupported match shape {sorted(policy.match)}; "
            "fallback must be explicit"
        )
    required_tiers = {"STRATEGIC", "CORE", "DEVELOPMENT"}
    if set(policy.tier_rules) != required_tiers:
        raise ValueError(f"{policy.policy_id} must configure all tier thresholds")
    if not (
        100 >= policy.tier_rules["STRATEGIC"]
        > policy.tier_rules["CORE"]
        > policy.tier_rules["DEVELOPMENT"]
        >= 0
    ):
        raise ValueError(f"{policy.policy_id} tier thresholds must be strictly descending")


class PolicyFile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: str
    policies: list[Policy] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_policy_set(self) -> "PolicyFile":
        active = [policy for policy in self.policies if policy.status == PolicyStatus.ACTIVE]
        defaults = [policy for policy in active if not policy.match]
        if len(defaults) != 1:
            raise ValueError("exactly one active global default policy is required")
        for policy in self.policies:
            validate_policy_configuration(policy)
        active_contexts: set[tuple[tuple[str, str], ...]] = set()
        for policy in active:
            context = tuple(sorted(policy.match.items()))
            if context in active_contexts:
                raise ValueError(f"multiple active policies exist for context {dict(context)}")
            active_contexts.add(context)
        return self


class PolicyRepository:
    """Read-only resolver containing active policies only."""

    def __init__(self, document: PolicyFile):
        self.document = document
        self._active = [
            policy.model_copy(deep=True)
            for policy in document.policies
            if policy.status == PolicyStatus.ACTIVE
        ]

    @classmethod
    def from_yaml(cls, path: str | Path) -> "PolicyRepository":
        with Path(path).open(encoding="utf-8") as handle:
            return cls(PolicyFile.model_validate(yaml.safe_load(handle)))

    @classmethod
    def from_policies(cls, policies: list[Policy], version: str = "runtime") -> "PolicyRepository":
        return cls(PolicyFile(version=version, policies=policies))

    def resolve(self, partner: PartnerRecord) -> Policy:
        return self.resolve_context(partner.model_dump(mode="json"))

    def resolve_context(self, context: Mapping[str, object]) -> Policy:
        candidates = [
            policy
            for policy in self._active
            if all(str(context.get(key)) == str(value) for key, value in policy.match.items())
        ]
        if not candidates:
            raise LookupError("no active policy matched and no global default is available")

        def rank(policy: Policy) -> tuple[int, int, int, str]:
            keys = frozenset(policy.match)
            level = {
                COUNTRY_CONTEXT: 5,
                EXACT_CONTEXT: 4,
                BUSINESS_LIFECYCLE_CONTEXT: 3,
                LIFECYCLE_CONTEXT: 2,
                frozenset(): 1,
            }[keys]
            return level, policy.priority, policy.version, policy.policy_id

        selected = max(candidates, key=rank).model_copy(deep=True)
        keys = frozenset(selected.match)
        if keys == COUNTRY_CONTEXT:
            selected.selection_level = "COUNTRY_OVERRIDE"
            selected.source_label = f"Country Override: {selected.match['country_code']}"
        elif keys == EXACT_CONTEXT:
            selected.selection_level = "EXACT_CONTEXT"
            selected.source_label = "Exact Context Policy"
        elif keys == BUSINESS_LIFECYCLE_CONTEXT:
            selected.selection_level = "BUSINESS_LIFECYCLE"
            selected.source_label = "Inherited from Business + Lifecycle Policy"
        elif keys == LIFECYCLE_CONTEXT:
            selected.selection_level = "LIFECYCLE"
            selected.source_label = "Inherited from Lifecycle Policy"
        else:
            selected.selection_level = "GLOBAL_DEFAULT"
            selected.source_label = "Inherited from Global Default Policy"
        return selected


class PolicyLifecycleManager:
    """Mutable policy lifecycle isolated from dashboard resolution."""

    def __init__(self, document: PolicyFile):
        self.document_version = document.version
        self.policies = [policy.model_copy(deep=True) for policy in document.policies]
        self.audit_records: list[AuditRecord] = []

    @classmethod
    def from_yaml(cls, path: str | Path) -> "PolicyLifecycleManager":
        with Path(path).open(encoding="utf-8") as handle:
            return cls(PolicyFile.model_validate(yaml.safe_load(handle)))

    def active_repository(self) -> PolicyRepository:
        active = [policy.model_copy(deep=True) for policy in self.policies if policy.status == PolicyStatus.ACTIVE]
        return PolicyRepository.from_policies(active, self.document_version)

    def drafts(self) -> list[Policy]:
        return [
            policy.model_copy(deep=True)
            for policy in self.policies
            if policy.status == PolicyStatus.DRAFT
        ]

    def get(self, policy_id: str, version: int) -> Policy:
        for policy in self.policies:
            if policy.policy_id == policy_id and policy.version == version:
                return policy.model_copy(deep=True)
        raise LookupError(f"policy {policy_id} v{version} does not exist")

    def save_draft(
        self,
        base_policy: Policy,
        *,
        pillar_weights: dict[Pillar, float],
        metrics: dict[str, MetricRule],
        actor: str,
        change_reason: str,
        match: dict[str, str] | None = None,
        policy_id: str | None = None,
        thresholds: dict[str, float] | None = None,
        tier_rules: dict[str, float] | None = None,
    ) -> Policy:
        target_id = policy_id or base_policy.policy_id
        versions = [policy.version for policy in self.policies if policy.policy_id == target_id]
        draft = base_policy.model_copy(
            deep=True,
            update={
                "policy_id": target_id,
                "version": max(versions, default=base_policy.version) + 1,
                "status": PolicyStatus.DRAFT,
                "scenario_tested": False,
                "base_version": base_policy.version,
                "match": deepcopy(match if match is not None else base_policy.match),
                "pillar_weights": deepcopy(pillar_weights),
                "metrics": deepcopy(metrics),
                "thresholds": deepcopy(thresholds if thresholds is not None else base_policy.thresholds),
                "tier_rules": deepcopy(tier_rules if tier_rules is not None else base_policy.tier_rules),
                "source_label": "Draft — not active",
                "selection_level": "DRAFT",
            },
        )
        validate_policy_configuration(draft)
        if not actor.strip() or not change_reason.strip():
            raise ValueError("actor and change_reason are required to save a draft")
        self.policies.append(draft)
        return draft.model_copy(deep=True)

    def mark_scenario_tested(self, policy_id: str, version: int) -> Policy:
        for index, policy in enumerate(self.policies):
            if policy.policy_id == policy_id and policy.version == version:
                if policy.status != PolicyStatus.DRAFT:
                    raise ValueError("only a draft can be scenario tested")
                tested = policy.model_copy(update={"scenario_tested": True})
                self.policies[index] = tested
                return tested.model_copy(deep=True)
        raise LookupError(f"draft {policy_id} v{version} does not exist")

    def scenario_repository(self, policy_id: str, version: int) -> PolicyRepository:
        draft = self.get(policy_id, version)
        if draft.status != PolicyStatus.DRAFT:
            raise ValueError("scenario policy must be a draft")
        active = [
            policy.model_copy(deep=True)
            for policy in self.policies
            if policy.status == PolicyStatus.ACTIVE and policy.match != draft.match
        ]
        active.append(draft.model_copy(update={"status": PolicyStatus.ACTIVE}))
        return PolicyRepository.from_policies(active, f"scenario-{policy_id}-v{version}")

    def activate(
        self,
        policy_id: str,
        version: int,
        *,
        actor: str,
        change_reason: str,
    ) -> AuditRecord:
        if not actor.strip() or not change_reason.strip():
            raise ValueError("actor and change_reason are required for activation")
        target_index = next(
            (
                index
                for index, policy in enumerate(self.policies)
                if policy.policy_id == policy_id and policy.version == version
            ),
            None,
        )
        if target_index is None:
            raise LookupError(f"draft {policy_id} v{version} does not exist")
        target = self.policies[target_index]
        if target.status != PolicyStatus.DRAFT or not target.scenario_tested:
            raise ValueError("draft must be scenario tested before activation")

        old_version: int | None = target.base_version
        for index, policy in enumerate(self.policies):
            if policy.status == PolicyStatus.ACTIVE and policy.match == target.match:
                old_version = policy.version
                self.policies[index] = policy.model_copy(update={"status": PolicyStatus.ARCHIVED})
        self.policies[target_index] = target.model_copy(
            update={"status": PolicyStatus.ACTIVE, "source_label": "", "selection_level": ""}
        )
        audit = AuditRecord(
            timestamp=datetime.now(timezone.utc).isoformat(),
            policy_id=policy_id,
            old_version=old_version,
            new_version=version,
            actor=actor.strip(),
            change_reason=change_reason.strip(),
        )
        self.audit_records.append(audit)
        return audit

