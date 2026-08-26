# 5-Minute Demo Guide

> **Adaptive Channel Governance & Partner Scoring Platform**  
> A walkthrough for interviewers, stakeholders, and reviewers.

---

## Prerequisites

```bash
git clone https://github.com/Felix-0521/Adaptive-channel-governance.git
cd Adaptive-channel-governance
python -m venv .venv
.\.venv\Scripts\Activate.ps1          # Windows
# source .venv/bin/activate            # macOS/Linux
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open the URL printed by Streamlit (usually `http://localhost:8501`).

> **No AI API key required.** The core application runs fully offline.

---

## Minute 0–1 · Business Problem

**Tab: 数据中心 · Data Center**

The opening screen explains the core problem:

- Channel data is scattered across systems
- Evaluation standards are inconsistent
- Decisions rely on individual experience

This platform transforms channel governance from an art into a **configurable, explainable, testable, and auditable** system.

Click **模板下载 · Download Templates** to see the 7 Excel templates:
Partner Master, Commercial Performance, Operational Health, Financial Health,
Service Capability, Compliance Governance, and Target Rationale.

---

## Minute 1–2 · Upload Partner Data

**Tab: 数据中心 · Data Center**

1. Click **数据上传与评估 · Upload & Evaluate**
2. Click **运行数据验证 · Run Validation** (optionally upload your own Excel files — or skip to use the built-in Synthetic Portfolio of 50 partners)
3. Review the **Import Summary**:
   - Partners Detected
   - Warnings (non-blocking — evaluation continues)
   - Errors (blocking — must be corrected)
   - Data Quality Score

The system distinguishes **warnings from errors**. A warning means "data quality is reduced but we can still evaluate." An error means "this record cannot be evaluated."

---

## Minute 2–3 · Partner Evaluation

**Tab: 数据中心 · Data Center**

Click **执行评估 · Run Evaluation**. The system evaluates all partners:

- Metric Score × Metric Weight → Pillar Score
- Pillar Score × Pillar Weight → Partner Score
- Confidence (null ≠ 0: missing data lowers confidence, not score)
- Risk Engine (independent from score)
- Gate Engine (overrides score-based recommendations)
- Tier Classification (UNRATED / DEVELOPMENT / CORE / STRATEGIC)
- Governance Status (ACTIVE / MONITOR / REVIEW / HOLD)
- Recommended Actions (prioritized, with human review flags)

After evaluation, view the **Score Distribution** histogram and **Risk Distribution** pie chart.

---

## Minute 3–4 · Partner 360 Deep Dive

**Tab: 合作伙伴全景分析 · Partner 360**

Select any partner. Follow the structured reading path:

### 1. Partner Profile
Who is this partner? Business line, country, lifecycle stage, market tier, and which policy is being applied.

### 2. Score Overview
Five headline numbers: Partner Score, Confidence, Tier, Risk Level, Governance Status.

### 3. Pillar Breakdown
A bar chart showing how the overall score is built from the six governance pillars:
Operational Health, Financial Health, Market Capability, Service Capability, Compliance, and Growth Potential.

### 4. Management Insight
**Executive Summary**: why the partner received this score.
**Key Drivers**: which specific metrics drove the score up or down, with benchmarks.
**Recommended Next Step**: what the management team should focus on.

### 5. Risk & Action
Risk signals (with severity icons) and recommended actions (with evidence and human-review flags).

### 6. Target Rationale
Is the proposed sales target realistic? The system performs a sanity check based on historical growth, pipeline, lifecycle stage, and resource commitment.

---

## Minute 4–5 · Policy Scenario & Management Insight

**Tab: 策略配置中心 · Policy Studio**

1. Select a policy context (e.g., AGRICULTURE · MATURE · HIGH_VALUE · DISTRIBUTOR · PL)
2. Adjust **Level 1 Pillar Weights**: for example, increase Financial Health from 15% to 25%
3. Save as **Draft**
4. Note: Draft does not affect evaluation until activated

**Tab: 策略模拟实验室 · Scenario Lab**

1. Choose **Full Portfolio** scope
2. Run the Scenario against the Draft
3. Compare **Baseline vs Scenario**:
   - Which partners' scores changed
   - Which partners changed tier (upgraded / downgraded)
   - Portfolio-level impact summary

This demonstrates the core value: **"What if we cared more about financial health?"** — answered quantitatively, without touching the live policy.

---

## Demo Scenarios for Interviewers

### Scenario A — High Score, High Risk
Show PT00006 (PT00006: High Revenue, 165 inventory days, REVIEW status, HIGH risk).
The audience will ask: "Why is a high-revenue partner in REVIEW?"
Answer: Risk is independent from score. Inventory risk triggers a governance review regardless of revenue.

### Scenario B — Unrated Partner
Show PT00024 (null revenue, null metrics, UNRATED, HOLD).
The audience will ask: "Why does this partner have no score?"
Answer: Missing data means unknown, never zero. The system correctly refuses to generate a score when data is insufficient.

### Scenario C — Policy Impact
Show the same partner's score under two different policy contexts (e.g., AGRICULTURE/MATURE vs. SURVEYING/ENTRY).
Demonstrate that the platform applies different weights for different business realities.

---

## Key Takeaways

| Concept | Demonstration |
|---|---|
| Adaptive Policy | Different weights for different partner contexts |
| Score ≠ Risk | High score + critical risk is possible and handled |
| NULL ≠ 0 | Missing data ≠ bad performance |
| Gate > Score | Compliance review blocks growth recommendations |
| Explainable | Every score traces back to specific metrics and weights |
| No AI required | Core functionality is fully deterministic |
