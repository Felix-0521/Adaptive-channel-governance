# Business Metric Dictionary & Data Contract Finalization

> **Document version:** 1.0
> **System:** Adaptive Channel Governance & Partner Scoring Platform
> **Status:** FROZEN — Any change to these definitions requires a policy review cycle.
> **Owner:** Sales Operations / Channel Management
> **Reviewed:** 2026-08-25

---

## Overview

This document is the authoritative Business Metric Dictionary for the Adaptive Channel Governance
platform. Every scoring metric is documented with:

- **Field Name** — canonical name in `PartnerRecord` / `scoring_rules.yaml`
- **Business Definition** — what the metric measures and why
- **Business Owner** — which department provides / owns the data
- **Input Source** — which Excel template and column provides the raw data
- **Required / Optional** — data policy for this field
- **Calculation Rule** — how raw input becomes the canonical value
- **Scoring Impact** — normalization method and pillar/weight assignment
- **Confidence Impact** — how missing data affects confidence
- **Classification** — Customer Input / Derived Metric / External Verification Signal / Deferred

---

## Metric Definitions

### A. Commercial Performance (Pillar weight: 25%)

---

#### `target_achievement_pct`

| Property | Value |
|---|---|
| **Field Name** | `target_achievement_pct` |
| **Business Definition** | Actual revenue achieved as a percentage of the agreed sales target. Measures how reliably the partner hits commercial commitments. |
| **Business Owner** | Sales Operations / Finance |
| **Input Source** | `02_Commercial_Performance_Template.xlsx` · `Annual_Revenue_USD` ÷ `Sales_Target_USD` × 100 |
| **Required / Optional** | Optional (reduces Commercial Pillar coverage if missing) |
| **Calculation Rule** | `Annual_Revenue_USD / Sales_Target_USD × 100` — if either source is null, metric is None |
| **Scoring Method** | Linear normalization: bad=50, good=110. Score = 0 if <50, 100 if ≥110. |
| **Pillar** | `COMMERCIAL_PERFORMANCE` |
| **Metric Weight** | 0.40 (40% of Commercial Pillar) |
| **Confidence Impact** | If null: reduces effective weight; Confidence score decreases proportionally. |
| **Classification** | **Derived Metric** — requires two input fields from Template 02 |

---

#### `yoy_growth_pct`

| Property | Value |
|---|---|
| **Field Name** | `yoy_growth_pct` |
| **Business Definition** | Year-over-year revenue growth percentage. Positive values indicate market expansion; negative values indicate contraction. |
| **Business Owner** | Finance / Sales Operations |
| **Input Source** | `02_Commercial_Performance_Template.xlsx` · `YoY_Growth_Percent` |
| **Required / Optional** | Optional |
| **Calculation Rule** | `normalize_percent(YoY_Growth_Percent)` — accepts "15%", 15, 0.15; negative values allowed |
| **Scoring Method** | Linear normalization: bad=-20, good=30. Score = 0 if ≤-20, 100 if ≥30. |
| **Pillar** | `COMMERCIAL_PERFORMANCE` |
| **Metric Weight** | 0.35 (35% of Commercial Pillar) |
| **Confidence Impact** | If null: reduces effective weight. |
| **Classification** | **Customer Input** — directly provided by business |

---

#### `new_product_contribution_pct`

| Property | Value |
|---|---|
| **Field Name** | `new_product_contribution_pct` |
| **Business Definition** | Percentage of total revenue from newly introduced products. Indicates the partner's ability to bring innovation to market. |
| **Business Owner** | Product / Sales Operations |
| **Input Source** | `02_Commercial_Performance_Template.xlsx` · `New_Product_Revenue_Percent` |
| **Required / Optional** | Optional |
| **Calculation Rule** | `normalize_percent(New_Product_Revenue_Percent)` |
| **Scoring Method** | Linear normalization: bad=0, good=30. |
| **Pillar** | `COMMERCIAL_PERFORMANCE` |
| **Metric Weight** | 0.25 (25% of Commercial Pillar) |
| **Confidence Impact** | If null: reduces effective weight. |
| **Classification** | **Customer Input** — directly provided by business |

