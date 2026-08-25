# Adaptive Channel Governance & Partner Scoring Platform
## Repository SSOT — v1.4.0

Status: **ACTIVE / AUTHORITATIVE FOR IMPLEMENTATION**  
Updated: **2026-08-25**  
Data policy: **Synthetic only**

This repository-local SSOT records the implemented product decisions from the
frozen v1.0 specification and the approved Policy Studio, Scenario,
Recommended Action, Management Insight, and Target Rationale updates. Code,
configuration, UI, tests, and documentation must use the terminology and
invariants below. The former term `Support Recommendation` is retired;
`Recommended Action` is canonical in every layer.

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

## Management Insight

Deterministic Management Insight is the authoritative, offline explanation
layer. It reads Partner Context and the existing Evaluation Result; it never
recalculates or mutates Score, Confidence, Tier, Risk, Gate, Governance Status,
or Recommended Action. Its canonical output is:

```text
Severity: INFO | ATTENTION | WARNING | CRITICAL
Executive Summary
Key Drivers
Management Attention
Recommended Next Step
Data Limitations
```

Driver ranking prioritizes Critical Gate, Critical Risk, High Risk, Low
Confidence, material metric weakness, and normal observations. Metric drivers
must expose observed value, configured benchmark/threshold, and weighted impact.
Without historical observations the system may describe distance to the policy
benchmark, but must not claim a change. Insufficient evidence uses the explicit
statement `Insufficient evidence to determine the primary cause.`

## Optional AI Insight and provider boundary

Rules-based insight is the default. AI may only explain, summarize, compare,
highlight, or rephrase supplied facts. It cannot calculate or change domain
results, invent causes or policy, issue legal conclusions, or make final
commercial decisions.

Only a whitelist-based Structured Management Context may cross the provider
boundary; raw DataFrames, uploaded CSV rows, and API keys must never be sent as
context or persisted. `OPENAI_API_KEY` is environment-only. Missing
configuration, dependency, timeout, provider, quota, network, or response
validation errors must fall back to the deterministic insight without breaking
Partner 360. The core application remains fully functional without AI.

## Target Rationale

Target Rationale is a decision-support sanity check for a user-supplied Proposed
Target. It does not set, recommend, approve, or reject a sales target. Canonical
assessments are:

```text
SUPPORTED
STRETCH
REVIEW_REQUIRED
INSUFFICIENT_EVIDENCE
```

Inputs may include Current Revenue, Proposed Target, Historical Growth, Current
Sell-out, Lifecycle Stage, Market Capability, Pipeline Value, New Customer Plan,
Coverage, New Product Potential, Resource Commitment, and existing governance
signals. Outputs include Proposed Target, Required Growth, Assessment,
Confidence, Supporting Drivers, Constraining Drivers, Required Assumptions, and
Management Review. Missing inputs reduce confidence.

ENTRY, BUILD, and EMERGING contexts emphasize pipeline, first customers,
capability, and footprint expansion rather than a low historical base. MATURE
contexts emphasize historical growth, sell-out, productivity, inventory, and
new-product evidence. DECLINE contexts apply greater caution to aggressive
growth. High/Critical governance risk and gates constrain the rationale but do
not create an approval workflow.

The following policy thresholds are configurable and never hard-coded in UI:
`pipeline_coverage_supported`, `pipeline_coverage_stretch`,
`max_historical_growth_deviation`, and `minimum_target_confidence`.

Tests must cover deterministic severity/driver/evidence behavior, AI provider
failure and privacy boundaries, all four Target Assessment values, lifecycle
sensitivity, governance constraints, missingness, Partner 360 startup, and the
existing regression suite.

## Current MVP boundary

Included: synthetic data, validation, adaptive Policy, two-level weights,
Country Override, lifecycle/audit, scoring, confidence, Risk, Gate, Tier,
Governance Status, Recommended Action, Executive Overview, Partner 360, Policy
Studio, Scenario Lab, Data Quality, deterministic Management Insight, optional
AI-enhanced explanation, Target Rationale, Partner Management, and tests.

Deferred: real CRM/ERP integration, automatic commercial decisions,
multi-user approvals, role permissions, external market data, mandatory AI
APIs, RAG, machine learning, and automatic target approval.

## SQLite persistence boundary

The local prototype persists Policy snapshots and lifecycle Audit History in
`data/app.db`, which is created automatically and excluded from Git. The YAML
Policy file remains the first-run seed. Stored Policy state includes version,
status, Country Override, Pillar/Metric weights, Scenario Tested, and activation
state. Stored Audit fields include timestamp, actor, action, entity, old/new
values, reason, and version. Draft save, scenario test, and activation are
transactionally persisted and survive application restart.

SQLite remains a local single-user prototype boundary. It does not add
authentication, role permissions, approval workflow, or production deployment.

## Partner Management boundary

Partner Management may create a Partner from management Context or import CSV
through Validation, Preview, and explicit Confirm Import. Partner ID is
generated when absent. Managed Partner records persist in `data/app.db` and are
combined with immutable Synthetic Demo records at runtime.

Required management fields are Partner Name, Country, Region, Business Line,
Partner Type, Lifecycle Stage, and Market Tier. Optional commercial observations
remain unknown when absent and reduce Confidence; the system must not invent a
Score. Created/imported records use the existing Adaptive Policy, scoring,
Risk, Gate, Tier, Governance Status, Recommended Action, and Management Insight
engines without alternative business logic. Duplicate Partner ID or Partner
Name + Country is rejected.

The current dependency baseline supports CSV import. Excel import is deferred
unless an Excel engine is intentionally added. The Streamlit interface is
Chinese-first and preserves canonical English product and technical terms.
