# 5-Minute Demo Guide

> **Adaptive Channel Governance & Partner Scoring Platform**  
> Final interview walkthrough for a rule-driven, data-driven, AI-assisted channel governance prototype.

## Prerequisites

```bash
git clone https://github.com/Felix-0521/Adaptive-channel-governance.git
cd Adaptive-channel-governance
python -m venv .venv
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open the Streamlit local URL. **No AI API key is required for core functionality.**

## Minute 0–1 · Start with the Data Boundary

Open **数据中心 · Data Center**. The application starts with `Active Dataset = None`.

Before data is loaded, Channel Overview, Partner 360 and Scenario Lab show explicit empty states. Policy Studio remains usable because governance rules exist before partner evaluation.

Key message: **the system never silently mixes demo data with uploaded business data.**

## Minute 1–2 · Load Demo or Upload Business Data

For a fast interview demo, click **加载演示数据 · Load Demo Dataset**. This explicitly loads the 50-partner synthetic portfolio and makes it the single Active Dataset.

For the business workflow:

```text
Download Templates → Fill Data → Upload → Validation → Preview → Confirm Active Dataset
```

Warnings are non-blocking and may lower confidence. Blocking errors must be corrected. Uploaded data does not affect analysis tabs until **Confirm Active Dataset** is clicked.

## Minute 2–3 · Channel Overview

Use **渠道总览 · Channel Overview** to explain Partner count, Strategic Partners, High/Critical Risk, Review Required, Active Governance, Governance Status distribution, Partner Score, Tier, Risk and Lifecycle distributions.

Key message: **Score, Risk and Governance Status are related but not interchangeable.**

## Minute 3–4 · Partner 360

Open **合作伙伴全景分析 · Partner 360** and follow the reading path:

1. Partner Profile and applied Policy Source
2. Partner Score / Confidence / Tier / Risk / Governance Status
3. Six-pillar score breakdown
4. Management Insight
5. Risk signals and Recommended Actions
6. Target Rationale

Key message: **NULL ≠ 0; missing evidence lowers confidence rather than fabricating a poor score.**

## Minute 4–5 · Policy Studio and Scenario Lab

In **策略配置中心 · Policy Studio**, select the policy context, adjust Level 1 Pillar Weights or Level 2 Metric Weights, and save as Draft.

In **策略模拟实验室 · Scenario Lab**, run Single Partner, Selected Market, or Full Portfolio scope and compare Baseline vs Scenario.

Key message: **Draft policy changes are tested before activation; the live evaluation logic is never silently overwritten.**

## Core Talking Points

| Principle | What the product demonstrates |
|---|---|
| Rule-driven, not AI-driven | Score, Risk, Gate and Tier are deterministic |
| Business context before evaluation | Different lifecycle / market contexts can use different policies |
| Risk ≠ Score | A high-score partner can still require REVIEW or HOLD |
| Gate > Score | Critical governance signals override growth recommendations |
| NULL ≠ 0 | Missing evidence lowers confidence |
| One Active Dataset | Demo and uploaded data never coexist ambiguously |
| Human-in-the-loop | Recommended Action remains decision support |
| AI as explanation layer | Optional AI explains structured results but never sets commercial decisions |

## Recommended Interview Story

> “我不是在做一个更复杂的 Excel 评分表，而是在把渠道管理里的经验判断拆成 Context、Policy、Score、Risk、Gate 和 Action。数据先通过统一入口进入系统，规则先于评价，风险独立于分数，AI 只负责解释。这样 Sales Platform 才能真正做到可配置、可测试、可追溯，而不是替销售拍脑袋做决定。”
