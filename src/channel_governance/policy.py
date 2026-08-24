"""Versioned policy loading, inheritance, and deterministic selection."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import yaml
from pydantic import BaseModel, Field, model_validator

from .models import PartnerRecord, Policy


class PolicyFile(BaseModel):
    version: str
    policies: list[Policy] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_policy_set(self) -> "PolicyFile":
        defaults = [policy for policy in self.policies if not policy.match]
        if len(defaults) != 1:
            raise ValueError("exactly one default policy is required")
        if abs(sum(defaults[0].pillar_weights.values()) - 1.0) > 1e-9:
            raise ValueError("default pillar weights must sum to 1.0")
        for policy in self.policies:
            if policy.pillar_weights and abs(sum(policy.pillar_weights.values()) - 1.0) > 1e-9:
                raise ValueError(f"{policy.policy_id} pillar weights must sum to 1.0")
        return self


class PolicyRepository:
    def __init__(self, document: PolicyFile):
        self.document = document
        self._default = next(policy for policy in document.policies if not policy.match)

    @classmethod
    def from_yaml(cls, path: str | Path) -> "PolicyRepository":
        with Path(path).open(encoding="utf-8") as handle:
            return cls(PolicyFile.model_validate(yaml.safe_load(handle)))

    def resolve(self, partner: PartnerRecord) -> Policy:
        context = partner.model_dump(mode="json")
        candidates = [
            policy
            for policy in self.document.policies
            if policy.match and all(str(context.get(key)) == str(value) for key, value in policy.match.items())
        ]
        if not candidates:
            return self._default.model_copy(deep=True)
        candidates.sort(key=lambda item: (item.priority, len(item.match), item.policy_id), reverse=True)
        selected = candidates[0]
        merged = deepcopy(self._default.model_dump())
        merged["policy_id"] = selected.policy_id
        merged["priority"] = selected.priority
        merged["match"] = selected.match
        for field in ("pillar_weights", "metrics", "thresholds"):
            merged[field].update(selected.model_dump()[field])
        return Policy.model_validate(merged)

