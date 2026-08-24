# Adaptive Channel Governance & Partner Scoring Platform

[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-45%20passing-2E7D32)](tests/)
[![Data](https://img.shields.io/badge/data-synthetic%20only-555555)](data/sample_partners.csv)

An explainable, policy-driven decision-support MVP for global Sales Operations
and Channel Management teams. It demonstrates how an ambiguous governance
problem can be translated into configurable rules, tested domain logic, and a
runnable product without company data or paid APIs.

> All names, observations, thresholds, policy weights, and business values in
> this repository are synthetic demonstration material. No real partner,
> price, margin, rebate, credit, revenue, or commercial policy data is used.

## Business problem

One-size-fits-all partner evaluation obscures differences between businesses,
countries, lifecycle stages, and partner types. A strong sell-in number may
coexist with excess inventory, deteriorating receivables, weak service
capability, or a critical compliance signal.

This project turns that problem into an auditable decision flow:

```mermaid
flowchart LR
    A[Validated partner data] --> B[Adaptive policy]
    B --> C[Metric and pillar scores]
    C --> D[Confidence]
    A --> E[Independent risk signals]
    A --> F[Critical gates]
    C --> G[Partner tier]
    D --> H[Governance status]
    E --> H
    F --> H
    G --> I[Recommended Action]
    H --> I
```

## Main functions

- Strict Pydantic data contract with row-level validation feedback
- Business/country/lifecycle-aware YAML policy resolution
- Explicit Country Override → Exact Context → Business + Lifecycle → Lifecycle
  → Global Default inheritance with visible policy source
- Policy Studio with independently validated Pillar and Metric weights
- Draft → Scenario Tested → Active → Archived lifecycle and activation audit
- Explainable metric, pillar, and overall partner scoring
- Confidence based on observed weighted inputs; missing data is never zero
- Inventory optimal-band scoring instead of “lower is always better”
- Risk signals reported independently from overall partner quality
- Critical gates capable of holding a high-scoring partner for human review
- Partner tier, governance status, and structured Recommended Actions
- Single Partner, Selected Market, and Full Portfolio scenario comparison
- Executive overview, Partner 360, Policy Studio, Scenario Lab, Data Quality,
  and Audit Log UI
- SQLite schema boundary for later evaluation and audit persistence

The score never automatically determines price, margin, rebate, credit limit,
partner freeze, or termination.

## Run locally

Python 3.12 is the canonical runtime.

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pytest
python -m streamlit run app.py
```

### macOS / Linux

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest
python -m streamlit run app.py
```

Open the local URL printed by Streamlit. No API key, database preparation,
cloud account, or manual data download is required.

## Architecture

The Streamlit layer composes application services but contains no scoring,
risk, gate, or tier rules. Domain code is independently testable.

```text
app.py                         Streamlit presentation layer
config/scoring_rules.yaml      Versioned synthetic policy configuration
data/sample_partners.csv       Fictional demonstration observations
src/channel_governance/
  models.py                    Pydantic input/output contracts
  validation.py                DataFrame validation boundary
  policy.py                    Resolution, lifecycle, activation audit
  scoring.py                   Normalization, score, confidence
  governance.py                Risk, gates, tier, status, Recommended Action
  evaluation.py                Application orchestration service
  scenario.py                  Multi-scope baseline/draft comparison
  storage.py                   SQLite schema boundary
tests/                         Unit and end-to-end tests
docs/                          Data contract and verification evidence
AI_USAGE.md                    Truthful AI-assisted development record
```

## Verification

```powershell
python -m pytest
```

Current verified result: **45 tests passed**. Tests include a full Streamlit
application execution check, two-level weight
validation, score propagation, explicit fallback sources, Country Overrides,
Draft/Active isolation, activation audit, three scenario scopes, tier
migration, risk stability, structured Recommended Actions, missing data,
critical gates, SQLite setup, and complete portfolio evaluation. See the
[adaptive policy workflow](docs/POLICY_WORKFLOW.md).

## AI-assisted development

AI assisted requirement decomposition, implementation, test generation,
debugging, and documentation. Deterministic business rules remain inspectable
and test-covered, and the core product has no AI runtime dependency. See
[AI_USAGE.md](AI_USAGE.md) for the actual development record and rejected
approaches.

## Roadmap

- Stable now: data contract, adaptive policies, two-level weights, Country
  Overrides, lifecycle/audit, scoring, confidence, risk, gates, tiers,
  Recommended Actions, Executive Overview, Partner 360, Policy Studio,
  Scenario Lab, Data Quality, and tests
- Next: target rationale and persistent SQLite policy/audit storage
- Later: optional deterministic or LLM-based management narrative

P0 stability and fresh-clone reproducibility take priority over optional
features and artificial line-count expansion.
