"""Tests for the business data normalization pipeline."""

from __future__ import annotations

import math

import pandas as pd
import pytest

from channel_governance import mappings as m
from channel_governance.data_normalizer import (
    NormalizationResult,
    NormalizerIssue,
    normalize_excel_templates,
)
from channel_governance.template_schema import TemplateId


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _excel_df(headers: list[str], data_rows: list[list]) -> pd.DataFrame:
    """Build a DataFrame mimicking openpyxl output.

    openpyxl reads a sheet as:
      row 0 = title string (padded to column count with empty cells)
      row 1 = column headers  (becomes df.columns after _strip_sheet skips row 0)
      row 2+ = data rows

    This helper pads every row (title + data) to match the header column count
    so pandas does NOT auto-generate integer column names.
    """
    n_cols = len(headers)
    title_row = ["Sheet Title"] + [""] * (n_cols - 1)
    all_rows = [[title_row], [headers], data_rows]
    flat = [title_row, headers] + data_rows
    # Pad every row to n_cols so pandas uses the exact header count
    padded = [r + [""] * (n_cols - len(r)) if len(r) < n_cols else r for r in flat]
    df = pd.DataFrame(padded)
    # Set column names so _strip_sheet finds the correct join key
    df.columns = headers
    return df


# ══════════════════════════════════════════════════════════════════════════════
# TEST 1 — Country mapping
# ══════════════════════════════════════════════════════════════════════════════

class TestCountryMapping:
    def test_english_name_to_code(self):
        assert m.normalize_country("Poland") == "PL"
        assert m.normalize_country("Germany") == "DE"
        assert m.normalize_country("France") == "FR"
        assert m.normalize_country("Spain") == "ES"
        assert m.normalize_country("Sweden") == "SE"

    def test_iso_code_uppercase(self):
        assert m.normalize_country("PL") == "PL"
        assert m.normalize_country("DE") == "DE"

    def test_case_insensitive(self):
        assert m.normalize_country("POLAND") == "PL"
        assert m.normalize_country("poland") == "PL"
        assert m.normalize_country("Poland") == "PL"

    def test_none_returns_none(self):
        assert m.normalize_country(None) is None
        assert m.normalize_country("") is None

    def test_unknown_raises(self):
        with pytest.raises(ValueError, match="Unrecognized country"):
            m.normalize_country("Neverland")


# ══════════════════════════════════════════════════════════════════════════════
# TEST 2 — Enum mapping
# ══════════════════════════════════════════════════════════════════════════════

class TestEnumMapping:
    @pytest.mark.parametrize("raw,expected", [
        ("ENTRY", "ENTRY"), ("BUILD", "BUILD"), ("GROWTH", "GROWTH"),
        ("MATURE", "MATURE"), ("DECLINE", "DECLINE"),
        ("entry", "ENTRY"), ("mature", "MATURE"), ("Entry", "ENTRY"),
    ])
    def test_lifecycle_stage(self, raw, expected):
        assert m.normalize_lifecycle_stage(raw) == expected

    def test_lifecycle_unknown_raises(self):
        with pytest.raises(ValueError, match="lifecycle stage"):
            m.normalize_lifecycle_stage("RETIRED")

    def test_lifecycle_none(self):
        assert m.normalize_lifecycle_stage(None) is None

    @pytest.mark.parametrize("raw,expected", [
        ("HIGH_VALUE", "HIGH_VALUE"), ("GROWTH_VALUE", "GROWTH_VALUE"),
        ("DEVELOPING", "DEVELOPING"), ("MID_VALUE", "MID_VALUE"),
        ("mid_value", "MID_VALUE"), ("high_value", "HIGH_VALUE"),
    ])
    def test_market_tier(self, raw, expected):
        assert m.normalize_market_tier(raw) == expected

    def test_market_tier_unknown_raises(self):
        with pytest.raises(ValueError, match="market tier"):
            m.normalize_market_tier("PREMIUM")

    @pytest.mark.parametrize("raw,expected", [
        ("DISTRIBUTOR", "DISTRIBUTOR"), ("DEALER", "DEALER"),
        ("distributor", "DISTRIBUTOR"), ("Dealer", "DEALER"),
    ])
    def test_partner_type(self, raw, expected):
        assert m.normalize_partner_type(raw) == expected