---

### B. Market Capability (Pillar weight: 15%)

---

#### `active_dealers`

| Property | Value |
|---|---|
| **Field Name** | `active_dealers` |
| **Business Definition** | Number of active sub-dealers or sub-distributors that regularly purchase from this partner. Indicates channel reach and market penetration. |
| **Business Owner** | Sales Operations |
| **Input Source** | **NOT IN CURRENT TEMPLATES** — requires new field in `02_Commercial_Performance_Template.xlsx` |
| **Required / Optional** | Optional (but has high scoring weight) |
| **Calculation Rule** | N/A — no source field exists in the current 7 templates |
| **Scoring Method** | Linear normalization: bad=0, good=30 |
| **Pillar** | `MARKET_CAPABILITY` |
| **Metric Weight** | 0.50 (50% of Market Capability Pillar) |
| **Confidence Impact** | Always null in current system → MARKET_CAPABILITY pillar has 0% effective weight → Confidence reduced by 15%. |
| **Classification** | **Deferred** — requires `Active_Dealer_Count` column in Template 02 or 01 |

> **Action Required:** Add `Active_Dealer_Count` (int) to the Partner Master or Commercial Performance template. Until then, `active_dealers` is always null and this pillar cannot contribute to the score.

---

#### `geographic_coverage_pct`

| Property | Value |
|---|---|
| **Field Name** | `geographic_coverage_pct` |
| **Business Definition** | Percentage of the partner's assigned territory or geographic area that is actively served. |
| **Business Owner** | Sales Operations / Channel Management |
| **Input Source** | **NOT IN CURRENT TEMPLATES** — requires new field |
| **Required / Optional** | Optional |
| **Calculation Rule** | N/A — no source field exists in the current 7 templates |
| **Scoring Method** | Linear normalization: bad=20, good=90 |
| **Pillar** | `MARKET_CAPABILITY` |
| **Metric Weight** | 0.50 (50% of Market Capability Pillar) |
| **Confidence Impact** | Always null in current system → same as `active_dealers` above. |
| **Classification** | **Deferred** — requires `Geographic_Coverage_Percent` column in Template 01 or 02 |

> **Action Required:** Add `Geographic_Coverage_Percent` (percent, 0–100) to the Partner Master template. Until then, this pillar cannot contribute to the score.

---

### C. Operational Health (Pillar weight: 20%)

---

#### `inventory_days`

| Property | Value |
|---|---|
| **Field Name** | `inventory_days` |
| **Business Definition** | Average number of days of inventory held by the partner before selling to the next tier. Lower values indicate efficient stock turnover; very low values risk stockouts, very high values indicate slow-moving stock. |
| **Business Owner** | Operations / Supply Chain |
| **Input Source** | `03_Operational_Health_Template.xlsx` · `Inventory_Days` |
| **Required / Optional** | Optional |
| **Calculation Rule** | Direct float value from template (integer days) |
| **Scoring Method** | Optimal band: low=45, high=90, hard_low=0, hard_high=180. Score=100 if in [45, 90]; linear interpolation outside the band. |
| **Pillar** | `OPERATIONAL_HEALTH` |
| **Metric Weight** | 0.40 (40% of Operational Health Pillar) |
| **Confidence Impact** | If null: reduces effective weight. |
| **Classification** | **Customer Input** — directly provided by business |

---

#### `sell_out_performance_pct`

| Property | Value |
|---|---|
| **Field Name** | `sell_out_performance_pct` |
| **Business Definition** | Volume of product sold to the next tier (sub-dealers/end users) relative to volume purchased from us (sell-in). Ratio >100% means the partner is reducing inventory; ratio <100% means inventory accumulation. |
| **Business Owner** | Operations / Sales Operations |
| **Input Source** | `02_Commercial_Performance_Template.xlsx` · `Sell_Out_Units` ÷ `Sell_In_Units` × 100 |
| **Required / Optional** | Optional |
| **Calculation Rule** | `Sell_Out_Units / Sell_In_Units × 100` — if either source is null, metric is None |
| **Scoring Method** | Linear normalization: bad=50, good=110 |
| **Pillar** | `OPERATIONAL_HEALTH` |
| **Metric Weight** | 0.35 (35% of Operational Health Pillar) |
| **Confidence Impact** | If null: reduces effective weight. |
| **Classification** | **Derived Metric** — requires two input fields from Template 02 |

