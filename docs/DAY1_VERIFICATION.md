# Day 1 Phase 0–2 Verification Record

## Phase 0 — Repository and runtime

- Python runtime: 3.12
- Local virtual environment: `.venv` (ignored by Git)
- Declared stack: Streamlit, Pandas, Plotly, Pydantic, PyYAML, SQLite, Pytest
- UI/domain separation: `app.py` composes services; rules live under `src/`
- Suggested commit: `chore: initialize Python 3.12 project structure`

## Phase 1 — Synthetic data and validation

- 12 fictional partner rows across multiple business, country, lifecycle, and
  partner-type contexts
- Strict Pydantic contract and actionable DataFrame validation
- Missing values remain missing
- Suggested commit: `feat: add synthetic partner data contract and validator`

## Phase 2A — Policy and score

- YAML policy version and default/specialized policy resolution
- Six-pillar weighted scoring with metric-level explanation
- Linear, inverse-linear, Boolean, and optimal-band normalization
- Confidence calculated from observed weighted inputs
- Suggested commit: `feat: implement adaptive policy and scoring engines`

## Phase 2B — Governance decisions

- Risk signals remain independent from score
- Critical gates can hold a high-scoring partner without rewriting its score
- Tier, governance status, and human-review recommendations
- SQLite schema boundary ready for evaluation/audit persistence
- Suggested commit: `feat: add risk gates tiers and recommendations`

## Commands

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m streamlit run app.py
```

## Latest verified result — 2026-08-24

- `pytest`: **18 passed**
- Python bytecode compilation: **passed**
- Streamlit headless smoke test: **server started successfully** on a local port
- Git repository: initialized on branch `main`; no commit created because no
  author identity is configured in this workspace

The counts above should be refreshed whenever tests or policies change; Git
history remains the authoritative record of when each stage is committed.
