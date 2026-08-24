# AI-Assisted Development Record

This file documents actual AI assistance used during development. It is not a
claim that AI independently designed, accepted, or verified the product.

## Responsibility model

- Human-defined inputs: project direction, interview context, product SSOT,
  HR assessment requirements, two-day scope, confidentiality boundary, and
  final accountability for repository submission.
- AI-assisted work: requirement decomposition, code drafting, test-case
  generation, debugging, consistency review, and documentation drafting.
- Verification: deterministic tests and local runtime checks are required
  before AI-assisted output is accepted into the working tree.
- Runtime boundary: the core application does not need an API key. Optional
  AI-enhanced wording is user-selected, receives only a structured summary, and
  always falls back to deterministic output.

## Activity log

| Date | AI tool | Development task | AI contribution | Human review / modification | Verified result |
|---|---|---|---|---|---|
| 2026-08-24 | OpenAI Codex | Requirement decomposition | Converted the frozen product principles and HR brief into P0/P1 phases and a repository structure. | Candidate supplied the business context, selected the project, froze the SSOT, and required a two-day sprint. | Scope recorded in README and verification notes. |
| 2026-08-24 | OpenAI Codex | Data contract and synthetic data | Drafted typed fields, constraints, row-level validation, and 12 fictional partner records. | Confidential-data guardrail retained; public company statistics were not encoded as program constants. | Contract, duplicate, unknown-column, null, and range tests pass. |
| 2026-08-24 | OpenAI Codex | Policy and scoring engines | Drafted YAML policy inheritance, specificity resolution, normalization, pillar score, and confidence calculations. | Rules were kept deterministic and configurable; missing observations were excluded rather than converted to zero. | Policy and scoring boundary tests pass. |
| 2026-08-24 | OpenAI Codex | Governance logic | Drafted independent risk signals, critical gates, tiering, status, and human-reviewed Recommended Actions. | Automatic price, margin, rebate, credit, freeze, termination, and legal conclusions were explicitly rejected. | A high-score/critical-gate regression test passes. |
| 2026-08-24 | OpenAI Codex | Debugging and optimization | Detected and corrected lexicographic risk-severity ordering; added explicit ordinal ranking and a regression assertion. | Change accepted only after the portfolio test demonstrated `CRITICAL` correctly. | Full test suite passes. |
| 2026-08-24 | OpenAI Codex | UI and documentation | Drafted Executive Overview, Partner 360, data-quality views, README, data contract, and verification record. | UI remains a presentation layer; product rules stay in independently tested modules. | Streamlit headless startup and Python compilation pass. |
| 2026-08-25 | OpenAI Codex | Two-level policy configuration | Refactored configuration into canonical Pillar weights and independent Metric weights, with mathematical validation at both levels. | Candidate supplied the exact two-level product decision; automatic cross-level weight adjustment was rejected. | Weight-total and score-propagation tests pass. |
| 2026-08-25 | OpenAI Codex | Policy inheritance and lifecycle | Implemented explicit Country Override resolution, Draft/Active/Archived states, scenario-tested marker, activation isolation, and audit records. | Silent fallback and direct overwrite of Active Policy were rejected. | Country, isolation, archive, and audit tests pass. |
| 2026-08-25 | OpenAI Codex | Policy Studio and Scenario Lab | Built nested weight controls and three-scope baseline/draft comparison with tier migration and portfolio impact. | Scenario uses a temporary repository and cannot mutate Active Policy. | Streamlit HTTP smoke test and scenario safety tests pass. |
| 2026-08-25 | OpenAI Codex | Recommended Action | Replaced unstructured recommendation strings with typed action, priority, reason, evidence, and human-review fields. | Total-score-to-action mapping was rejected; Gate/Risk precedence was retained. | New-business, mature-business, financial-risk, and gate tests pass. |
| 2026-08-25 | OpenAI Codex | Management Insight design | Decomposed the explanation contract, drafted weighted driver ranking, deterministic narrative, severity order, and Partner 360 presentation. | Historical-change language was rejected because the current dataset has no time series; the engine states this limitation. | Gate, risk, confidence, driver, missing-evidence, and offline tests pass. |
| 2026-08-25 | OpenAI Codex | Optional provider and prompt design | Drafted a provider protocol, whitelist context, Responses API adapter, structured narrative schema, guardrail prompt, and exception fallback. | Raw rows and domain result objects were kept outside the provider boundary; AI can edit prose but not deterministic severity or ranked evidence. | Unavailable, timeout, immutability, and privacy tests pass without a live API call. |
| 2026-08-25 | OpenAI Codex | Target Rationale | Drafted configurable sanity-check thresholds, lifecycle-sensitive assessment, evidence confidence, UI, and boundary tests. | Automatic target setting and approval were rejected; low historical base is not treated as a negative for new business. | Four assessments, lifecycle, governance, and missing-data tests pass. |
| 2026-08-25 | OpenAI Codex | Tests, debugging, and code review | Ran focused and full regression tests; tightened the AI schema so only narrative fields are provider-editable. | Changes were accepted in focused commits only after regression checks. | 64 tests pass before fresh-clone verification. |

## AI suggestions or tempting shortcuts rejected

The following approaches were deliberately not used:

1. **Score → exact margin/rebate/credit.** This would turn decision support into
   an unjustified automatic commercial decision.
2. **AI-generated partner scores.** Scores must be deterministic, explainable,
   configurable, and auditable.
3. **Missing value → zero.** Unknown information must reduce confidence rather
   than create a false negative observation.
4. **Compliance risk hidden inside score.** A high-quality partner can still
   have a critical current risk and trigger a governance hold.
5. **Inventory “lower is better.”** Distributor stock supports local supply;
   the synthetic policy therefore uses an optimal band.
6. **Hard-coded public company scale figures.** Public figures provide context,
   not internal operating constants.
7. **Artificial line-count inflation.** The repository favors cohesive modules,
   test coverage, and explainability over reaching a number with dead code.
8. **Mandatory AI API integration.** The optional adapter is isolated; fresh
   clones and the full core product run without the dependency or a key.

## How generated work was checked

- Pydantic enforces the input contract.
- Pytest covers business invariants and end-to-end portfolio evaluation.
- Python compilation catches syntax/import issues.
- Streamlit is started headlessly as a runtime smoke test.
- Synthetic data and policy files are reviewed for confidentiality boundaries.
- The README is maintained against the actual repository structure and commands.

AI assistance accelerates implementation; it does not replace the candidate's
responsibility to understand, explain, test, and defend every submitted design.