# ══════════════════════════════════════════════════════════════════════════════
# TEST 3 — Percentage conversion
# ══════════════════════════════════════════════════════════════════════════════

class TestPercentageParsing:
    @pytest.mark.parametrize("raw,expected", [
        ("85%", 85.0), ("10%", 10.0), ("0%", 0.0), ("100%", 100.0),
        ("26.5%", 26.5), (85.0, 85.0), (26.0, 26.0), (0, 0.0), (100, 100.0),
    ])
    def test_valid_percent(self, raw, expected):
        assert m.normalize_percent(raw) == expected

    def test_decimal_auto_scale(self):
        assert m.normalize_percent(0.85) == 85.0
        assert m.normalize_percent(0.265) == 26.5
        assert m.normalize_percent(0.0) == 0.0
        assert m.normalize_percent(1.0) == 100.0

    def test_none_returns_none(self):
        assert m.normalize_percent(None) is None
        assert m.normalize_percent("") is None

    def test_invalid_raises(self):
        with pytest.raises(ValueError, match="Unrecognised"):
            m.normalize_percent("not_a_number")

    def test_out_of_range_raises(self):
        with pytest.raises(ValueError, match="out of reasonable range"):
            m.normalize_percent(999.0)


# ══════════════════════════════════════════════════════════════════════════════
# TEST 4 — Invalid percentage
# ══════════════════════════════════════════════════════════════════════════════

class TestInvalidPercentage:
    def test_nonsense_string_raises(self):
        with pytest.raises(ValueError, match="Unrecognised"):
            m.normalize_percent("seventy-five percent")

    def test_negative_growth_valid(self):
        """Negative percentages (growth) must be accepted."""
        assert m.normalize_percent("-5%") == -5.0
        assert m.normalize_percent("-20%") == -20.0


# ══════════════════════════════════════════════════════════════════════════════
# TEST 5 — Missing Partner ID
# ══════════════════════════════════════════════════════════════════════════════

class TestMissingPartnerID:
    def test_missing_partner_id_in_template(self):
        headers = ["Partner_ID", "Partner_Name", "Country", "Region",
                   "Business_Line", "Partner_Type", "Lifecycle_Stage",
                   "Market_Tier", "Cooperation_Start_Date"]
        data = [
            ["", "Partner_X", "Poland", "CEE",
             "AGRICULTURE", "DISTRIBUTOR", "GROWTH", "HIGH_VALUE", "2021-01-01"],
        ]
        df = _excel_df(headers, data)

        result = normalize_excel_templates({TemplateId.PARTNER_MASTER: df})

        missing_issues = [i for i in result.warnings
                         if "Missing Partner_ID" in i.message or "empty Partner_ID" in i.message]
        assert len(missing_issues) >= 1


# ══════════════════════════════════════════════════════════════════════════════
# TEST 6 — Duplicate Partner
# ══════════════════════════════════════════════════════════════════════════════

class TestDuplicatePartner:
    def test_duplicate_partner_id(self):
        headers = ["Partner_ID", "Partner_Name", "Country", "Region",
                   "Business_Line", "Partner_Type", "Lifecycle_Stage",
                   "Market_Tier", "Cooperation_Start_Date"]
        data = [
            ["PT00001", "Partner_01", "Poland", "CEE",
             "AGRICULTURE", "DISTRIBUTOR", "GROWTH", "HIGH_VALUE", "2021-01-01"],
            ["PT00001", "Partner_01_copy", "Germany", "DACH",
             "AGRICULTURE", "DISTRIBUTOR", "GROWTH", "HIGH_VALUE", "2022-01-01"],
        ]
        df = _excel_df(headers, data)

        result = normalize_excel_templates({TemplateId.PARTNER_MASTER: df})

        dup_issues = [i for i in result.issues
                      if "Duplicate" in i.message and "PT00001" in i.message]
        assert len(dup_issues) >= 1


