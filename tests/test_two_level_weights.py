from copy import deepcopy
from pathlib import Path

import pandas as pd
import pytest
from pydantic import ValidationError

from channel_governance.models import Pillar
from channel_governance.policy import PolicyFile
from channel_governance.scoring import score_partner
from channel_governance.validation import require_valid_dataframe


ROOT = Path(__file__).parents[1]


def sample_partner(partner_id: str = "P-002"):
    records = require_valid_dataframe(pd.read_csv(ROOT / "data" / "sample_partners.csv"))
    return next(record for record in records if record.partner_id == partner_id)


def test_every_policy_has_six_pillars_totalling_one(policies) -> None:
    for policy in policies.document.policies:
        assert set(policy.pillar_weights) == set(Pillar)
        assert sum(policy.pillar_weights.values()) == pytest.approx(1.0)


def test_metric_weights_total_one_inside_each_pillar(policies) -> None:
    for policy in policies.document.policies:
        for pillar in Pillar:
            total = sum(rule.weight for rule in policy.metrics.values() if rule.pillar == pillar)
            assert total == pytest.approx(1.0)


def test_invalid_pillar_total_is_rejected(policies) -> None:
    document = deepcopy(policies.document.model_dump(mode="json"))
    document["policies"][0]["pillar_weights"]["COMMERCIAL_PERFORMANCE"] = 0.30
    with pytest.raises(ValidationError, match="pillar weights must sum to 1.0"):
        PolicyFile.model_validate(document)


def test_invalid_metric_total_is_rejected(policies) -> None:
    document = deepcopy(policies.document.model_dump(mode="json"))
    document["policies"][0]["metrics"]["inventory_days"]["weight"] = 0.30
    with pytest.raises(ValidationError, match="metric weights for OPERATIONAL_HEALTH"):
        PolicyFile.model_validate(document)


def test_metric_weight_change_affects_pillar_score(policies) -> None:
    partner = sample_partner()
    policy = policies.resolve(partner)
    changed = policy.model_copy(deep=True)
    changed.metrics["inventory_days"] = changed.metrics["inventory_days"].model_copy(update={"weight": 0.10})
    changed.metrics["sell_out_performance_pct"] = changed.metrics[
        "sell_out_performance_pct"
    ].model_copy(update={"weight": 0.65})

    _, _, baseline_pillars, _ = score_partner(partner, policy)
    _, _, changed_pillars, _ = score_partner(partner, changed)
    assert changed_pillars["OPERATIONAL_HEALTH"] != baseline_pillars["OPERATIONAL_HEALTH"]


def test_pillar_weight_change_affects_only_overall_weighting(policies) -> None:
    partner = sample_partner()
    policy = policies.resolve(partner)
    changed = policy.model_copy(deep=True)
    changed.pillar_weights[Pillar.COMMERCIAL_PERFORMANCE] -= 0.10
    changed.pillar_weights[Pillar.MARKET_CAPABILITY] += 0.10

    baseline_score, _, baseline_pillars, _ = score_partner(partner, policy)
    changed_score, _, changed_pillars, _ = score_partner(partner, changed)
    assert changed_pillars == baseline_pillars
    assert changed_score != baseline_score