---

#### `forecast_accuracy_pct`

| Property | Value |
|---|---|
| **Field Name** | `forecast_accuracy_pct` |
| **Business Definition** | Accuracy of the partner's demand forecast versus actual purchase orders. High forecast accuracy enables efficient supply chain planning. |
| **Business Owner** | Operations / Supply Chain |
| **Input Source** | `03_Operational_Health_Template.xlsx` · `Forecast_Accuracy_Percent` |
| **Required / Optional** | Optional |
| **Calculation Rule** | `normalize_percent(Forecast_Accuracy_Percent)` |
| **Scoring Method** | Linear normalization: bad=40, good=90 |
| **Pillar** | `OPERATIONAL_HEALTH` |
| **Metric Weight** | 0.15 (15% of Operational Health Pillar) |
| **Confidence Impact** | If null: reduces effective weight. |
| **Classification** | **Customer Input** — directly provided by business |

---

#### `data_reporting_quality_pct`

| Property | Value |
|---|---|
| **Field Name** | `data_reporting_quality_pct` |
| **Business Definition** | Quality score for the partner's data reporting timeliness and completeness. Higher scores indicate the partner reliably reports sales, inventory, and operational data on schedule. |
| **Business Owner** | Operations / Sales Operations |
| **Input Source** | `03_Operational_Health_Template.xlsx` · `Reporting_Timeliness_Percent` |
| **Required / Optional** | Optional |
| **Calculation Rule** | `normalize_percent(Reporting_Timeliness_Percent)` |
| **Scoring Method** | Linear normalization: bad=40, good=100 |
| **Pillar** | `OPERATIONAL_HEALTH` |
| **Metric Weight** | 0.10 (10% of Operational Health Pillar) |
| **Confidence Impact** | If null: reduces effective weight. |
| **Classification** | **Customer Input** — directly provided by business |

---

### D. Financial Health (Pillar weight: 15%)

---

#### `payment_on_time_pct`

| Property | Value |
|---|---|
| **Field Name** | `payment_on_time_pct` |
| **Business Definition** | Percentage of invoices paid on or before the due date. High on-time payment rates indicate healthy financial discipline. |
| **Business Owner** | Finance / Credit |
| **Input Source** | `04_Financial_Health_Template.xlsx` · `Payment_On_Time_Percent` |
| **Required / Optional** | Optional |
| **Calculation Rule** | `normalize_percent(Payment_On_Time_Percent)` |
| **Scoring Method** | Linear normalization: bad=50, good=98 |
| **Pillar** | `FINANCIAL_HEALTH` |
| **Metric Weight** | 0.60 (60% of Financial Health Pillar) |
| **Confidence Impact** | If null: reduces effective weight. |
| **Classification** | **Customer Input** — directly provided by business |

---

#### `ar_overdue_90d_pct`

| Property | Value |
|---|---|
| **Field Name** | `ar_overdue_90d_pct` |
| **Business Definition** | Proportion of outstanding accounts receivable that is overdue by more than 90 days. High values indicate collection risk and potential credit exposure. |
| **Business Owner** | Finance / Credit |
| **Input Source** | `04_Financial_Health_Template.xlsx` · `Overdue_AR_USD` ÷ `Outstanding_AR_USD` × 100 |
| **Required / Optional** | Optional |
| **Calculation Rule** | `Overdue_AR_USD / Outstanding_AR_USD × 100` — if either source is null, metric is None |
| **Scoring Method** | Inverse linear normalization: good=0, bad=30. Higher overdue % = lower score. |
| **Pillar** | `FINANCIAL_HEALTH` |
| **Metric Weight** | 0.40 (40% of Financial Health Pillar) |
| **Confidence Impact** | If null: reduces effective weight. Also triggers `AR_OVERDUE_HIGH` gate check when >20%. |
| **Classification** | **Derived Metric** — requires two input fields from Template 04 |

