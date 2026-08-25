from channel_governance.models import PartnerRecord


def partner(**changes):
    base = dict(
        partner_id="P-1", partner_name="Synthetic", business_line="AGRICULTURE",
        country_code="PL", lifecycle_stage="GROWTH", market_tier="HIGH_VALUE",
        partner_type="DISTRIBUTOR",
    )
    return PartnerRecord(**(base | changes))


def test_most_specific_policy_wins(policies) -> None:
    resolved = policies.resolve(partner())
    assert resolved.policy_id == "POL-AGR-GROWTH-HV-DIST-PL"
    assert resolved.source_label == "Country Override: PL"


def test_lifecycle_policy_inherits_default_metrics(policies) -> None:
    resolved = policies.resolve(partner(country_code="DE", lifecycle_stage="EMERGING"))
    assert resolved.policy_id == "POL-LIFECYCLE-EMERGING"
    assert "inventory_days" in resolved.metrics
    assert sum(resolved.pillar_weights.values()) == 1.0


def test_default_policy_is_fallback(policies) -> None:
    resolved = policies.resolve(partner(country_code="US", lifecycle_stage="MAINTENANCE"))
    assert resolved.policy_id == "POL-DEFAULT"


def test_exact_context_is_inherited_when_country_override_missing(policies) -> None:
    resolved = policies.resolve(partner(country_code="DE"))
    assert resolved.policy_id == "POL-AGR-GROWTH-HV-DIST"
    assert resolved.selection_level == "EXACT_CONTEXT"
    assert resolved.source_label == "Exact Context Policy"


def test_fallback_source_is_never_silent(policies) -> None:
    resolved = policies.resolve(
        partner(business_line="GEOSPATIAL", country_code="BE", lifecycle_stage="MATURE")
    )
    assert resolved.selection_level == "LIFECYCLE"
    assert resolved.source_label == "Inherited from Lifecycle Policy"
