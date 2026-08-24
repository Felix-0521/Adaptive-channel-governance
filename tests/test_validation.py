import pandas as pd

from channel_governance.validation import validate_dataframe


def test_missing_column_is_reported() -> None:
    records, issues = validate_dataframe(pd.DataFrame({"partner_id": ["P-1"]}))
    assert records == []
    assert any(issue.field == "partner_name" for issue in issues)


def test_null_metric_stays_none() -> None:
    row = {name: None for name in __import__("channel_governance.models", fromlist=["PartnerRecord"]).PartnerRecord.model_fields}
    row.update({
        "partner_id": "P-1", "partner_name": "Synthetic", "business_line": "AGRICULTURE",
        "country_code": "pl", "lifecycle_stage": "GROWTH", "market_tier": "HIGH_VALUE",
        "partner_type": "DISTRIBUTOR",
    })
    records, issues = validate_dataframe(pd.DataFrame([row]))
    assert not issues
    assert records[0].inventory_days is None
    assert records[0].country_code == "PL"


def test_out_of_range_value_is_rejected() -> None:
    row = {name: None for name in __import__("channel_governance.models", fromlist=["PartnerRecord"]).PartnerRecord.model_fields}
    row.update({
        "partner_id": "P-1", "partner_name": "Synthetic", "business_line": "AGRICULTURE",
        "country_code": "PL", "lifecycle_stage": "GROWTH", "market_tier": "HIGH_VALUE",
        "partner_type": "DISTRIBUTOR",
        "payment_on_time_pct": 120,
    })
    _, issues = validate_dataframe(pd.DataFrame([row]))
    assert any(issue.field == "payment_on_time_pct" for issue in issues)


def test_unknown_column_is_rejected() -> None:
    row = {name: None for name in __import__("channel_governance.models", fromlist=["PartnerRecord"]).PartnerRecord.model_fields}
    row.update({
        "partner_id": "P-1", "partner_name": "Synthetic", "business_line": "AGRICULTURE",
        "country_code": "PL", "lifecycle_stage": "GROWTH", "market_tier": "HIGH_VALUE",
        "partner_type": "DISTRIBUTOR",
        "secret_margin": 25,
    })
    _, issues = validate_dataframe(pd.DataFrame([row]))
    assert any(issue.field == "secret_margin" for issue in issues)


def test_duplicate_partner_id_is_rejected() -> None:
    row = {name: None for name in __import__("channel_governance.models", fromlist=["PartnerRecord"]).PartnerRecord.model_fields}
    row.update({
        "partner_id": "P-1", "partner_name": "Synthetic", "business_line": "AGRICULTURE",
        "country_code": "PL", "lifecycle_stage": "GROWTH", "market_tier": "HIGH_VALUE",
        "partner_type": "DISTRIBUTOR",
    })
    _, issues = validate_dataframe(pd.DataFrame([row, row]))
    assert any("duplicate" in issue.message for issue in issues)