---

### E. Service & Technical Capability (Pillar weight: 15%)

---

#### `certified_engineers`

| Property | Value |
|---|---|
| **Field Name** | `certified_engineers` |
| **Business Definition** | Number of engineers employed by the partner who hold current product certifications. Indicates the partner's technical capacity to install, configure, and support the product. |
| **Business Owner** | Technical Enablement |
| **Input Source** | `05_Service_Capability_Template.xlsx` · `Certified_Engineer_Count` |
| **Required / Optional** | Optional |
| **Calculation Rule** | Integer count from template |
| **Scoring Method** | Linear normalization: bad=0, good=5 |
| **Pillar** | `SERVICE_TECH_CAPABILITY` |
| **Metric Weight** | 0.40 (40% of Service Capability Pillar) |
| **Confidence Impact** | If null: reduces effective weight. |
| **Classification** | **Customer Input** — directly provided by business |

---

#### `training_completion_pct`

| Property | Value |
|---|---|
| **Field Name** | `training_completion_pct` |
| **Business Definition** | Percentage of required training modules completed by the partner's team within the evaluation period. |
| **Business Owner** | Technical Enablement |
| **Input Source** | `05_Service_Capability_Template.xlsx` · `Training_Completion_Percent` |
| **Required / Optional** | Optional |
| **Calculation Rule** | `normalize_percent(Training_Completion_Percent)` |
| **Scoring Method** | Linear normalization: bad=20, good=95 |
| **Pillar** | `SERVICE_TECH_CAPABILITY` |
| **Metric Weight** | 0.30 (30% of Service Capability Pillar) |
| **Confidence Impact** | If null: reduces effective weight. |
| **Classification** | **Customer Input** — directly provided by business |

---

#### `demo_capability`

| Property | Value |
|---|---|
| **Field Name** | `demo_capability` |
| **Business Definition** | Whether the partner has at least one demonstration machine or equipment available for prospect demonstrations. Indicates sales enablement and market-facing capability. |
| **Business Owner** | Technical Enablement / Sales |
| **Input Source** | `05_Service_Capability_Template.xlsx` · `Demo_Machine_Count` |
| **Required / Optional** | Optional |
| **Calculation Rule** | `Demo_Machine_Count > 0 → True; Demo_Machine_Count == 0 → False; null → None` |
| **Scoring Method** | Boolean: True = 100, False = 0 |
| **Pillar** | `SERVICE_TECH_CAPABILITY` |
| **Metric Weight** | 0.30 (30% of Service Capability Pillar) |
| **Confidence Impact** | If null: reduces effective weight. |
| **Classification** | **Derived Metric** — derived from `Demo_Machine_Count` |

---

### F. Compliance & Governance (Pillar weight: 10%)

---

#### `pricing_violations`

| Property | Value |
|---|---|
| **Field Name** | `pricing_violations` |
| **Business Definition** | Number of confirmed incidents where the partner deviated from agreed pricing policies (e.g., selling below minimum price, unauthorized discounts). |
| **Business Owner** | Compliance / Legal / Sales Operations |
| **Input Source** | `06_Compliance_Governance_Template.xlsx` · `Confirmed_Compliance_Incident` |
| **Required / Optional** | Optional |
| **Calculation Rule** | Integer count from template |
| **Scoring Method** | Inverse linear normalization: good=0, bad=3. Higher violations = lower score. |
| **Pillar** | `COMPLIANCE_GOVERNANCE` |
| **Metric Weight** | 0.40 (40% of Compliance Pillar) |
| **Confidence Impact** | If null: reduces effective weight. Also triggers `PRICING_VIOLATION` gate when >0. |
| **Classification** | **External Verification Signal** — confirmed incidents from compliance system |

---

#### `unauthorized_sales_incidents`

