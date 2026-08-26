"""Tests for the synthetic 50-partner portfolio (PART B)."""
from __future__ import annotations

import pytest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent.parent
SYNTHETIC_DIR = ROOT / "data" / "synthetic"


class TestSyntheticPortfolioStructure:
    """PART B: Verify the 50-partner portfolio structure."""

    def test_all_7_templates_exist(self):
        expected = [
            "01_Partner_Master.xlsx",
            "02_Commercial_Performance.xlsx",
            "03_Operational_Health.xlsx",
            "04_Financial_Health.xlsx",
            "05_Service_Capability.xlsx",
            "06_Compliance_Governance.xlsx",
            "07_Target_Rationale.xlsx",
        ]
        for fname in expected:
            path = SYNTHETIC_DIR / fname
            assert path.exists(), f"Missing template: {fname}"

    def test_exactly_50_partners(self):
        df = pd.read_excel(SYNTHETIC_DIR / "01_Partner_Master.xlsx",
                           sheet_name="Template", header=0)
        assert len(df) == 50, f"Expected 50 partners, got {len(df)}"

    def test_partner_ids_unique(self):
        df = pd.read_excel(SYNTHETIC_DIR / "01_Partner_Master.xlsx",
                           sheet_name="Template", header=0)
        assert df["Partner_ID"].nunique() == 50, "Duplicate Partner_ID found"

    def test_all_templates_have_same_partner_ids(self):
        master_ids = set(pd.read_excel(
            SYNTHETIC_DIR / "01_Partner_Master.xlsx",
            sheet_name="Template", header=0)["Partner_ID"])
        for fname in [
            "02_Commercial_Performance.xlsx",
            "03_Operational_Health.xlsx",
            "04_Financial_Health.xlsx",
            "05_Service_Capability.xlsx",
            "06_Compliance_Governance.xlsx",
            "07_Target_Rationale.xlsx",
        ]:
            ids = set(pd.read_excel(
                SYNTHETIC_DIR / fname,
                sheet_name="Template", header=0)["Partner_ID"])
            assert ids == master_ids, f"{fname} has mismatched Partner_IDs"

    def test_countries_coverage(self):
        df = pd.read_excel(SYNTHETIC_DIR / "01_Partner_Master.xlsx",
                           sheet_name="Template", header=0)
        countries = set(df["Country"].unique())
        required = {"Poland", "Germany", "France", "Spain", "Sweden",
                    "Netherlands", "Italy"}
        assert required <= countries, \
            f"Missing countries: {required - countries}"

    def test_business_lines_coverage(self):
        df = pd.read_excel(SYNTHETIC_DIR / "01_Partner_Master.xlsx",
                           sheet_name="Template", header=0)
        bls = set(df["Business_Line"].unique())
        required = {"AGRICULTURE", "GEOSPATIAL_SURVEYING", "LANDSCAPING",
                    "FACILITY_SERVICES", "CONSTRUCTION"}
        assert required <= bls, f"Missing business lines: {required - bls}"

    def test_lifecycle_coverage(self):
        df = pd.read_excel(SYNTHETIC_DIR / "01_Partner_Master.xlsx",
                           sheet_name="Template", header=0)
        lcs = set(df["Lifecycle_Stage"].unique())
        required = {"ENTRY", "BUILD", "GROWTH", "MATURE", "DECLINE"}
        assert required <= lcs, f"Missing lifecycle stages: {required - lcs}"

    def test_market_tiers_coverage(self):
        df = pd.read_excel(SYNTHETIC_DIR / "01_Partner_Master.xlsx",
                           sheet_name="Template", header=0)
        tiers = set(df["Market_Tier"].unique())
        required = {"HIGH_VALUE", "GROWTH_VALUE", "DEVELOPING", "MID_VALUE"}
        assert required <= tiers, f"Missing market tiers: {required - tiers}"

    def test_percentages_are_strings(self):
        df = pd.read_excel(SYNTHETIC_DIR / "02_Commercial_Performance.xlsx",
                           sheet_name="Template", header=0)
        for col in ["YoY_Growth_Percent", "Gross_Margin_Percent",
                    "New_Product_Revenue_Percent"]:
            non_null = df[col].dropna()
            for val in non_null:
                assert isinstance(val, str) and "%" in str(val), \
                    f"{col}={val!r} is not a percentage string"


