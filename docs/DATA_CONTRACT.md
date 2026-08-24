# Synthetic Partner Data Contract

Version: 1.0.0  
Canonical implementation: `channel_governance.models.PartnerRecord`

Every row is one synthetic partner observation for one evaluation run. Empty
metric cells are accepted as missing observations; they are never converted to
zero. Identifier and segmentation fields are mandatory. The validator rejects
unknown columns, invalid enumerations, impossible percentages, negative counts,
and malformed country codes.

## Segmentation and identifiers

| Field | Type | Required | Rule |
|---|---|---:|---|
| `partner_id` | string | yes | Non-empty, unique within the source file |
| `partner_name` | string | yes | Synthetic display name |
| `business_line` | string | yes | Policy context, not a hard-coded company fact |
| `country_code` | string | yes | Two-letter uppercase code |
| `lifecycle_stage` | enum | yes | `BUILD`, `EMERGING`, `GROWTH`, `MATURE`, `MAINTENANCE` |
| `market_tier` | enum | yes | `HIGH_VALUE`, `GROWTH_VALUE`, `DEVELOPING` |
| `partner_type` | enum | yes | `DISTRIBUTOR`, `DEALER` |

## Scored observations

All fields below are nullable. Percentage fields accept `0..100`, except target
achievement (`0..300`) and growth (`-100..500`). Counts and revenue are
non-negative.

| Pillar | Fields |
|---|---|
| Commercial | `annual_revenue`, `target_achievement_pct`, `yoy_growth_pct`, `new_product_contribution_pct` |
| Market | `active_dealers`, `geographic_coverage_pct` |
| Operational | `inventory_days`, `sell_out_performance_pct`, `forecast_accuracy_pct`, `data_reporting_quality_pct` |
| Financial | `payment_on_time_pct`, `ar_overdue_90d_pct` |
| Capability | `certified_engineers`, `training_completion_pct`, `demo_capability` |
| Compliance | `pricing_violations`, `unauthorized_sales_incidents` |

`annual_revenue` is retained for context but is intentionally not scored in the
v1 synthetic policy. This prevents absolute scale from silently dominating
partner health.

## Gate-only signals

`sanctions_match` and `material_contract_breach` are nullable booleans. A true
value triggers human-review gates. A blank value means unknown, not false.
The system does not make a legal finding.

## Validation output

Validation returns valid typed records and row-level issues containing source
row, field, and message. Portfolio evaluation is fail-closed: no scores are
produced while contract errors remain.
