"""Transparent normalization and weighted scoring."""

from __future__ import annotations

from collections import defaultdict

from .models import MetricRule, PartnerRecord, Pillar, Policy


def _clamp(value: float) -> float:
    return max(0.0, min(100.0, value))


def normalize(value: float | bool, rule: MetricRule) -> float:
    if rule.method == "boolean":
        return 100.0 if bool(value) else 0.0
    if rule.method == "linear":
        assert rule.bad is not None and rule.good is not None and rule.good != rule.bad
        return _clamp((float(value) - rule.bad) / (rule.good - rule.bad) * 100)
    if rule.method == "inverse_linear":
        assert rule.bad is not None and rule.good is not None and rule.bad != rule.good
        return _clamp((rule.bad - float(value)) / (rule.bad - rule.good) * 100)
    if rule.method == "optimal_band":
        assert None not in (rule.low, rule.high, rule.hard_low, rule.hard_high)
        number = float(value)
        if rule.low <= number <= rule.high:
            return 100.0
        if number < rule.low:
            return _clamp((number - rule.hard_low) / (rule.low - rule.hard_low) * 100)
        return _clamp((rule.hard_high - number) / (rule.hard_high - rule.high) * 100)
    raise ValueError(f"unsupported normalization method: {rule.method}")


def score_partner(
    partner: PartnerRecord, policy: Policy
) -> tuple[float | None, float, dict[str, float | None], dict[str, float | None]]:
    metric_scores: dict[str, float | None] = {}
    pillar_values: dict[Pillar, list[tuple[float, float]]] = defaultdict(list)
    available_weight = 0.0
    total_weight = 0.0

    for metric, rule in policy.metrics.items():
        effective_weight = policy.pillar_weights[rule.pillar] * rule.weight
        total_weight += effective_weight
        value = getattr(partner, metric)
        if value is None:
            metric_scores[metric] = None
            continue
        metric_score = normalize(value, rule)
        metric_scores[metric] = round(metric_score, 2)
        pillar_values[rule.pillar].append((metric_score, rule.weight))
        available_weight += effective_weight

    pillar_scores: dict[str, float | None] = {}
    score_terms: list[tuple[float, float]] = []
    for pillar, pillar_weight in policy.pillar_weights.items():
        values = pillar_values.get(pillar, [])
        if not values:
            pillar_scores[pillar.value] = None
            continue
        pillar_score = sum(value * weight for value, weight in values) / sum(weight for _, weight in values)
        pillar_scores[pillar.value] = round(pillar_score, 2)
        score_terms.append((pillar_score, pillar_weight))

    score = (
        sum(value * weight for value, weight in score_terms) / sum(weight for _, weight in score_terms)
        if score_terms
        else None
    )
    confidence = available_weight / total_weight if total_weight else 0.0
    return None if score is None else round(score, 2), round(confidence, 3), pillar_scores, metric_scores