# ══════════════════════════════════════════════════════════════════════════════
# TEST 7 — Derived metric calculation
# ══════════════════════════════════════════════════════════════════════════════

class TestDerivedMetrics:
    def test_target_achievement_derived(self):
        t01 = _excel_df(
            ["Partner_ID", "Partner_Name", "Country", "Region",
             "Business_Line", "Partner_Type", "Lifecycle_Stage",
             "Market_Tier", "Cooperation_Start_Date"],
            [["PT00001", "Partner_01", "Poland", "CEE",
              "AGRICULTURE", "DISTRIBUTOR", "GROWTH", "HIGH_VALUE", "2021-01-01"]]
        )
        t02 = _excel_df(
            ["Partner_ID", "Evaluation_Period", "Annual_Revenue_USD",
             "Sales_Target_USD", "YoY_Growth_Percent", "New_Product_Revenue_Percent"],
            [["PT00001", "2026Q2", "1685615", "4780690", "10%", "29%"]]
        )

        result = normalize_excel_templates({
            TemplateId.PARTNER_MASTER: t01,
            TemplateId.COMMERCIAL_PERFORMANCE: t02,
        })

        assert result.success, f"Failed: {result.issues}"
        assert len(result.partner_records) == 1
        rec = result.partner_records[0]
        assert rec.target_achievement_pct is not None
        assert 35.0 <= rec.target_achievement_pct <= 36.0  # 1685615/4780690*100 ≈ 35.26

    def test_sell_out_performance_derived(self):
        t01 = _excel_df(
            ["Partner_ID", "Partner_Name", "Country", "Region",
             "Business_Line", "Partner_Type", "Lifecycle_Stage",
             "Market_Tier", "Cooperation_Start_Date"],
            [["PT00001", "Partner_01", "Poland", "CEE",
              "AGRICULTURE", "DISTRIBUTOR", "GROWTH", "HIGH_VALUE", "2021-01-01"]]
        )
        t02 = _excel_df(
            ["Partner_ID", "Evaluation_Period", "Sell_In_Units", "Sell_Out_Units"],
            [["PT00001", "2026Q2", "100", "80"]]
        )

        result = normalize_excel_templates({
            TemplateId.PARTNER_MASTER: t01,
            TemplateId.COMMERCIAL_PERFORMANCE: t02,
        })

        assert result.success
        rec = result.partner_records[0]
        assert rec.sell_out_performance_pct == 80.0

    def test_ar_overdue_ratio_derived(self):
        t01 = _excel_df(
            ["Partner_ID", "Partner_Name", "Country", "Region",
             "Business_Line", "Partner_Type", "Lifecycle_Stage",
             "Market_Tier", "Cooperation_Start_Date"],
            [["PT00001", "Partner_01", "Poland", "CEE",
              "AGRICULTURE", "DISTRIBUTOR", "GROWTH", "HIGH_VALUE", "2021-01-01"]]
        )
        t04 = _excel_df(
            ["Partner_ID", "Outstanding_AR_USD", "Overdue_AR_USD",
             "Payment_On_Time_Percent"],
            [["PT00001", "100000", "25000", "89%"]]
        )

        result = normalize_excel_templates({
            TemplateId.PARTNER_MASTER: t01,
            TemplateId.FINANCIAL_HEALTH: t04,
        })

        assert result.success
        rec = result.partner_records[0]
        assert rec.ar_overdue_90d_pct == 25.0

    def test_demo_capability_from_machine_count(self):
        t01 = _excel_df(
            ["Partner_ID", "Partner_Name", "Country", "Region",
             "Business_Line", "Partner_Type", "Lifecycle_Stage",
             "Market_Tier", "Cooperation_Start_Date"],
            [["PT00001", "Partner_01", "Poland", "CEE",
              "AGRICULTURE", "DISTRIBUTOR", "GROWTH", "HIGH_VALUE", "2021-01-01"]]
        )
        t05 = _excel_df(
            ["Partner_ID", "Certified_Engineer_Count", "Demo_Machine_Count"],
            [["PT00001", "5", "3"]]
        )

        result = normalize_excel_templates({
            TemplateId.PARTNER_MASTER: t01,
            TemplateId.SERVICE_CAPABILITY: t05,
        })

        assert result.success
        rec = result.partner_records[0]
        assert rec.demo_capability is True

    def test_demo_capability_zero_is_false(self):
        t01 = _excel_df(
            ["Partner_ID", "Partner_Name", "Country", "Region",
             "Business_Line", "Partner_Type", "Lifecycle_Stage",
             "Market_Tier", "Cooperation_Start_Date"],
            [["PT00001", "Partner_01", "Poland", "CEE",
              "AGRICULTURE", "DISTRIBUTOR", "GROWTH", "HIGH_VALUE", "2021-01-01"]]
        )
        t05 = _excel_df(
            ["Partner_ID", "Certified_Engineer_Count", "Demo_Machine_Count"],
            [["PT00001", "0", "0"]]
        )

        result = normalize_excel_templates({
            TemplateId.PARTNER_MASTER: t01,
            TemplateId.SERVICE_CAPABILITY: t05,
        })

        assert result.success
        rec = result.partner_records[0]
        assert rec.demo_capability is False