| Property | Value |
|---|---|
| **Field Name** | `unauthorized_sales_incidents` |
| **Business Definition** | Number of incidents where the partner sold products outside their authorized territory or to unauthorized customers. |
| **Business Owner** | Compliance / Legal |
| **Input Source** | `06_Compliance_Governance_Template.xlsx` · `Unauthorized_Sales_Signal` |
| **Required / Optional** | Optional |
| **Calculation Rule** | Integer count from template |
| **Scoring Method** | Inverse linear normalization: good=0, bad=2 |
| **Pillar** | `COMPLIANCE_GOVERNANCE` |
| **Metric Weight** | 0.60 (60% of Compliance Pillar) |
| **Confidence Impact** | If null: reduces effective weight. Also triggers `UNAUTHORIZED_SALES` gate when >0. |
| **Classification** | **External Verification Signal** — flagged incidents from compliance system |

---

#### `sanctions_match`

| Property | Value |
|---|---|
| **Field Name** | `sanctions_match` |
| **Business Definition** | Whether the partner appears on applicable trade sanctions or restricted party lists. True = sanctions match confirmed. |
| **Business Owner** | Legal / Compliance |
| **Input Source** | **NOT IN CURRENT TEMPLATES** — no source column exists |
| **Required / Optional** | Optional |
| **Calculation Rule** | Always null in current system (no source data) |
| **Scoring Method** | Boolean: True = 0 (CRITICAL risk), False = not scored by this metric |
| **Pillar** | `COMPLIANCE_GOVERNANCE` (gate signal only) |
| **Metric Weight** | Not in scoring metrics — used as a Gate signal |
| **Confidence Impact** | Always null → not included in confidence denominator |
| **Classification** | **Deferred** — requires sanctions screening integration |

> **Action Required:** Add `Sanctions_Match` (boolean: TRUE/FALSE) to `06_Compliance_Governance_Template.xlsx`. Until then, this field is always null.

---

#### `material_contract_breach`

| Property | Value |
|---|---|
| **Field Name** | `material_contract_breach` |
| **Business Definition** | Whether the partner has committed a material breach of their distribution agreement (e.g., significant contractual violation, fraud, or data falsification). True = breach confirmed. |
| **Business Owner** | Legal / Compliance |
| **Input Source** | `06_Compliance_Governance_Template.xlsx` · `Data_Fraud_Flag` |
| **Required / Optional** | Optional |
| **Calculation Rule** | `normalize_bool(Data_Fraud_Flag)` — "TRUE"/"FALSE" strings → Python bool |
| **Scoring Method** | Boolean: True = 0 (CRITICAL risk), False = not scored by this metric |
| **Pillar** | `COMPLIANCE_GOVERNANCE` (gate signal only) |
| **Metric Weight** | Not in scoring metrics — used as a Gate signal |
| **Confidence Impact** | If null: not included in confidence denominator |
| **Classification** | **External Verification Signal** — confirmed breach/fraud from legal system |

---

## Context Fields (Not Scored)

These fields define the evaluation context and drive policy resolution but are not themselves scored:

| Field | Source Template | Values | Policy Driver |
|---|---|---|---|
| `partner_id` | T01 | String | Join key |
| `partner_name` | T01 | String | Display only |
| `business_line` | T01 | AGRICULTURE, GEOSPATIAL_SURVEYING, LANDSCAPING, FACILITY_SERVICES, CONSTRUCTION | Policy match dimension |
| `country_code` | T01 | PL, DE, FR, ES, SE (ISO 3166-1 alpha-2) | Country override lookup |
| `region` | T01 | CEE, DACH, WEST_EU, SOUTH_EU, etc. | Context display |
| `lifecycle_stage` | T01 | ENTRY, BUILD, EMERGING, GROWTH, MATURE, MAINTENANCE, DECLINE | Policy match dimension |
| `market_tier` | T01 | HIGH_VALUE, GROWTH_VALUE, DEVELOPING | Policy match dimension |
| `partner_type` | T01 | DISTRIBUTOR, DEALER | Policy match dimension |

---

## Target Rationale Inputs

These fields are used by `target_rationale.assess_target()` to evaluate proposed sales targets:

| Field | Source Template | Classification |
|---|---|---|
| `current_revenue` | T07 `Current_Revenue_USD` | Customer Input |
| `proposed_target` | T07 `Proposed_Target_USD` | Customer Input |
| `historical_growth_pct` | T07 `Historical_Growth_Percent` | Customer Input |
| `pipeline_value` | T07 `Pipeline_Value_USD` | Customer Input |
| `new_customer_plan` | T07 `New_Customer_Plan` | Customer Input |
| `coverage_pct` | T07 `Coverage_Expansion_Plan` | **Deferred** — template provides integer count, not % |
| `resource_commitment` | T07 `Resource_Commitment` | Customer Input |
| `new_product_potential_pct` | T07 `New_Product_Plan` | **Derived** — "High"→80%, "Medium"→50%, "Low"→20% |
| `inventory_days` | T03 `Inventory_Days` | Customer Input |
| `ar_overdue_90d_pct` | T04 derived | Derived Metric |

---

## Deferred Field Action Register

The following fields are used by the scoring engine but have no current source in the Excel templates. They must be addressed in a future template update:

| Priority | Field | Pillar Impact | Recommended Action |
|---|---|---|---|
| **HIGH** | `Active_Dealer_Count` → `active_dealers` | MARKET_CAPABILITY = 0% | Add integer column to T02 |
| **HIGH** | `Geographic_Coverage_Percent` → `geographic_coverage_pct` | MARKET_CAPABILITY = 0% | Add percent column to T01 |
| **MEDIUM** | `Sanctions_Match` → `sanctions_match` | Gate only | Add boolean column to T06 |
| **LOW** | `Coverage_Expansion_Plan` (count → pct) | Target Rationale | Add explicit `Coverage_Pct` column to T07 |

---

## Market Tier Extension Register

| Tier | Canonical Value | In `MarketTier` Enum | Status |
|---|---|---|---|
| HIGH_VALUE | `HIGH_VALUE` | ✅ Yes | Fully supported |
| GROWTH_VALUE | `GROWTH_VALUE` | ✅ Yes | Fully supported |
| DEVELOPING | `DEVELOPING` | ✅ Yes | Fully supported |
| **MID_VALUE** | `MID_VALUE` | ❌ **No** | Extended in normalizer; requires `MarketTier.MID_VALUE` in `models.py` |

**Recommended Action:** Add `MID_VALUE = "MID_VALUE"` to `MarketTier` in `models.py`. The normalizer currently accepts `MID_VALUE` as an extended value but `PartnerRecord` validation will reject it until the enum is updated.

---

## Data Quality Thresholds

| Threshold | Value | Source |
|---|---|---|
| `minimum_confidence` | 0.70 | If `active_dealers` and `geographic_coverage_pct` are null, MARKET_CAPABILITY pillar (15% of total score) is effectively 0% → confidence ≈ 0.85 |
| `ar_overdue_90d_high_pct` | 20% | Gate trigger: `AR_OVERDUE_HIGH` if `ar_overdue_90d_pct` > 20 |
| `inventory_days_high` | 90 days | Gate trigger: `INVENTORY_HIGH` if `inventory_days` > 90 |
| `inventory_days_low` | 45 days | Gate trigger: `INVENTORY_LOW` if `inventory_days` < 45 |

---

## Pillar Weight Summary

| Pillar | Weight | Metrics with Data | Effective Coverage |
|---|---|---|---|
| COMMERCIAL_PERFORMANCE | 25% | 3/3 | ✅ 100% (when target_ach data available) |
| MARKET_CAPABILITY | 15% | 0/2 | ❌ 0% (no source for active_dealers or coverage) |
| OPERATIONAL_HEALTH | 20% | 4/4 | ✅ 100% |
| FINANCIAL_HEALTH | 15% | 2/2 | ✅ 100% |
| SERVICE_TECH_CAPABILITY | 15% | 3/3 | ✅ 100% |
| COMPLIANCE_GOVERNANCE | 10% | 2/4 | ✅ 50% (gate signals missing sanctions_match) |

**System Confidence at full data coverage: ~85%** (market capability pillar has no data in current templates)
