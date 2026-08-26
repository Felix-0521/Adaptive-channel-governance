# Data Normalization Layer Design

> **Document version:** 1.0
> **System:** Adaptive Channel Governance & Partner Scoring Platform
> **Purpose:** Explain how raw Excel template data is transformed into the canonical `PartnerRecord` format consumed by the existing evaluation engine.
> **Audience:** Engineers, product architects, and business analysts integrating the normalization layer.

---

## 1. Why a Normalization Layer Exists

The existing evaluation engine (`evaluation.py`) is built around a strict data contract: `PartnerRecord`. It assumes:

- ISO 3166-1 alpha-2 country codes (`country_code: str`, 2 characters)
- Python enums for `lifecycle_stage`, `market_tier`, `partner_type`
- Numeric percentages in the range 0–100 (never "85%", never 0.85)
- Boolean flags for `demo_capability`, `material_contract_breach`, etc.

Business users fill Excel templates that use:

- Free-form country names ("Poland", "Germany")
- Enum values that differ from the Python enums ("MID_VALUE" vs "HIGH_VALUE")
- Percentage strings ("85%")
- Qualitative plan levels ("High", "Medium")
- Raw fields that require derivation (e.g., Sell_Out / Sell_In)

The normalization layer bridges this gap. It is a **pure transformation layer**: it reads Excel template DataFrames and emits validated `PartnerRecord` objects. It does not score, evaluate, persist, or recommend — it only normalizes.

---

## 2. Raw vs. Canonical Data Model

### Raw Input (Excel Templates)

| Template | Source | Join Key | Notable Raw Fields |
|---|---|---|---|
| `01_Partner_Master_Template.xlsx` | Sales Ops | `Partner_ID` | Country name, free-text enums |
| `02_Commercial_Performance_Template.xlsx` | Finance | `Partner_ID` | Revenue/target integers, % strings |
| `03_Operational_Health_Template.xlsx` | Operations | `Partner_ID` | Inventory days, forecast accuracy |
| `04_Financial_Health_Template.xlsx` | Finance | `Partner_ID` | AR amounts, payment % |
| `05_Service_Capability_Template.xlsx` | Technical | `Partner_ID` | Engineer count, machine count |
| `06_Compliance_Governance_Template.xlsx` | Compliance | `Partner_ID` | Boolean strings ("FALSE") |
| `07_Target_Rationale_Template.xlsx` | Sales Planning | `Partner_ID` | Qualitative plan levels |

### Canonical Output (`PartnerRecord`)

All fields match the `models.py` contract exactly:

```
partner_id          str
partner_name        str
business_line       str
country_code        str  (ISO alpha-2, e.g. "PL")
region              str | None
lifecycle_stage     LifecycleStage  (ENTRY, BUILD, GROWTH, ...)
market_tier         MarketTier      (HIGH_VALUE, GROWTH_VALUE, DEVELOPING)
partner_type        PartnerType     (DISTRIBUTOR, DEALER)
annual_revenue      float | None
target_achievement_pct float | None  (0–300, derived)
yoy_growth_pct     float | None     (can be negative)
new_product_contribution_pct float | None (0–100)
inventory_days      float | None     (0–730)
sell_out_performance_pct float | None (0–200, derived)
forecast_accuracy_pct float | None   (0–100)
data_reporting_quality_pct float | None (0–100)
payment_on_time_pct float | None    (0–100)
ar_overdue_90d_pct  float | None   (derived)
certified_engineers int | None
training_completion_pct float | None (0–100)
demo_capability     bool | None     (derived: Demo_Machine_Count > 0)
pricing_violations  int | None
unauthorized_sales_incidents int | None
material_contract_breach bool | None
sanctions_match     bool | None     (not in Excel — always None)
```

---

## 3. Field Mapping

### Excel → PartnerRecord