# ══════════════════════════════════════════════════════════════════════════════
# TEST 8 — Multi-template join
# ══════════════════════════════════════════════════════════════════════════════

class TestMultiTemplateJoin:
    def test_missing_template_creates_warning(self):
        t01 = _excel_df(
            ["Partner_ID", "Partner_Name", "Country", "Region",
             "Business_Line", "Partner_Type", "Lifecycle_Stage",
             "Market_Tier", "Cooperation_Start_Date"],
            [["PT00001", "Partner_01", "Poland", "CEE",
              "AGRICULTURE", "DISTRIBUTOR", "GROWTH", "HIGH_VALUE", "2021-01-01"]]
        )
        t03 = _excel_df(
            ["Partner_ID", "Evaluation_Period", "Inventory_Days"],
            [["PT00002", "2026Q2", "90"]]  # Different partner
        )

        result = normalize_excel_templates({
            TemplateId.PARTNER_MASTER: t01,
            TemplateId.OPERATIONAL_HEALTH: t03,
        })

        assert result.success
        cross_issues = [i for i in result.issues
                        if "missing from template" in i.message.lower()]
        assert len(cross_issues) >= 1

    def test_all_templates_joined(self):
        t01 = _excel_df(
            ["Partner_ID", "Partner_Name", "Country", "Region",
             "Business_Line", "Partner_Type", "Lifecycle_Stage",
             "Market_Tier", "Cooperation_Start_Date"],
            [["PT00001", "Partner_01", "Poland", "CEE",
              "AGRICULTURE", "DISTRIBUTOR", "GROWTH", "HIGH_VALUE", "2021-01-01"]]
        )
        t02 = _excel_df(
            ["Partner_ID", "Evaluation_Period", "Annual_Revenue_USD",
             "YoY_Growth_Percent", "New_Product_Revenue_Percent",
             "Sell_In_Units", "Sell_Out_Units", "Sales_Target_USD",
             "Gross_Margin_Percent", "Active_Customer_Count", "Pipeline_Value_USD"],
            [["PT00001", "2026Q2", "1000000", "15%", "25%", "100", "80", "1200000", "20%", "50", "200000"]]
        )
        t03 = _excel_df(
            ["Partner_ID", "Evaluation_Period", "Inventory_Days",
             "Forecast_Accuracy_Percent", "Reporting_Timeliness_Percent",
             "Sell_Out_Last_3M", "Inventory_Value_USD", "Inventory_Units",
             "Stock_Aging_90_Days_Percent", "Order_Fulfillment_Rate"],
            [["PT00001", "2026Q2", "68", "88%", "95%", "640", "100000", "50", "10%", "90%"]]
        )
        t04 = _excel_df(
            ["Partner_ID", "Payment_On_Time_Percent",
             "Outstanding_AR_USD", "Overdue_AR_USD",
             "Credit_Limit_USD", "Credit_Used_USD", "DSO_Days", "Credit_Rating"],
            [["PT00001", "89%", "100000", "5000", "500000", "200000", "25", "A"]]
        )
        t05 = _excel_df(
            ["Partner_ID", "Certified_Engineer_Count",
             "Training_Completion_Percent", "Demo_Machine_Count",
             "Service_Center_Count", "Spare_Part_Availability_Percent",
             "Average_Response_Time_Hours", "SLA_Compliance_Percent",
             "Demo_Conversion_Percent", "Reference_Project_Count"],
            [["PT00001", "5", "80%", "3", "2", "90%", "24", "95%", "30%", "5"]]
        )
        t06 = _excel_df(
            ["Partner_ID", "Confirmed_Compliance_Incident",
             "Unauthorized_Sales_Signal", "Data_Fraud_Flag",
             "Reporting_Compliance_Percent", "Contract_Status",
             "Contract_Expiration_Date", "Compliance_Training_Status",
             "Audit_Result"],
            [["PT00001", "0", "0", "FALSE", "95%", "Active", "2027-12-31", "Completed", "Passed"]]
        )
        t07 = _excel_df(
            ["Partner_ID", "Current_Revenue_USD", "Proposed_Target_USD",
             "Historical_Growth_Percent", "Resource_Commitment",
             "New_Product_Plan", "Pipeline_Value_USD",
             "New_Customer_Plan", "Coverage_Expansion_Plan"],
            [["PT00001", "1000000", "1200000", "15%",
              "Engineer Support", "High", "200000", "10", "5"]]
        )

        result = normalize_excel_templates({
            TemplateId.PARTNER_MASTER: t01,
            TemplateId.COMMERCIAL_PERFORMANCE: t02,
            TemplateId.OPERATIONAL_HEALTH: t03,
            TemplateId.FINANCIAL_HEALTH: t04,
            TemplateId.SERVICE_CAPABILITY: t05,
            TemplateId.COMPLIANCE_GOVERNANCE: t06,
            TemplateId.TARGET_RATIONALE: t07,
        })

        assert result.success, f"Issues: {result.issues}"
        assert len(result.partner_records) == 1
        rec = result.partner_records[0]
        assert rec.partner_id == "PT00001"
        assert rec.country_code == "PL"
        assert rec.lifecycle_stage.value == "GROWTH"
        assert rec.market_tier.value == "HIGH_VALUE"
        assert rec.yoy_growth_pct == 15.0
        assert rec.inventory_days == 68.0
        assert rec.demo_capability is True
        assert rec.training_completion_pct == 80.0


