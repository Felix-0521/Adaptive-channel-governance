from channel_governance.models import PartnerRecord


def partner(**changes):
    base = dict(
        partner_id="P-1", partner_name="Synthetic", business_line="AGRICULTURE",
        country_code="PL", lifecycle_stage="GROWTH", market_tier="HIGH_VALUE",
        partner_type="DISTRIBUTOR",
    )
    return PartnerRecord(**(base | changes))


def test_most_specific_policy_wins(policies) -> None:
    assert policies.resolve(partner()).policy_id == "POL-AGR-PL-GROWTH-001"


def test_lifecycle_policy_inherits_default_metrics(policies) -> None:
    resolved = policies.resolve(partner(country_code="DE", lifecycle_stage="EMERGING"))
    assert resolved.policy_id == "POL-EMERGING-001"
    assert "inventory_days" in resolved.metrics
    assert sum(resolved.pillar_weights.values()) == 1.0


def test_default_policy_is_fallback(policies) -> None:
    resolved = policies.resolve(partner(country_code="US", lifecycle_stage="MAINTENANCE"))
    assert resolved.policy_id == "POL-DEFAULT-001"