| Excel Column | Template | PartnerRecord Field | Transformation |
|---|---|---|---|
| `Partner_ID` | T01 | `partner_id` | Direct pass-through |
| `Partner_Name` | T01 | `partner_name` | Direct pass-through |
| `Country` | T01 | `country_code` | Country name → ISO alpha-2 via `mappings.normalize_country()` |
| `Region` | T01 | `region` | Direct pass-through |
| `Business_Line` | T01 | `business_line` | Direct pass-through |
| `Partner_Type` | T01 | `partner_type` | `mappings.normalize_partner_type()` |
| `Lifecycle_Stage` | T01 | `lifecycle_stage` | `mappings.normalize_lifecycle_stage()` |
| `Market_Tier` | T01 | `market_tier` | `mappings.normalize_market_tier()` (MID_VALUE → MID_VALUE) |
| `Annual_Revenue_USD` | T02 | `annual_revenue` | Float cast |
| `YoY_Growth_Percent` | T02 | `yoy_growth_pct` | `mappings.normalize_percent()` |
| `New_Product_Revenue_Percent` | T02 | `new_product_contribution_pct` | `mappings.normalize_percent()` |
| `Inventory_Days` | T03 | `inventory_days` | Float cast |
| `Forecast_Accuracy_Percent` | T03 | `forecast_accuracy_pct` | `mappings.normalize_percent()` |
| `Reporting_Timeliness_Percent` | T03 | `data_reporting_quality_pct` | `mappings.normalize_percent()` |
| `Payment_On_Time_Percent` | T04 | `payment_on_time_pct` | `mappings.normalize_percent()` |
| `Overdue_AR_USD / Outstanding_AR_USD` | T04 | `ar_overdue_90d_pct` | Derived ratio × 100 |
| `Certified_Engineer_Count` | T05 | `certified_engineers` | Int cast |
| `Training_Completion_Percent` | T05 | `training_completion_pct` | `mappings.normalize_percent()` |
| `Demo_Machine_Count` | T05 | `demo_capability` | `count > 0 → True` |
| `Confirmed_Compliance_Incident` | T06 | `pricing_violations` | Int cast |
| `Unauthorized_Sales_Signal` | T06 | `unauthorized_sales_incidents` | Int cast |
| `Data_Fraud_Flag` | T06 | `material_contract_breach` | `mappings.normalize_bool()` |

---

## 4. Transformation Rules

### 4.1 Country Normalization

```
Input: "Poland"  |  Output: "PL"
Input: "DE"       |  Output: "DE"
Input: "France"   |  Output: "FR"
Input: None        |  Output: None
Input: "Neverland" |  ValueError raised
```

Supported countries: Poland, Germany, France, Spain, Sweden.

### 4.2 Enum Normalization

**Lifecycle Stage:**
```
"ENTRY" / "entry" / "Entry"  → LifecycleStage.ENTRY
"BUILD"                        → LifecycleStage.BUILD
"GROWTH"                       → LifecycleStage.GROWTH
"MATURE"                        → LifecycleStage.MATURE
"DECLINE"                       → LifecycleStage.DECLINE
```

**Market Tier:**
```
"HIGH_VALUE" / "high_value"  → MarketTier.HIGH_VALUE
"GROWTH_VALUE"               → MarketTier.GROWTH_VALUE
"DEVELOPING"                  → MarketTier.DEVELOPING
"MID_VALUE" / "mid_value"    → "MID_VALUE"  (extended; requires models.py update)
```

**Partner Type:**
```
"DISTRIBUTOR" / "distributor"  → PartnerType.DISTRIBUTOR
"DEALER"                       → PartnerType.DEALER
```

### 4.3 Percentage Parsing

Accepts three input forms and normalizes all to float 0–100:

```
"85%"   → 85.0
85      → 85.0
0.85    → 85.0  (auto-detected as decimal fraction, scaled)
"-20%"  → -20.0 (negative allowed for growth metrics)
```

### 4.4 Boolean Parsing

Accepts: `true/false`, `yes/no`, `1/0`, `on/off` (case-insensitive). Empty string → `None`.

---

## 5. Derived Metrics

### 5.1 `target_achievement_pct`

```
Annual_Revenue_USD / Sales_Target_USD × 100
```

**Source fields:** T02 `Annual_Revenue_USD`, T02 `Sales_Target_USD`
**If either is null:** value = None, warning emitted

### 5.2 `sell_out_performance_pct`

```
Sell_Out_Units / Sell_In_Units × 100
```

**Source fields:** T02 `Sell_Out_Units`, T02 `Sell_In_Units`
**If either is null:** value = None, warning emitted

### 5.3 `ar_overdue_90d_pct`

```
Overdue_AR_USD / Outstanding_AR_USD × 100
```

**Source fields:** T04 `Overdue_AR_USD`, T04 `Outstanding_AR_USD`
**If either is null:** value = None, warning emitted

### 5.4 `demo_capability`

```
Demo_Machine_Count > 0 → True
Demo_Machine_Count == 0 → False
Demo_Machine_Count is null → None
```

### 5.5 Unavailable Metrics

The following `PartnerRecord` fields cannot be derived from the current Excel templates and are always `None`:

- `active_dealers` — no proxy column exists
- `geographic_coverage_pct` — no proxy column exists
- `sanctions_match` — no source in any template

These gaps reduce the **Confidence** score in the evaluation engine (lower weight coverage).

---

## 6. Validation Rules

### 6.1 Cross-Template Join (Partner_ID)

| Check | Severity | Outcome |
|---|---|---|
| Missing `Partner_ID` in a row | Error | Row rejected, `NormalizerIssue` reported |
| Duplicate `Partner_ID` within a template | Error | Both rows rejected, `NormalizerIssue` reported |
| Partner present in T01 but missing from T03–T07 | Warning | `NormalizerIssue` with missing template list |