# ══════════════════════════════════════════════════════════════════════════════
# TEST 9 — Missing data reduces quality score
# ══════════════════════════════════════════════════════════════════════════════

class TestDataQualityScore:
    def test_full_data_higher_score_than_minimal(self):
        t01_full = _excel_df(
            ["Partner_ID", "Partner_Name", "Country", "Region",
             "Business_Line", "Partner_Type", "Lifecycle_Stage",
             "Market_Tier", "Cooperation_Start_Date"],
            [["PT00001", "Partner_01", "Poland", "CEE",
              "AGRICULTURE", "DISTRIBUTOR", "GROWTH", "HIGH_VALUE", "2021-01-01"]]
        )
        t02_full = _excel_df(
            ["Partner_ID", "Evaluation_Period", "Annual_Revenue_USD",
             "YoY_Growth_Percent", "New_Product_Revenue_Percent",
             "Sell_In_Units", "Sell_Out_Units", "Sales_Target_USD",
             "Gross_Margin_Percent", "Active_Customer_Count", "Pipeline_Value_USD"],
            [["PT00001", "2026Q2", "1000000", "15%", "25%", "100", "80", "1200000", "20%", "50", "200000"]]
        )
        t03_full = _excel_df(
            ["Partner_ID", "Evaluation_Period", "Inventory_Days",
             "Forecast_Accuracy_Percent", "Reporting_Timeliness_Percent",
             "Sell_Out_Last_3M", "Inventory_Value_USD", "Inventory_Units",
             "Stock_Aging_90_Days_Percent", "Order_Fulfillment_Rate"],
            [["PT00001", "2026Q2", "68", "88%", "95%", "640", "100000", "50", "10%", "90%"]]
        )
        t04_full = _excel_df(
            ["Partner_ID", "Payment_On_Time_Percent",
             "Outstanding_AR_USD", "Overdue_AR_USD",
             "Credit_Limit_USD", "Credit_Used_USD", "DSO_Days", "Credit_Rating"],
            [["PT00001", "89%", "100000", "5000", "500000", "200000", "25", "A"]]
        )
        t05_full = _excel_df(
            ["Partner_ID", "Certified_Engineer_Count",
             "Training_Completion_Percent", "Demo_Machine_Count",
             "Service_Center_Count", "Spare_Part_Availability_Percent",
             "Average_Response_Time_Hours", "SLA_Compliance_Percent",
             "Demo_Conversion_Percent", "Reference_Project_Count"],
            [["PT00001", "5", "80%", "3", "2", "90%", "24", "95%", "30%", "5"]]
        )
        t06_full = _excel_df(
            ["Partner_ID", "Confirmed_Compliance_Incident",
             "Unauthorized_Sales_Signal", "Data_Fraud_Flag",
             "Reporting_Compliance_Percent", "Contract_Status",
             "Contract_Expiration_Date", "Compliance_Training_Status",
             "Audit_Result"],
            [["PT00001", "0", "0", "FALSE", "95%", "Active", "2027-12-31", "Completed", "Passed"]]
        )

        result_full = normalize_excel_templates({
            TemplateId.PARTNER_MASTER: t01_full,
            TemplateId.COMMERCIAL_PERFORMANCE: t02_full,
            TemplateId.OPERATIONAL_HEALTH: t03_full,
            TemplateId.FINANCIAL_HEALTH: t04_full,
            TemplateId.SERVICE_CAPABILITY: t05_full,
            TemplateId.COMPLIANCE_GOVERNANCE: t06_full,
        })
        assert result_full.success
        assert result_full.data_quality_score > 0.0

        # Minimal: T01 only
        t01_min = _excel_df(
            ["Partner_ID", "Partner_Name", "Country", "Region",
             "Business_Line", "Partner_Type", "Lifecycle_Stage",
             "Market_Tier", "Cooperation_Start_Date"],
            [["PT00002", "Partner_02", "Poland", "CEE",
              "AGRICULTURE", "DISTRIBUTOR", "GROWTH", "HIGH_VALUE", "2021-01-01"]]
        )
        result_min = normalize_excel_templates({TemplateId.PARTNER_MASTER: t01_min})
        assert result_min.success
        assert result_min.data_quality_score < result_full.data_quality_score