class TestBusinessCases:
    """Verify the 5 designed business cases exist."""

    def test_healthy_strategic_partner(self):
        df = pd.read_excel(SYNTHETIC_DIR / "01_Partner_Master.xlsx",
                           sheet_name="Template", header=0)
        t02 = pd.read_excel(SYNTHETIC_DIR / "02_Commercial_Performance.xlsx",
                            sheet_name="Template", header=0)
        t04 = pd.read_excel(SYNTHETIC_DIR / "04_Financial_Health.xlsx",
                            sheet_name="Template", header=0)
        # PT00001: Poland, AGRICULTURE, GROWTH, HIGH_VALUE
        row = df[df["Partner_ID"] == "PT00001"].iloc[0]
        assert row["Country"] == "Poland"
        assert row["Lifecycle_Stage"] == "GROWTH"
        assert row["Market_Tier"] == "HIGH_VALUE"
        comm = t02[t02["Partner_ID"] == "PT00001"].iloc[0]
        assert comm["Annual_Revenue_USD"] > 3_000_000  # High revenue
        fin = t04[t04["Partner_ID"] == "PT00001"].iloc[0]
        assert fin["Payment_On_Time_Percent"] == "96%"

    def test_inventory_risk_partner(self):
        t03 = pd.read_excel(SYNTHETIC_DIR / "03_Operational_Health.xlsx",
                            sheet_name="Template", header=0)
        # PT00006: inventory_days = 165 (> 90 high threshold)
        row = t03[t03["Partner_ID"] == "PT00006"].iloc[0]
        assert row["Inventory_Days"] == 165

    def test_growth_partner_low_revenue(self):
        t02 = pd.read_excel(SYNTHETIC_DIR / "02_Commercial_Performance.xlsx",
                            sheet_name="Template", header=0)
        # PT00011: entry partner, revenue < 500K
        row = t02[t02["Partner_ID"] == "PT00011"].iloc[0]
        assert row["Annual_Revenue_USD"] < 500_000
        assert row["YoY_Growth_Percent"] == "60%"

    def test_financial_risk_partner(self):
        t04 = pd.read_excel(SYNTHETIC_DIR / "04_Financial_Health.xlsx",
                            sheet_name="Template", header=0)
        # PT00016: payment 62% (low), overdue high
        row = t04[t04["Partner_ID"] == "PT00016"].iloc[0]
        assert row["Payment_On_Time_Percent"] == "62%"
        assert row["Overdue_AR_USD"] > 100_000

    def test_low_data_quality_partners_missing_commercial_data(self):
        t02 = pd.read_excel(SYNTHETIC_DIR / "02_Commercial_Performance.xlsx",
                            sheet_name="Template", header=0)
        for pid in ["PT00021", "PT00022", "PT00023", "PT00024", "PT00025"]:
            row = t02[t02["Partner_ID"] == pid].iloc[0]
            assert pd.isna(row["Annual_Revenue_USD"]), \
                f"{pid} should have null revenue"

    def test_mid_value_tier_exists(self):
        df = pd.read_excel(SYNTHETIC_DIR / "01_Partner_Master.xlsx",
                           sheet_name="Template", header=0)
        mid_val = df[df["Market_Tier"] == "MID_VALUE"]
        assert len(mid_val) >= 1, "At least one MID_VALUE partner expected"


class TestMultiTemplateJoin:
    """PART B: Multi-template join on Partner_ID."""

    def test_all_7_templates_join_on_partner_id(self):
        parts = {}
        templates = [
            "01_Partner_Master.xlsx",
            "02_Commercial_Performance.xlsx",
            "03_Operational_Health.xlsx",
            "04_Financial_Health.xlsx",
            "05_Service_Capability.xlsx",
            "06_Compliance_Governance.xlsx",
            "07_Target_Rationale.xlsx",
        ]
        for fname in templates:
            df = pd.read_excel(SYNTHETIC_DIR / fname,
                               sheet_name="Template", header=0)
            parts[fname] = set(df["Partner_ID"])

        master_ids = parts["01_Partner_Master.xlsx"]
        for fname, ids in parts.items():
            assert ids == master_ids, \
                f"{fname} Partner_ID set does not match master"

    def test_null_handling_in_case5_partners(self):
        t02 = pd.read_excel(SYNTHETIC_DIR / "02_Commercial_Performance.xlsx",
                            sheet_name="Template", header=0)
        t03 = pd.read_excel(SYNTHETIC_DIR / "03_Operational_Health.xlsx",
                            sheet_name="Template", header=0)
        t04 = pd.read_excel(SYNTHETIC_DIR / "04_Financial_Health.xlsx",
                            sheet_name="Template", header=0)
        for pid in ["PT00021", "PT00022", "PT00023", "PT00024", "PT00025"]:
            row2 = t02[t02["Partner_ID"] == pid].iloc[0]
            row3 = t03[t03["Partner_ID"] == pid].iloc[0]
            row4 = t04[t04["Partner_ID"] == pid].iloc[0]
            # Commercial and Financial data should be null
            assert pd.isna(row2["Annual_Revenue_USD"])
            assert pd.isna(row4["Outstanding_AR_USD"])
            # Partner master context should still be present
            master = pd.read_excel(SYNTHETIC_DIR / "01_Partner_Master.xlsx",
                                   sheet_name="Template", header=0)
            mrow = master[master["Partner_ID"] == pid].iloc[0]
            assert mrow["Partner_Name"] is not None