### 6.2 Enum Validation

| Field | Valid Values | Invalid → |
|---|---|---|
| `Lifecycle_Stage` | ENTRY, BUILD, EMERGING, GROWTH, MATURE, MAINTENANCE, DECLINE | `ValueError` → `NormalizerIssue` |
| `Market_Tier` | HIGH_VALUE, GROWTH_VALUE, DEVELOPING, MID_VALUE | `ValueError` → `NormalizerIssue` |
| `Partner_Type` | DISTRIBUTOR, DEALER | `ValueError` → `NormalizerIssue` |
| `Country` | PL, DE, FR, ES, SE (or full English names) | `ValueError` → `NormalizerIssue` |

### 6.3 Data Quality Score

```
data_quality_score = non_null_metric_fields / (num_partners × total_optional_fields)
```

Where optional fields = 17 metrics from `PartnerRecord` (annual_revenue, yoy_growth_pct, etc.).
Range: 0.0–1.0. A record with only T01 filled has score ≈ 0.1; a fully populated record ≈ 0.6.

### 6.4 NormalizationResult Structure

```python
@dataclass(frozen=True)
class NormalizationResult:
    success: bool                    # True if no errors and at least one record
    partner_records: list[PartnerRecord]  # Validated canonical records
    target_inputs: list[TargetRationaleInput]  # Target rationale inputs
    issues: list[NormalizerIssue]    # All issues (errors + warnings)
    derived_metrics: dict[str, list[DerivedMetric]]  # Per-partner log
    data_quality_score: float       # 0.0–1.0

    @property
    def errors(self) -> list[NormalizerIssue]:   # row=-1 or contains "error"
    @property
    def warnings(self) -> list[NormalizerIssue]: # row!=-1 and not "error"
```

---

## 7. Error Handling

### Silent-Fallback Prohibition

The normalizer **never silently converts unknown values**:

- Unknown country → `ValueError` → `NormalizerIssue`
- Unknown enum → `ValueError` → `NormalizerIssue`
- Unparseable percentage → `ValueError` → `NormalizerIssue`
- Missing required column → `ValueError` → `NormalizerIssue`

### Non-Crashing Design

`normalize_excel_templates()` never raises an exception to the caller. All errors are captured in `NormalizationResult.issues`. The caller can inspect `result.success` and `result.errors` to decide how to present issues to the user.

### Evaluation Engine Compatibility

Normalized `PartnerRecord` objects are fully compatible with `evaluation.evaluate_partner()`. All Pydantic validation runs at the `PartnerRecord` construction step. Any `ValidationError` is caught and converted to a `NormalizerIssue`.

---

## 8. Data Flow

```
Business Excel Files
        │
        ▼
  openpyxl / pandas  ─── reads sheet as DataFrame
        │
        ▼
  _normalize_template_raw()  ─── type parsing, empty-string cleanup
        │
        ▼
  _validate_join()  ─── Partner_ID integrity checks
        │
        ▼
  _map_row()  ─── Excel columns → canonical fields, enum normalization
        │
        ▼
  _compute_derived_metrics()  ─── ratios, booleans from raw counts
        │
        ▼
  _build_partner_record()  ─── Pydantic PartnerRecord construction
        │
        ▼
  NormalizationResult
   ├── partner_records: list[PartnerRecord]  ───→ evaluation.evaluate_partner()
   ├── target_inputs: list[TargetRationaleInput]  ───→ target_rationale.assess_target()
   ├── issues: list[NormalizerIssue]  ───→ UI feedback
   └── data_quality_score: float  ───→ confidence indicator
```

---

## 9. Known Limitations

| Limitation | Impact | Mitigation |
|---|---|---|
| `MarketTier.MID_VALUE` not in existing enum | MID_VALUE tier rejected | Emit issue; partner scored without market_tier |
| `active_dealers` / `geographic_coverage_pct` not derivable | MARKET_CAPABILITY pillar weight reduced | Emit warning; Confidence score reflects gap |
| `sanctions_match` not in Excel templates | Always `None` | Emit warning |
| Coverage_Expansion_Plan is count (not %) | `coverage_pct` for TargetRationaleInput cannot be derived | Emit warning; user must fill manually |
| Country set limited to 5 countries | Partners in other countries rejected | Emit `ValueError`; country list is extensible |
| Only one policy supported per `PolicyRepository.from_yaml()` | Portfolio evaluation uses one policy | Already a system constraint, not new |

---

## 10. Module Map

```
src/channel_governance/
  mappings.py           — Pure mapping functions (country, enum, percent, bool)
  template_schema.py   — Template schemas (field definitions, types, required flags)
  data_normalizer.py   — Pipeline orchestration (join, map, derive, build)

tests/
  test_data_normalizer.py  — 52 tests covering all normalization functions

docs/
  DATA_NORMALIZATION_DESIGN.md  — This document
```