# ══════════════════════════════════════════════════════════════════════════════
# TEST 10 — Normalized output compatible with evaluation engine
# ══════════════════════════════════════════════════════════════════════════════

class TestEvaluationEngineCompatibility:
    def test_partner_record_usable_by_evaluation(self):
        from channel_governance.models import PartnerRecord
        from channel_governance.policy import PolicyRepository
        from channel_governance import evaluation

        t01 = _excel_df(
            ["Partner_ID", "Partner_Name", "Country", "Region",
             "Business_Line", "Partner_Type", "Lifecycle_Stage",
             "Market_Tier", "Cooperation_Start_Date"],
            [["PT00001", "Partner_01", "Poland", "CEE",
              "AGRICULTURE", "DISTRIBUTOR", "GROWTH", "HIGH_VALUE", "2021-01-01"]]
        )
        t02 = _excel_df(
            ["Partner_ID", "Evaluation_Period", "Annual_Revenue_USD",
             "YoY_Growth_Percent", "New_Product_Revenue_Percent",
             "Sell_In_Units", "Sell_Out_Units", "Sales_Target_USD",
             "Gross_Margin_Percent", "Active_Customer_Count", "Pipeline_Value_USD"],
            [["PT00001", "2026Q2", "1000000", "15%", "25%", "100", "80", "1200000", "20%", "50", "200000"]]
        )
        t03 = _excel_df(
            ["Partner_ID", "Evaluation_Period", "Inventory_Days",
             "Forecast_Accuracy_Percent", "Reporting_Timeliness_Percent",
             "Sell_Out_Last_3M", "Inventory_Value_USD", "Inventory_Units",
             "Stock_Aging_90_Days_Percent", "Order_Fulfillment_Rate"],
            [["PT00001", "2026Q2", "68", "88%", "95%", "640", "100000", "50", "10%", "90%"]]
        )
        t04 = _excel_df(
            ["Partner_ID", "Payment_On_Time_Percent",
             "Outstanding_AR_USD", "Overdue_AR_USD",
             "Credit_Limit_USD", "Credit_Used_USD", "DSO_Days", "Credit_Rating"],
            [["PT00001", "89%", "100000", "5000", "500000", "200000", "25", "A"]]
        )
        t05 = _excel_df(
            ["Partner_ID", "Certified_Engineer_Count",
             "Training_Completion_Percent", "Demo_Machine_Count",
             "Service_Center_Count", "Spare_Part_Availability_Percent",
             "Average_Response_Time_Hours", "SLA_Compliance_Percent",
             "Demo_Conversion_Percent", "Reference_Project_Count"],
            [["PT00001", "5", "80%", "3", "2", "90%", "24", "95%", "30%", "5"]]
        )
        t06 = _excel_df(
            ["Partner_ID", "Confirmed_Compliance_Incident",
             "Unauthorized_Sales_Signal", "Data_Fraud_Flag",
             "Reporting_Compliance_Percent", "Contract_Status",
             "Contract_Expiration_Date", "Compliance_Training_Status",
             "Audit_Result"],
            [["PT00001", "0", "0", "FALSE", "95%", "Active", "2027-12-31", "Completed", "Passed"]]
        )

        result = normalize_excel_templates({
            TemplateId.PARTNER_MASTER: t01,
            TemplateId.COMMERCIAL_PERFORMANCE: t02,
            TemplateId.OPERATIONAL_HEALTH: t03,
            TemplateId.FINANCIAL_HEALTH: t04,
            TemplateId.SERVICE_CAPABILITY: t05,
            TemplateId.COMPLIANCE_GOVERNANCE: t06,
        })

        assert result.success, f"Issues: {result.issues}"
        rec = result.partner_records[0]
        assert isinstance(rec, PartnerRecord)
        assert rec.partner_id == "PT00001"
        assert rec.partner_name == "Partner_01"
        assert rec.country_code == "PL"

        repo = PolicyRepository.from_yaml("config/scoring_rules.yaml")
        eval_result = evaluation.evaluate_partner(rec, repo)

        assert eval_result.partner_id == "PT00001"
        assert eval_result.score is not None
        assert 0 <= eval_result.score <= 100
        assert 0.0 <= eval_result.confidence <= 1.0
        assert eval_result.governance_status.value in {"ACTIVE", "MONITOR", "REVIEW", "HOLD"}
