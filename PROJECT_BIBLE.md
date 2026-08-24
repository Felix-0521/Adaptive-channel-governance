# Adaptive Channel Governance & Partner Scoring Platform
## Repository SSOT — v1.1.0

Status: **ACTIVE / AUTHORITATIVE FOR IMPLEMENTATION**  
Updated: **2026-08-25**  
Data policy: **Synthetic only**

This repository-local SSOT records the implemented product decisions from the
frozen v1.0 specification and the approved Policy Studio / Scenario /
Recommended Action update. Code, configuration, UI, tests, and documentation
must use the terminology and invariants below.

## Product invariants

- Rule-driven, data-driven, AI-assisted; never AI-scored.
- Explainable and configurable; never black-box or hidden fallback.
- Missing data is unknown, never zero.
- Risk is independent from score.
- Gate evaluation precedes growth action.
- Decision support requires human review and never automatically sets price,
  margin, rebate, credit, freeze, or termination.
- The core application runs without an API key or cloud dependency.

## Canonical policy context

Every evaluation context contains:

1. Business Line
2. Lifecycle Stage
3. Market Tier
4. Partner Type
5. Optional Country Override

Resolution priority is fixed:

```text
Country Override
→ Exact Business × Lifecycle × Market Tier × Partner Type
→ Business + Lifecycle
→ Lifecycle
→ Global Default
```

The selected source must be returned to the UI. Unsupported match shapes and
missing global fallback are validation errors.

## Canonical Pillars and two-level weighting

```text
COMMERCIAL_PERFORMANCE
MARKET_CAPABILITY
OPERATIONAL_HEALTH
FINANCIAL_HEALTH
SERVICE_TECH_CAPABILITY
COMPLIANCE_GOVERNANCE
```

Rules:

- Six Pillar Weights independently total 100%.
- Metric Weights independently total 100% inside each Pillar.
- Changing Pillar Weight never changes Metric Weight.
- Invalid totals cannot be saved.
- All weights originate in Policy Configuration.

Calculation:

```text
Metric Score × Metric Weight → Pillar Score
Pillar Score × Pillar Weight → Partner Score
Observed weighted inputs / configured weighted inputs → Confidence
```

## Policy lifecycle

```text
Active v1 → Draft v2 → Scenario Tested → Activate v2 → v1 Archived
```

- Saving a Draft cannot change dashboard results, official score, or tier.
- Scenario uses a temporary Policy Repository and cannot mutate Active Policy.
- Activation requires a scenario-tested Draft.
- Activation records timestamp, policy ID, old version, new version, actor, and
  change reason.
- A newly activated Country Override does not archive its inherited parent.

## Scenario scopes and output

Scopes: Single Partner, Selected Market, Full Portfolio.

Selected Market supports Country, Business Line, Market Tier, and Lifecycle
filters. Output compares baseline/scenario Score, Tier, Risk, and Governance
Status and reports average score change, upgrades, downgrades, tier migration,
largest impacts, and tier counts before/after.

A weight-only scenario must not redefine Risk or Gate logic.

## Recommended Action

Canonical output fields:

```text
Action
Priority: HIGH | MEDIUM | LOW
Reason
Evidence
Human Review Required
```

Growth actions:

```text
BRANDING_MDF
ENGINEER_SUPPORT
DEMO_SUPPORT
TRAINING_CERTIFICATION
NEW_PRODUCT_ENABLEMENT
CHANNEL_EXPANSION
JOINT_BUSINESS_PLANNING
AFTERSALES_CAPABILITY
```

Governance actions:

```text
INVENTORY_OPTIMIZATION
CREDIT_REVIEW
DATA_QUALITY_IMPROVEMENT
CORRECTIVE_ACTION_PLAN
COMPLIANCE_REVIEW
NO_ADDITIONAL_SUPPORT
```

Actions must use Lifecycle, Business, Pillar Breakdown, Metric Breakdown, Risk,
and Gate context. They must not be mapped directly from total Score. Critical
Gate and High Risk actions take precedence over growth actions.

## Current MVP boundary

Included: synthetic data, validation, adaptive Policy, two-level weights,
Country Override, lifecycle/audit, scoring, confidence, Risk, Gate, Tier,
Governance Status, Recommended Action, Executive Overview, Partner 360, Policy
Studio, Scenario Lab, Data Quality, and tests.

Deferred: real CRM/ERP integration, automatic commercial decisions,
multi-user approvals, role permissions, persistent policy database, target
rationale, external market data, and mandatory AI APIs.

