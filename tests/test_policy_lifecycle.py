from channel_governance.models import Pillar, PolicyStatus


CONTEXT = {
    "business_line": "AGRICULTURE",
    "lifecycle_stage": "GROWTH",
    "market_tier": "HIGH_VALUE",
    "partner_type": "DISTRIBUTOR",
    "country_code": "PL",
}


def create_draft(policy_manager):
    active = policy_manager.active_repository().resolve_context(CONTEXT)
    weights = dict(active.pillar_weights)
    weights[Pillar.COMMERCIAL_PERFORMANCE] -= 0.05
    weights[Pillar.OPERATIONAL_HEALTH] += 0.05
    return policy_manager.save_draft(
        active,
        pillar_weights=weights,
        metrics=active.metrics,
        actor="Felix-0521",
        change_reason="Test a greater operational-health emphasis",
    )


def test_draft_does_not_affect_active_calculation(policy_manager) -> None:
    before = policy_manager.active_repository().resolve_context(CONTEXT)
    draft = create_draft(policy_manager)
    after = policy_manager.active_repository().resolve_context(CONTEXT)
    assert draft.status == PolicyStatus.DRAFT
    assert after.version == before.version == 1
    assert after.pillar_weights == before.pillar_weights


def test_scenario_repository_uses_draft_without_mutating_active(policy_manager) -> None:
    draft = create_draft(policy_manager)
    scenario = policy_manager.scenario_repository(draft.policy_id, draft.version)
    assert scenario.resolve_context(CONTEXT).version == draft.version
    assert policy_manager.active_repository().resolve_context(CONTEXT).version == 1


def test_activation_archives_previous_active_and_changes_resolution(policy_manager) -> None:
    draft = create_draft(policy_manager)
    policy_manager.mark_scenario_tested(draft.policy_id, draft.version)
    policy_manager.activate(
        draft.policy_id,
        draft.version,
        actor="Felix-0521",
        change_reason="Scenario reviewed",
    )
    resolved = policy_manager.active_repository().resolve_context(CONTEXT)
    old = policy_manager.get(draft.policy_id, 1)
    assert resolved.version == draft.version
    assert resolved.status == PolicyStatus.ACTIVE
    assert old.status == PolicyStatus.ARCHIVED


def test_activation_creates_required_audit_record(policy_manager) -> None:
    draft = create_draft(policy_manager)
    policy_manager.mark_scenario_tested(draft.policy_id, draft.version)
    audit = policy_manager.activate(
        draft.policy_id,
        draft.version,
        actor="Felix-0521",
        change_reason="Approved after scenario review",
    )
    assert audit.policy_id == draft.policy_id
    assert audit.old_version == 1
    assert audit.new_version == 2
    assert audit.actor == "Felix-0521"
    assert audit.change_reason == "Approved after scenario review"
    assert audit.timestamp


def test_unscenarioed_draft_cannot_activate(policy_manager) -> None:
    draft = create_draft(policy_manager)
    try:
        policy_manager.activate(
            draft.policy_id,
            draft.version,
            actor="Felix-0521",
            change_reason="Should fail",
        )
    except ValueError as error:
        assert "scenario tested" in str(error)
    else:
        raise AssertionError("activation unexpectedly accepted an untested draft")

