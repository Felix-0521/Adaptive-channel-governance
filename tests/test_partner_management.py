import pandas as pd

from channel_governance.evaluation import evaluate_partner
from channel_governance.models import LifecycleStage, MarketTier, PartnerType
from channel_governance.partner_management import (
    analyze_partner_import,
    create_partner,
    import_partners,
)
from channel_governance.storage import SQLitePartnerStore


def import_frame(**changes) -> pd.DataFrame:
    row = {
        "partner_name": "Synthetic Managed Partner",
        "country_code": "PL",
        "region": "Central Europe",
        "business_line": "AGRICULTURE",
        "partner_type": "DISTRIBUTOR",
        "lifecycle_stage": "GROWTH",
        "market_tier": "GROWTH_VALUE",
    }
    row.update(changes)
    return pd.DataFrame([row])


def test_create_partner_is_persisted_and_enters_existing_engine(tmp_path, policies) -> None:
    store = SQLitePartnerStore(tmp_path / "app.db")
    partner = create_partner(
        store,
        partner_name="Synthetic New Partner",
        country_code="de",
        region="DACH",
        business_line="SURVEYING",
        partner_type=PartnerType.DEALER,
        lifecycle_stage=LifecycleStage.ENTRY,
        market_tier=MarketTier.DEVELOPING,
    )
    reloaded = SQLitePartnerStore(tmp_path / "app.db").list_partners()[0]
    result = evaluate_partner(reloaded, policies)
    assert reloaded.partner_id.startswith("P-")
    assert reloaded.country_code == "DE"
    assert result.score is None
    assert result.confidence == 0
    assert result.tier == "UNRATED"


def test_csv_analysis_reports_missing_management_fields() -> None:
    analysis = analyze_partner_import(pd.DataFrame({"partner_name": ["Incomplete"]}), [])
    assert not analysis.can_import
    assert any(issue.field == "country_code" for issue in analysis.issues)


def test_create_partner_requires_region(tmp_path) -> None:
    store = SQLitePartnerStore(tmp_path / "app.db")
    try:
        create_partner(
            store,
            partner_name="No Region",
            country_code="PL",
            region=" ",
            business_line="AGRICULTURE",
            partner_type=PartnerType.DISTRIBUTOR,
            lifecycle_stage=LifecycleStage.GROWTH,
            market_tier=MarketTier.GROWTH_VALUE,
        )
    except ValueError as error:
        assert "Region" in str(error)
    else:
        raise AssertionError("blank Region was accepted")


def test_csv_analysis_reports_invalid_values() -> None:
    analysis = analyze_partner_import(import_frame(market_tier="NOT_A_TIER"), [])
    assert not analysis.can_import
    assert any(issue.field == "market_tier" for issue in analysis.issues)


def test_csv_analysis_reports_existing_duplicate(tmp_path) -> None:
    store = SQLitePartnerStore(tmp_path / "app.db")
    existing_analysis = analyze_partner_import(import_frame(), [])
    import_partners(store, existing_analysis)
    duplicate = analyze_partner_import(import_frame(), store.list_partners())
    assert not duplicate.can_import
    assert any("duplicate" in issue.message.lower() for issue in duplicate.issues)


def test_confirmed_csv_import_persists_and_reports_data_quality(tmp_path) -> None:
    store = SQLitePartnerStore(tmp_path / "app.db")
    analysis = analyze_partner_import(import_frame(), [])
    imported = import_partners(store, analysis)
    assert imported == 1
    assert len(store.list_partners()) == 1
    assert analysis.warnings
