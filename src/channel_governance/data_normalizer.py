"""Business data normalization pipeline.

Transforms raw Excel template data into the canonical PartnerRecord format
consumed by the existing evaluation engine without touching scoring, policy,
or governance logic.

Pipeline
========
  Excel templates (7 files)
        ↓
  Template-level type normalization (% stripping, bool parsing, etc.)
        ↓
  Cross-template join on Partner_ID
        ↓
  Field mapping (Excel column → PartnerRecord field)
        ↓
  Enum normalization (Country, Lifecycle, MarketTier, PartnerType)
        ↓
  Derived metric computation
        ↓
  CanonicalPartnerRecord + NormalizationResult
        ↓
  PartnerRecord (validated by existing Pydantic contract)
        ↓
  evaluation.evaluate_partner()  ← unchanged
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

import pandas as pd
from pydantic import ValidationError

from .governance import detect_risks, evaluate_gates
from .mappings import (
    MAPPINGS,
    normalize_bool,
    normalize_country,
    normalize_lifecycle_stage,
    normalize_market_tier,
    normalize_new_product_plan,
    normalize_partner_type,
    normalize_percent,
    normalize_resource_commitment,
)
from .models import (
    LifecycleStage,
    MarketTier,
    PartnerRecord,
    PartnerType,
    RiskSeverity,
    TargetRationaleInput,
)
from .template_schema import TEMPLATES, TemplateId, TemplateSchema


# ──────────────────────────────────────────────────────────────────────────────
# Issue reporting
# ──────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class NormalizerIssue:
    """Row-level issue raised during normalization. Mirrors ValidationIssue."""

    row: int          # 1-indexed data row; -1 for file-level issues
    field: str        # logical field name (canonical)
    message: str      # human-readable description


@dataclass(frozen=True)
class DerivedMetric:
    """Record of a computed metric."""

    name: str
    value: Any
    source_fields: tuple[str, ...]
    formula: str
    is_none_because: str | None = None  # human-readable reason if value is None


@dataclass(frozen=True)
class NormalizationResult:
    """Outcome of normalizing a full set of templates.

    Attributes
    ----------
    success : bool
        True only when no errors were raised and at least one PartnerRecord
        was produced.
    partner_records : list[PartnerRecord]
        Validated canonical records ready for evaluation.
    target_inputs : list[TargetRationaleInput]
        Canonical target rationale inputs for each partner.
    issues : list[NormalizerIssue]
        All errors (blocking) and warnings (non-blocking).
    derived_metrics : dict[str, list[DerivedMetric]]
        Per-partner derived metric log.
    data_quality_score : float
        Fraction of expected fields that are non-null (0.0–1.0).
    """

    success: bool
    partner_records: list[PartnerRecord]
    target_inputs: list[TargetRationaleInput]
    issues: list[NormalizerIssue]
    derived_metrics: dict[str, list[DerivedMetric]] = field(default_factory=dict)
    data_quality_score: float = 0.0

    @property
    def errors(self) -> list[NormalizerIssue]:
        return [i for i in self.issues if i.row == -1 or "error" in i.message.lower()]

    @property
    def warnings(self) -> list[NormalizerIssue]:
        return [i for i in self.issues if i.row != -1 and "error" not in i.message.lower()]


# ──────────────────────────────────────────────────────────────────────────────
# Raw Excel → typed row dicts
# ──────────────────────────────────────────────────────────────────────────────

def _parse_bool_cell(raw: Any) -> bool | None:
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        return None
    return normalize_bool(raw)


def _parse_percent_cell(raw: Any) -> float | None:
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        return None
    try:
        return normalize_percent(raw)
    except ValueError:
        return None


def _parse_date_cell(raw: Any) -> str | None:
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        return None
    return str(raw).strip()


def _parse_float_cell(raw: Any) -> float | None:
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        return None
    try:
        return float(str(raw).strip())
    except (ValueError, TypeError):
        return None


def _parse_int_cell(raw: Any) -> int | None:
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        return None
    try:
        return int(float(str(raw).strip()))
    except (ValueError, TypeError):
        return None


def _strip_sheet(
    df: pd.DataFrame, schema: TemplateSchema
) -> tuple[pd.DataFrame, list[NormalizerIssue]]:
    """Drop title and header rows, trim to schema column count, clean empty cells.

    openpyxl with values_only=True reads a sheet as:
      row 0 = title (always skipped)
      row 1 = column headers  (skipped here; df.columns is already set by caller)
      row 2+ = actual data rows

    Returns the cleaned DataFrame and any non-blocking issues found during processing.
    """
    issues: list[NormalizerIssue] = []

    # Skip title row (index 0) and header row (index 1)
    # The DataFrame column names are already set by the caller (via _excel_df
    # or by openpyxl reading). We only need to keep the actual data rows.
    df = df.iloc[2:].copy().reset_index(drop=True)

    # The schema defines which columns matter; ignore any extra trailing cols
    schema_col_count = len(schema.fields)
    if len(df.columns) > schema_col_count:
        df = df.iloc[:, :schema_col_count]

    # If fewer columns than schema, pad with empty strings (will become NaN below)
    if len(df.columns) < schema_col_count:
        for _ in range(schema_col_count - len(df.columns)):
            df[len(df.columns)] = ""

    # Set column names from schema to guarantee alignment
    df.columns = list(df.columns)[:schema_col_count]

    join_key = schema.join_key
    if join_key not in df.columns:
        raise ValueError(
            f"Join key column '{join_key}' not found in template data. "
            f"Available columns: {list(df.columns)}."
        )

    # Detect empty-string Partner_ID values BEFORE replacing empty strings with NaN.
    # After replace('', nan), empty-string rows become NaN and are silently dropped,
    # which would suppress the Missing Partner_ID error. We report them first.
    for ridx, raw_val in enumerate(df[join_key], start=1):
        if str(raw_val).strip() == "":
            issues.append(NormalizerIssue(
                ridx, join_key,
                f"Missing or empty Partner_ID in template '{schema.template_id.value}'."
            ))

    # Replace empty strings with NaN so that pandas dropna works
    df = df.replace("", float("nan")).infer_objects(copy=False)

    # Drop rows with missing join key
    df = df.dropna(subset=[join_key])
    return df, issues


# ──────────────────────────────────────────────────────────────────────────────
# Template-level normalization
# ──────────────────────────────────────────────────────────────────────────────

def _normalize_template_raw(
    df: pd.DataFrame,
    schema: TemplateSchema,
) -> tuple[list[dict], list[NormalizerIssue]]:
    """Parse raw Excel data using the template schema.

    Returns a list of typed row dicts and a list of non-blocking issues.
    Raises ValueError on required-column absence.
    """
    df, strip_issues = _strip_sheet(df, schema)
    all_issues = strip_issues

    # Verify all required columns are present
    for f in schema.required_fields():
        if f.excel_name not in df.columns:
            raise ValueError(
                f"Required column '{f.excel_name}' is missing from template "
                f"'{schema.template_id.value}'."
            )

    rows: list[dict] = []
    row_issues: list[NormalizerIssue] = []

    for ridx, (_, raw_row) in enumerate(df.iterrows(), start=1):
        row_data: dict[str, Any] = {}
        for f in schema.fields:
            raw_val = raw_row.get(f.excel_name)
            try:
                if f.field_type.name == "PERCENT":
                    row_data[f.excel_name] = _parse_percent_cell(raw_val)
                elif f.field_type.name == "BOOL":
                    row_data[f.excel_name] = _parse_bool_cell(raw_val)
                elif f.field_type.name == "DATE":
                    row_data[f.excel_name] = _parse_date_cell(raw_val)
                elif f.field_type.name == "INT":
                    row_data[f.excel_name] = _parse_int_cell(raw_val)
                elif f.field_type.name == "FLOAT":
                    row_data[f.excel_name] = _parse_float_cell(raw_val)
                elif f.field_type.name == "ENUM":
                    val = str(raw_val).strip() if raw_val is not None else None
                    if val and f.enum_values and val not in f.enum_values:
                        row_issues.append(NormalizerIssue(
                            ridx, f.excel_name,
                            f"Unrecognised enum value '{val}'. "
                            f"Expected one of: {sorted(f.enum_values)}."
                        ))
                    row_data[f.excel_name] = val
                else:
                    row_data[f.excel_name] = (
                        str(raw_val).strip() if raw_val is not None else None
                    )
            except Exception as exc:
                row_issues.append(NormalizerIssue(
                    ridx, f.excel_name,
                    f"Failed to parse '{f.excel_name}' value '{raw_val}': {exc}"
                ))
                row_data[f.excel_name] = None

        rows.append(row_data)

    all_issues.extend(row_issues)
    return rows, all_issues


# ──────────────────────────────────────────────────────────────────────────────
# Canonical field mapping
# ──────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class _PartnerRow:
    """Intermediate canonical row after field mapping and enum normalization."""

    partner_id: str
    partner_name: str | None = None
    business_line: str | None = None
    country_code: str | None = None
    region: str | None = None
    lifecycle_stage: str | None = None
    market_tier: str | None = None
    partner_type: str | None = None
    annual_revenue: float | None = None
    target_achievement_pct: float | None = None
    yoy_growth_pct: float | None = None
    new_product_contribution_pct: float | None = None
    active_dealers: int | None = None
    geographic_coverage_pct: float | None = None
    inventory_days: float | None = None
    sell_out_performance_pct: float | None = None
    forecast_accuracy_pct: float | None = None
    data_reporting_quality_pct: float | None = None
    payment_on_time_pct: float | None = None
    ar_overdue_90d_pct: float | None = None
    certified_engineers: int | None = None
    training_completion_pct: float | None = None
    demo_capability: bool | None = None
    pricing_violations: int | None = None
    unauthorized_sales_incidents: int | None = None
    sanctions_match: bool | None = None
    material_contract_breach: bool | None = None

    # Target Rationale inputs
    tr_current_revenue: float | None = None
    tr_proposed_target: float | None = None
    tr_historical_growth_pct: float | None = None
    tr_current_sell_out_pct: float | None = None
    tr_market_capability_score: float | None = None
    tr_pipeline_value: float | None = None
    tr_new_customer_plan: int | None = None
    tr_coverage_pct: float | None = None
    tr_new_product_potential_pct: float | None = None
    tr_resource_commitment: bool | None = None
    tr_inventory_days: float | None = None
    tr_ar_overdue_90d_pct: float | None = None


def _map_row(
    rows_by_template: dict[TemplateId, list[dict]],
    issues: list[NormalizerIssue],
) -> dict[str, _PartnerRow]:
    """Merge all template rows by partner_id and apply field mapping."""

    # Collect all partner IDs
    all_partner_ids: set[str] = set()
    for tid, rows in rows_by_template.items():
        for row in rows:
            pid = str(row.get("Partner_ID") or "").strip()
            if pid:
                all_partner_ids.add(pid)

    canonical: dict[str, _PartnerRow] = {}

    for pid in all_partner_ids:
        # Gather raw values per template
        def get(template_id: TemplateId, field: str) -> Any:
            rows = rows_by_template.get(template_id, [])
            for r in rows:
                if str(r.get("Partner_ID") or "").strip() == pid:
                    return r.get(field)
            return None

        row_errors: list[NormalizerIssue] = []

        # ── Partner Master (T01) ──────────────────────────────────────────────
        lifecycle_raw = get(TemplateId.PARTNER_MASTER, "Lifecycle_Stage")
        market_tier_raw = get(TemplateId.PARTNER_MASTER, "Market_Tier")
        country_raw = get(TemplateId.PARTNER_MASTER, "Country")
        partner_type_raw = get(TemplateId.PARTNER_MASTER, "Partner_Type")

        # Normalize enums
        try:
            lifecycle_norm = normalize_lifecycle_stage(lifecycle_raw)
        except ValueError as exc:
            row_errors.append(NormalizerIssue(0, "lifecycle_stage", str(exc)))
            lifecycle_norm = None

        try:
            market_tier_norm = normalize_market_tier(market_tier_raw)
        except ValueError as exc:
            row_errors.append(NormalizerIssue(0, "market_tier", str(exc)))
            market_tier_norm = None

        try:
            country_norm = normalize_country(country_raw)
        except ValueError as exc:
            row_errors.append(NormalizerIssue(0, "country_code", str(exc)))
            country_norm = None

        try:
            partner_type_norm = normalize_partner_type(partner_type_raw)
        except ValueError as exc:
            row_errors.append(NormalizerIssue(0, "partner_type", str(exc)))
            partner_type_norm = None

        # ── Commercial Performance (T02) ──────────────────────────────────────
        revenue_raw = get(TemplateId.COMMERCIAL_PERFORMANCE, "Annual_Revenue_USD")
        target_raw = get(TemplateId.COMMERCIAL_PERFORMANCE, "Sales_Target_USD")
        sell_in_raw = get(TemplateId.COMMERCIAL_PERFORMANCE, "Sell_In_Units")
        sell_out_raw = get(TemplateId.COMMERCIAL_PERFORMANCE, "Sell_Out_Units")
        yoy_raw = get(TemplateId.COMMERCIAL_PERFORMANCE, "YoY_Growth_Percent")
        new_prod_rev_raw = get(TemplateId.COMMERCIAL_PERFORMANCE, "New_Product_Revenue_Percent")

        yoy_norm = _parse_percent_cell(yoy_raw)
        new_prod_norm = _parse_percent_cell(new_prod_rev_raw)

        # ── Operational Health (T03) ───────────────────────────────────────────
        inv_days_raw = get(TemplateId.OPERATIONAL_HEALTH, "Inventory_Days")
        forecast_raw = get(TemplateId.OPERATIONAL_HEALTH, "Forecast_Accuracy_Percent")
        reporting_raw = get(TemplateId.OPERATIONAL_HEALTH, "Reporting_Timeliness_Percent")

        inv_days_norm = float(inv_days_raw) if inv_days_raw is not None else None
        forecast_norm = _parse_percent_cell(forecast_raw)
        reporting_norm = _parse_percent_cell(reporting_raw)

        # ── Financial Health (T04) ─────────────────────────────────────────────
        payment_raw = get(TemplateId.FINANCIAL_HEALTH, "Payment_On_Time_Percent")
        outstanding_ar_raw = get(TemplateId.FINANCIAL_HEALTH, "Outstanding_AR_USD")
        overdue_ar_raw = get(TemplateId.FINANCIAL_HEALTH, "Overdue_AR_USD")

        payment_norm = _parse_percent_cell(payment_raw)
        # ar_overdue_90d_pct = Overdue_AR_USD / Outstanding_AR_USD * 100
        if outstanding_ar_raw and outstanding_ar_raw > 0:
            ar_ratio = (float(overdue_ar_raw) / float(outstanding_ar_raw)) * 100.0 if overdue_ar_raw else 0.0
        else:
            ar_ratio = None

        # ── Service Capability (T05) ───────────────────────────────────────────
        engineers_raw = get(TemplateId.SERVICE_CAPABILITY, "Certified_Engineer_Count")
        training_raw = get(TemplateId.SERVICE_CAPABILITY, "Training_Completion_Percent")
        demo_machines_raw = get(TemplateId.SERVICE_CAPABILITY, "Demo_Machine_Count")

        engineers_norm = int(float(engineers_raw)) if engineers_raw is not None else None
        training_norm = _parse_percent_cell(training_raw)
        # demo_capability: True if Demo_Machine_Count > 0, None if unknown
        if demo_machines_raw is not None:
            try:
                demo_cap_norm: bool | None = int(float(demo_machines_raw)) > 0
            except (ValueError, TypeError):
                demo_cap_norm = None
        else:
            demo_cap_norm = None

        # ── Compliance Governance (T06) ─────────────────────────────────────────
        incidents_raw = get(TemplateId.COMPLIANCE_GOVERNANCE, "Confirmed_Compliance_Incident")
        unauthorized_raw = get(TemplateId.COMPLIANCE_GOVERNANCE, "Unauthorized_Sales_Signal")
        fraud_raw = get(TemplateId.COMPLIANCE_GOVERNANCE, "Data_Fraud_Flag")

        incidents_norm = int(float(incidents_raw)) if incidents_raw is not None else None
        unauthorized_norm = int(float(unauthorized_raw)) if unauthorized_raw is not None else None
        fraud_norm = _parse_bool_cell(fraud_raw)

        # ── Target Rationale (T07) ─────────────────────────────────────────────
        tr_revenue_raw = get(TemplateId.TARGET_RATIONALE, "Current_Revenue_USD")
        tr_target_raw = get(TemplateId.TARGET_RATIONALE, "Proposed_Target_USD")
        tr_hist_growth_raw = get(TemplateId.TARGET_RATIONALE, "Historical_Growth_Percent")
        tr_pipeline_raw = get(TemplateId.TARGET_RATIONALE, "Pipeline_Value_USD")
        tr_new_cust_raw = get(TemplateId.TARGET_RATIONALE, "New_Customer_Plan")
        tr_coverage_raw = get(TemplateId.TARGET_RATIONALE, "Coverage_Expansion_Plan")
        tr_resource_raw = get(TemplateId.TARGET_RATIONALE, "Resource_Commitment")
        tr_new_prod_raw = get(TemplateId.TARGET_RATIONALE, "New_Product_Plan")

        tr_revenue_norm = float(tr_revenue_raw) if tr_revenue_raw is not None else None
        tr_target_norm = float(tr_target_raw) if tr_target_raw is not None else None
        tr_hist_growth_norm = _parse_percent_cell(tr_hist_growth_raw)
        tr_pipeline_norm = float(tr_pipeline_raw) if tr_pipeline_raw is not None else None
        tr_new_cust_norm = int(float(tr_new_cust_raw)) if tr_new_cust_raw is not None else None

        try:
            tr_resource_norm = normalize_resource_commitment(tr_resource_raw)
        except ValueError:
            tr_resource_norm = None

        try:
            tr_new_prod_norm = normalize_new_product_plan(tr_new_prod_raw)
        except ValueError:
            tr_new_prod_norm = None

        # coverage_pct: Excel provides absolute Coverage_Expansion_Plan (count),
        # not a percentage. Cannot derive without a denominator.
        # Mark as None and let Confidence reflect the gap.
        tr_coverage_norm: float | None = None

        canonical[pid] = _PartnerRow(
            partner_id=pid,
            partner_name=str(get(TemplateId.PARTNER_MASTER, "Partner_Name") or "").strip() or None,
            business_line=str(get(TemplateId.PARTNER_MASTER, "Business_Line") or "").strip() or None,
            country_code=country_norm,
            region=str(get(TemplateId.PARTNER_MASTER, "Region") or "").strip() or None,
            lifecycle_stage=lifecycle_norm,
            market_tier=market_tier_norm,
            partner_type=partner_type_norm,
            annual_revenue=float(revenue_raw) if revenue_raw is not None else None,
            yoy_growth_pct=yoy_norm,
            new_product_contribution_pct=new_prod_norm,
            inventory_days=inv_days_norm,
            forecast_accuracy_pct=forecast_norm,
            data_reporting_quality_pct=reporting_norm,
            payment_on_time_pct=payment_norm,
            ar_overdue_90d_pct=ar_ratio,
            certified_engineers=engineers_norm,
            training_completion_pct=training_norm,
            demo_capability=demo_cap_norm,
            pricing_violations=incidents_norm,
            unauthorized_sales_incidents=unauthorized_norm,
            material_contract_breach=fraud_norm,
            tr_current_revenue=tr_revenue_norm,
            tr_proposed_target=tr_target_norm,
            tr_historical_growth_pct=tr_hist_growth_norm,
            tr_pipeline_value=tr_pipeline_norm,
            tr_new_customer_plan=tr_new_cust_norm,
            tr_coverage_pct=tr_coverage_norm,
            tr_new_product_potential_pct=tr_new_prod_norm,
            tr_resource_commitment=tr_resource_norm,
            tr_inventory_days=inv_days_norm,
            tr_ar_overdue_90d_pct=ar_ratio,
        )

        issues.extend(row_errors)

    return canonical


# ──────────────────────────────────────────────────────────────────────────────
# Derived metrics
# ──────────────────────────────────────────────────────────────────────────────

def _compute_derived_metrics(
    row: _PartnerRow,
    target_ach: float | None,
    sell_out_perf: float | None,
) -> tuple[dict[str, DerivedMetric], list[NormalizerIssue]]:
    """Derive computed metrics from raw template fields.

    Returns a dict of metric-name → DerivedMetric and any warnings.
    """
    derived: dict[str, DerivedMetric] = {}
    issues: list[NormalizerIssue] = []

    # 1. target_achievement_pct = Annual_Revenue / Sales_Target * 100
    derived["target_achievement_pct"] = DerivedMetric(
        name="target_achievement_pct",
        value=target_ach,
        source_fields=("Annual_Revenue_USD", "Sales_Target_USD"),
        formula="Annual_Revenue_USD / Sales_Target_USD * 100",
        is_none_because=(
            None if target_ach is not None
            else "Sales_Target_USD or Annual_Revenue_USD was null; cannot compute."
        ),
    )
    if target_ach is None:
        issues.append(NormalizerIssue(
            0, "target_achievement_pct",
            "Cannot derive target_achievement_pct: required source fields are null."
        ))

    # 2. sell_out_performance_pct = Sell_Out_Units / Sell_In_Units * 100
    derived["sell_out_performance_pct"] = DerivedMetric(
        name="sell_out_performance_pct",
        value=sell_out_perf,
        source_fields=("Sell_Out_Units", "Sell_In_Units"),
        formula="Sell_Out_Units / Sell_In_Units * 100",
        is_none_because=(
            None if sell_out_perf is not None
            else "Sell_In_Units or Sell_Out_Units was null; cannot compute."
        ),
    )
    if sell_out_perf is None:
        issues.append(NormalizerIssue(
            0, "sell_out_performance_pct",
            "Cannot derive sell_out_performance_pct: required source fields are null."
        ))

    # 3. ar_overdue_90d_pct
    derived["ar_overdue_90d_pct"] = DerivedMetric(
        name="ar_overdue_90d_pct",
        value=row.ar_overdue_90d_pct,
        source_fields=("Overdue_AR_USD", "Outstanding_AR_USD"),
        formula="Overdue_AR_USD / Outstanding_AR_USD * 100",
        is_none_because=(
            None if row.ar_overdue_90d_pct is not None
            else "Overdue_AR_USD or Outstanding_AR_USD was null; cannot compute."
        ),
    )

    # 4. demo_capability
    derived["demo_capability"] = DerivedMetric(
        name="demo_capability",
        value=row.demo_capability,
        source_fields=("Demo_Machine_Count",),
        formula="Demo_Machine_Count > 0 → True else False",
        is_none_because=(
            "Demo_Machine_Count was null." if row.demo_capability is None else None
        ),
    )

    # 5. active_dealers: no reliable proxy in Excel templates
    derived["active_dealers"] = DerivedMetric(
        name="active_dealers",
        value=None,
        source_fields=(),
        formula="N/A",
        is_none_because=(
            "No proxy field exists in the Excel templates for active_dealers. "
            "Add 'Active_Dealer_Count' to the template. "
            "MARKET_CAPABILITY pillar scoring will be affected. "
            "Confidence will be reduced accordingly."
        ),
    )
    issues.append(NormalizerIssue(
        0, "active_dealers",
        "active_dealers cannot be derived from the current Excel templates. "
        "MARKET_CAPABILITY pillar scoring will be affected."
    ))

    # 6. geographic_coverage_pct: no proxy
    derived["geographic_coverage_pct"] = DerivedMetric(
        name="geographic_coverage_pct",
        value=None,
        source_fields=(),
        formula="N/A",
        is_none_because=(
            "No proxy field exists for geographic_coverage_pct in the current templates. "
            "Add 'Geographic_Coverage_Percent' to Template 01 or 02."
        ),
    )
    issues.append(NormalizerIssue(
        0, "geographic_coverage_pct",
        "geographic_coverage_pct cannot be derived from the current Excel templates. "
        "MARKET_CAPABILITY pillar scoring will be affected."
    ))

    return derived, issues


# ──────────────────────────────────────────────────────────────────────────────
# Canonical → PartnerRecord
# ──────────────────────────────────────────────────────────────────────────────

def _build_partner_record(
    row: _PartnerRow,
    target_ach: float | None,
    sell_out_perf: float | None,
    all_issues: list[NormalizerIssue],
) -> tuple[PartnerRecord | None, list[NormalizerIssue]]:
    """Convert an intermediate _PartnerRow to a validated PartnerRecord."""
    row_issues: list[NormalizerIssue] = []

    def _lifecycle(val: str | None) -> LifecycleStage | None:
        if val is None:
            return None
        try:
            return LifecycleStage(val)
        except ValueError:
            row_issues.append(NormalizerIssue(
                0, "lifecycle_stage",
                f"'{val}' is not a valid LifecycleStage enum value."
            ))
            return None

    def _market_tier(val: str | None) -> MarketTier | None:
        if val is None:
            return None
        if val == "MID_VALUE":
            row_issues.append(NormalizerIssue(
                0, "market_tier",
                f"'{val}' requires MarketTier enum extension in models.py. "
                f"Currently only HIGH_VALUE, GROWTH_VALUE, DEVELOPING are supported."
            ))
            return None
        try:
            return MarketTier(val)
        except ValueError:
            row_issues.append(NormalizerIssue(
                0, "market_tier",
                f"'{val}' is not a valid MarketTier enum value."
            ))
            return None

    def _partner_type(val: str | None) -> PartnerType | None:
        if val is None:
            return None
        try:
            return PartnerType(val)
        except ValueError:
            row_issues.append(NormalizerIssue(
                0, "partner_type",
                f"'{val}' is not a valid PartnerType enum value."
            ))
            return None

    try:
        record = PartnerRecord(
            partner_id=row.partner_id,
            partner_name=row.partner_name or "",
            business_line=row.business_line or "",
            country_code=row.country_code or "",
            region=row.region,
            lifecycle_stage=_lifecycle(row.lifecycle_stage),
            market_tier=_market_tier(row.market_tier),
            partner_type=_partner_type(row.partner_type),
            annual_revenue=row.annual_revenue,
            target_achievement_pct=target_ach,
            yoy_growth_pct=row.yoy_growth_pct,
            new_product_contribution_pct=row.new_product_contribution_pct,
            # active_dealers: not in Excel templates
            # geographic_coverage_pct: not in Excel templates
            inventory_days=row.inventory_days,
            sell_out_performance_pct=sell_out_perf,
            forecast_accuracy_pct=row.forecast_accuracy_pct,
            data_reporting_quality_pct=row.data_reporting_quality_pct,
            payment_on_time_pct=row.payment_on_time_pct,
            ar_overdue_90d_pct=row.ar_overdue_90d_pct,
            certified_engineers=row.certified_engineers,
            training_completion_pct=row.training_completion_pct,
            demo_capability=row.demo_capability,
            pricing_violations=row.pricing_violations,
            unauthorized_sales_incidents=row.unauthorized_sales_incidents,
            # sanctions_match: not in Excel templates
            material_contract_breach=row.material_contract_breach,
        )
        return record, row_issues
    except ValidationError as exc:
        for err in exc.errors():
            loc = ".".join(str(l) for l in err["loc"])
            row_issues.append(NormalizerIssue(0, loc, err["msg"]))
        return None, row_issues


def _build_target_rationale_input(
    row: _PartnerRow,
) -> TargetRationaleInput | None:
    """Build TargetRationaleInput from _PartnerRow."""
    lifecycle = None
    if row.lifecycle_stage:
        try:
            lifecycle = LifecycleStage(row.lifecycle_stage)
        except ValueError:
            return None

    try:
        return TargetRationaleInput(
            current_revenue=row.tr_current_revenue,
            proposed_target=row.tr_proposed_target,
            historical_growth_pct=row.tr_historical_growth_pct,
            current_sell_out_pct=row.tr_current_sell_out_pct,
            lifecycle_stage=lifecycle,
            market_capability_score=row.tr_market_capability_score,
            pipeline_value=row.tr_pipeline_value,
            new_customer_plan=row.tr_new_customer_plan,
            coverage_pct=row.tr_coverage_pct,
            new_product_potential_pct=row.tr_new_product_potential_pct,
            resource_commitment=row.tr_resource_commitment,
            inventory_days=row.tr_inventory_days,
            ar_overdue_90d_pct=row.tr_ar_overdue_90d_pct,
        )
    except (ValidationError, ValueError):
        return None


# ──────────────────────────────────────────────────────────────────────────────
# Data quality score
# ──────────────────────────────────────────────────────────────────────────────

# Fields that count towards the quality score (subset of PartnerRecord optional fields)
_QUALITY_FIELDS = (
    "annual_revenue",
    "yoy_growth_pct",
    "new_product_contribution_pct",
    "active_dealers",
    "geographic_coverage_pct",
    "inventory_days",
    "sell_out_performance_pct",
    "forecast_accuracy_pct",
    "data_reporting_quality_pct",
    "payment_on_time_pct",
    "ar_overdue_90d_pct",
    "certified_engineers",
    "training_completion_pct",
    "demo_capability",
    "pricing_violations",
    "unauthorized_sales_incidents",
    "material_contract_breach",
)
_TOTAL_QUALITY_FIELDS = len(_QUALITY_FIELDS)


def _compute_quality_score(records: list[PartnerRecord]) -> float:
    if not records:
        return 0.0
    total_non_null = 0
    for rec in records:
        for f in _QUALITY_FIELDS:
            if getattr(rec, f, None) is not None:
                total_non_null += 1
    return round(total_non_null / (len(records) * _TOTAL_QUALITY_FIELDS), 4)


# ──────────────────────────────────────────────────────────────────────────────
# Multi-template join validation
# ──────────────────────────────────────────────────────────────────────────────

def _validate_join(
    rows_by_template: dict[TemplateId, list[dict]],
) -> list[NormalizerIssue]:
    """Check for join-key anomalies across all templates."""
    issues: list[NormalizerIssue] = []

    # Collect all partner IDs per template
    pid_sets: dict[TemplateId, set[str]] = {}
    for tid, rows in rows_by_template.items():
        pids = set()
        for r in rows:
            pid = str(r.get("Partner_ID") or "").strip()
            if pid:
                pids.add(pid)
        pid_sets[tid] = pids

    all_pids = set()
    for pids in pid_sets.values():
        all_pids |= pids

    # Missing Partner_ID
    for tid, rows in rows_by_template.items():
        for ridx, r in enumerate(rows, start=1):
            pid = str(r.get("Partner_ID") or "").strip()
            if not pid:
                issues.append(NormalizerIssue(
                    ridx, "Partner_ID",
                    f"Missing Partner_ID in template '{tid.value}'."
                ))

    # Duplicate Partner_ID within a template
    for tid, rows in rows_by_template.items():
        seen: dict[str, int] = {}
        for ridx, r in enumerate(rows, start=1):
            pid = str(r.get("Partner_ID") or "").strip()
            if pid:
                if pid in seen:
                    issues.append(NormalizerIssue(
                        ridx, "Partner_ID",
                        f"Duplicate Partner_ID '{pid}' in template '{tid.value}' "
                        f"(first seen on row {seen[pid]})."
                    ))
                seen[pid] = ridx

    # Partner present in some templates but not all (warning, not error)
    for pid in all_pids:
        missing = [tid for tid, pids in pid_sets.items() if pid not in pids]
        if missing:
            issues.append(NormalizerIssue(
                0, "cross_template_join",
                f"Partner '{pid}' is missing from template(s): "
                f"{', '.join(t.value for t in missing)}. "
                f"Metrics from those templates will not be available for this partner."
            ))

    return issues


# ──────────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────────

def normalize_excel_templates(
    templates: dict[TemplateId, pd.DataFrame],
) -> NormalizationResult:
    """Normalize a set of Excel template DataFrames to canonical PartnerRecords.

    Parameters
    ----------
    templates : dict[TemplateId, pd.DataFrame]
        Mapping from template ID to raw DataFrame as read by openpyxl / pandas.

    Returns
    -------
    NormalizationResult
        Contains validated PartnerRecord list, per-partner derived metrics,
        data quality score, and structured issues.
    """
    all_issues: list[NormalizerIssue] = []
    rows_by_template: dict[TemplateId, list[dict]] = {}

    # ── 1. Template-level type normalization ───────────────────────────────────
    for tid, df in templates.items():
        schema = TEMPLATES[tid]
        try:
            rows, template_issues = _normalize_template_raw(df, schema)
            rows_by_template[tid] = rows
            all_issues.extend(template_issues)
        except ValueError as exc:
            all_issues.append(NormalizerIssue(-1, tid.value, str(exc)))
            rows_by_template[tid] = []

    # ── 2. Cross-template join validation ────────────────────────────────────
    all_issues.extend(_validate_join(rows_by_template))

    # ── 3. Field mapping and enum normalization ───────────────────────────────
    canonical_rows = _map_row(rows_by_template, all_issues)

    # ── 4. Derived metrics + PartnerRecord conversion ───────────────────────
    partner_records: list[PartnerRecord] = []
    target_inputs: list[TargetRationaleInput] = []
    derived_metrics: dict[str, list[DerivedMetric]] = {}

    for pid, crow in canonical_rows.items():
        # Derive from T02 raw values before conversion
        t02_rows = rows_by_template.get(TemplateId.COMMERCIAL_PERFORMANCE, [])
        target_ach: float | None = None
        sell_out_perf: float | None = None
        for trow in t02_rows:
            if str(trow.get("Partner_ID") or "").strip() == pid:
                tgt = trow.get("Sales_Target_USD")
                rev = trow.get("Annual_Revenue_USD")
                si = trow.get("Sell_In_Units")
                so = trow.get("Sell_Out_Units")
                if tgt and rev:
                    try:
                        t_val = float(str(tgt)); r_val = float(str(rev))
                        if t_val > 0:
                            target_ach = round((r_val / t_val) * 100.0, 4)
                    except (ValueError, TypeError):
                        pass
                if si and so:
                    try:
                        si_val = float(str(si)); so_val = float(str(so))
                        if si_val > 0:
                            sell_out_perf = round((so_val / si_val) * 100.0, 4)
                    except (ValueError, TypeError):
                        pass
                break

        derived, deriv_issues = _compute_derived_metrics(crow, target_ach, sell_out_perf)
        derived_metrics[pid] = derived
        all_issues.extend(deriv_issues)

        record, build_issues = _build_partner_record(crow, target_ach, sell_out_perf, all_issues)
        all_issues.extend(build_issues)
        if record is not None:
            partner_records.append(record)

        tri = _build_target_rationale_input(crow)
        if tri is not None:
            target_inputs.append(tri)

    # ── 5. Data quality score ────────────────────────────────────────────────
    quality_score = _compute_quality_score(partner_records)

    success = (
        len(partner_records) > 0
        and not any(i.row == -1 for i in all_issues)
    )

    return NormalizationResult(
        success=success,
        partner_records=partner_records,
        target_inputs=target_inputs,
        issues=all_issues,
        derived_metrics=derived_metrics,
        data_quality_score=quality_score,
    )
