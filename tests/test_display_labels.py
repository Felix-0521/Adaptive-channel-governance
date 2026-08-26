from channel_governance.display_labels import (
    action_label,
    action_reason,
    governance_label,
    lifecycle_label,
    localize_text,
    metric_label,
    risk_label,
    target_assessment_label,
    tier_label,
)


def test_core_status_labels_are_chinese_first() -> None:
    assert tier_label("STRATEGIC") == "战略级 · Strategic"
    assert risk_label("CRITICAL") == "严重风险 · Critical"
    assert governance_label("HOLD") == "暂停推进 · Hold"
    assert lifecycle_label("MATURE") == "成熟期 · Mature"


def test_business_labels_preserve_english_reference() -> None:
    assert metric_label("inventory_days") == "库存天数 · Inventory Days"
    assert "库存优化" in action_label("INVENTORY_OPTIMIZATION")
    assert target_assessment_label("REVIEW_REQUIRED") == "需要管理层复核 · Review Required"


def test_deterministic_summary_is_localized_without_changing_values() -> None:
    source = (
        "Partner Atlas is classified as STRATEGIC with a score of 94.8. "
        "Governance status is ACTIVE under Country Override: PL."
    )
    localized = localize_text(source)
    assert "Partner Atlas" in localized
    assert "94.8" in localized
    assert "战略级" in localized
    assert "正常推进" in localized
    assert "Country Override: PL" in localized


def test_action_reason_is_natural_chinese() -> None:
    localized = action_reason(
        "Inventory exceeds the configured optimal band and requires a sell-out-led plan."
    )
    assert "库存" in localized
    assert "Sell-out" in localized
    assert "优化" in localized


def test_unknown_display_value_falls_back_safely() -> None:
    assert tier_label("CUSTOM_STATE") == "Custom State"
    assert localize_text("Unmapped explanatory text") == "Unmapped explanatory text"
