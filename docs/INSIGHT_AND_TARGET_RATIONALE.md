# Management Insight and Target Rationale

## Explanation flow

`generate_deterministic_insight` reads a validated PartnerRecord, its existing
EvaluationResult, and the resolved Policy. It does not call scoring or
governance engines. Gate, risk, confidence, largest weighted benchmark gap, and
largest weighted positive contribution are ranked in that order.

When AI-enhanced mode is selected, `build_management_context` creates a
whitelist-only summary. The provider can return four narrative fields. Severity,
ranked drivers, Score, Tier, Risk, Gate, and Recommended Action remain
deterministic. Any provider/configuration/network/validation error returns the
original rules-based insight.

## Target calculation definitions

- Required Growth = `(Proposed Target / Current Revenue - 1) × 100`.
- Pipeline Coverage Ratio = `Pipeline Value / Proposed Target`.
- Target vs Current Revenue = `Proposed Target / Current Revenue`.
- Target vs Sell-out Trend compares Required Growth with the available
  `sell_out_performance_pct - 100` proxy and is not represented as historical
  growth.
- Confidence is the sum of configured evidence-presence weights. Missingness
  lowers confidence and values are never replaced with zero.

Policy thresholds live in `config/scoring_rules.yaml`. Target Rationale returns
SUPPORTED, STRETCH, REVIEW_REQUIRED, or INSUFFICIENT_EVIDENCE. It never returns
a recommended target or an approval decision.
