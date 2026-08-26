from pathlib import Path
import re

# Presentation theme: preserve approved appearance while removing brand-specific naming.
theme = Path("src/channel_governance/ui_theme.py")
text = theme.read_text(encoding="utf-8")
text = text.replace(
    "The theme translates Xiaomi / HyperOS-inspired principles such as\nclear hierarchy, comfortable spacing, restrained surfaces and a small\norange accent into an enterprise dashboard. It changes presentation\nonly and never touches governance or scoring behavior.",
    "The theme provides a clean, restrained enterprise visual system with\nclear hierarchy, comfortable spacing, neutral surfaces and a focused accent.\nIt changes presentation only and never touches governance or scoring behavior.",
)
text = text.replace('"MiSans", "Inter", "SF Pro Display", "Segoe UI",', '"Inter", "SF Pro Display", "Segoe UI",')
for old, new in {
    "--mi-bg": "--ui-bg",
    "--mi-surface": "--ui-surface",
    "--mi-soft": "--ui-soft",
    "--mi-text-2": "--ui-text-2",
    "--mi-text": "--ui-text",
    "--mi-muted": "--ui-muted",
    "--mi-line": "--ui-line",
    "--mi-accent": "--ui-accent",
    "--mi-radius-xl": "--ui-radius-xl",
    "--mi-radius-lg": "--ui-radius-lg",
    "--mi-radius-md": "--ui-radius-md",
}.items():
    text = text.replace(old, new)
theme.write_text(text, encoding="utf-8")

# README: synchronize test count and final Active Dataset flow.
readme = Path("README.md")
text = readme.read_text(encoding="utf-8")
text = text.replace("tests-164%20passing", "tests-166%20passing")
text = text.replace("| Automated Tests | **164 passed** |", "| Automated Tests | **166 passed** |")
text = text.replace(
    "1. **数据中心 · Data Center** — 下载模板、上传 Excel、数据校验、规范化、评估运行",
    "1. **数据中心 · Data Center** — 唯一数据入口；下载模板、上传验证、显式加载 Demo、确认 Active Dataset",
)
text = text.replace(
    '2. **渠道总览 · Channel Overview** — Executive Dashboard，6 KPI，回答"渠道健康状态如何？"',
    "2. **渠道总览 · Channel Overview** — 仅基于当前 Active Dataset 的 Executive Dashboard，回答“渠道健康状态如何？”",
)
text = text.replace(
    "3. **合作伙伴全景分析 · Partner 360** — 为什么这个 Partner 是这个结果？下一步应该做什么？",
    "3. **合作伙伴全景分析 · Partner 360** — 基于同一 Active Dataset 解释“为什么是这个结果、下一步做什么？”",
)
demo = """## 5 分钟演示流程

快速体验完整渠道治理分析流程：

**Minute 0–1 · Data Center / Empty State**  
应用首次启动时 `Active Dataset = None`。Channel Overview、Partner 360 与 Scenario Lab 不会自动展示任何 Partner 数据；Policy Studio 仍可独立配置治理规则。这个设计确保 Demo 数据和用户数据不会被混淆。

**Minute 1–2 · Load Demo or Upload Business Data**  
在 **Data Center** 二选一：
- 点击 **Load Demo Dataset**，显式加载 50 个 Synthetic Partners；或
- 上传标准 Excel/CSV 模板，运行 Validation，检查 Blocking Error / Warning / Data Quality，并预览待确认数据。

上传数据只有在点击 **Confirm Active Dataset** 后，才会成为全系统统一数据源。

**Minute 2–3 · Channel Overview**  
进入 **Channel Overview**，查看当前 Active Dataset 的 Partner 总数、Strategic Partner、High/Critical Risk、Review Required、Active Governance 与 Recommended Action 等管理信号，并结合治理状态、Partner Score、Tier、Risk 与 Lifecycle 分布判断渠道健康度。

**Minute 3–4 · Partner 360**  
选择一个 Partner，沿固定阅读路径查看：Partner Profile → Score / Confidence / Tier / Risk / Governance Status → Pillar Breakdown → Management Insight → Risk & Recommended Action → Target Rationale。所有核心评价均来自 deterministic rule engine，AI 仅作为可选解释层。

**Minute 4–5 · Policy Studio + Scenario Lab**  
在 **Policy Studio** 调整 Pillar / Metric 权重并保存 Draft；进入 **Scenario Lab** 用 Single Partner、Selected Market 或 Full Portfolio 比较 Baseline vs Scenario。Draft 不会直接改写 Active Policy，必须经过 Scenario Test 与显式 Activate。

> 推荐面试演示路径：**先展示 Empty State → Load Demo Dataset → Channel Overview → Partner 360 → Policy Studio / Scenario Lab**。这样最能体现系统的数据边界、治理逻辑和产品完整性。

"""
text, count = re.subn(
    r"## 5 分钟演示流程\n.*?\nPython 3\.12 是标准运行环境。",
    demo + "Python 3.12 是标准运行环境。",
    text,
    count=1,
    flags=re.S,
)
if count != 1:
    raise RuntimeError("README demo section anchor missing")
anchor = "核心业务逻辑与 Streamlit UI 分离，可独立测试。SQLite 是本地运行状态，不包含真实商业数据。"
if "Refined Enterprise UI" not in text:
    text = text.replace(
        anchor,
        anchor + "\n\n展示层采用 **Refined Enterprise UI**：统一字号、边距、卡片、按钮、Tab、表格与空状态规范；视觉样式与业务引擎解耦，不影响 Score / Risk / Gate / Policy 计算。",
        1,
    )
readme.write_text(text, encoding="utf-8")

# Final demo guide.
Path("docs/FINAL_DEMO_GUIDE.md").write_text("""# 5-Minute Demo Guide

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
""", encoding="utf-8")

Path("docs/FINAL_RELEASE_REPORT.md").write_text("""# Final Release Report

> **Adaptive Channel Governance & Partner Scoring Platform**  
> Final Interview Release — 2026-08-26

## 1. Release Status

**Status: FINAL CANDIDATE — READY FOR INTERVIEW SUBMISSION**

The product flow, refined enterprise presentation layer, active-dataset architecture, synthetic demo package, and submission documentation are complete.

## 2. Final Product Flow

```text
Business Data / Explicit Demo Load
→ Validation & Normalization
→ Confirm Active Dataset
→ Adaptive Policy Resolution
→ Partner Score + Confidence
→ Independent Risk + Gate
→ Tier + Governance Status
→ Recommended Action
→ Management Insight / Target Rationale
```

The application starts with **no Active Dataset**. Demo data is loaded only through an explicit user action. Uploaded data becomes the shared source for Channel Overview, Partner 360 and Scenario Lab only after validation and confirmation.

Policy Studio remains available before partner data is loaded because governance rules logically precede evaluation.

## 3. Final Capability Scope

- Data Center as the single dataset gateway
- Explicit 50-partner Synthetic Demo Dataset load
- 7 Excel templates with upload, validation, normalization and preview
- Adaptive Policy with lifecycle / market / partner context and Country Override
- Two-level Pillar / Metric weighting
- Deterministic Partner Score and Confidence
- Independent Risk and Gate evaluation
- Governance Status and human-reviewed Recommended Action
- Channel Overview and Partner 360 driven by one Active Dataset
- Scenario Lab with Single Partner / Selected Market / Full Portfolio scope
- Policy Draft → Scenario Test → Activate lifecycle
- SQLite persistence and Audit Log
- Rules-based Management Insight with optional AI-enhanced wording
- Target Rationale decision-support check
- Refined Enterprise UI presentation system

## 4. Architecture and Safety Boundary

Core domain logic remains separated from the Streamlit presentation layer. The final UI/data-flow pass does **not** modify `scoring.py`, `governance.py`, `policy.py`, or `evaluation.py`.

AI remains optional and explanatory. It never determines Score, Tier, Risk, Gate, credit, margin, rebate, channel termination, legal conclusions, or final sales targets.

All repository business data is synthetic.

## 5. Final Verification

- Automated regression suite: **166 passed**
- Python compilation: passed
- Streamlit headless startup / health check: passed
- Browser-style Excel normalization: passed
- Explicit Demo Dataset test: 50 Partners after user click
- Empty-state test: no automatic partner portfolio before data activation
- Core scoring / governance / policy / evaluation modules unchanged by final presentation/data-gateway pass

## 6. Known Limitations

- Local prototype; no authentication or role-based access
- SQLite is suitable for this prototype, not a production multi-user deployment
- No live CRM / ERP integration
- Optional AI insight requires an API key; deterministic core does not
- Not presented as a production-ready enterprise deployment

## 7. Run

```bash
git clone https://github.com/Felix-0521/Adaptive-channel-governance.git
cd Adaptive-channel-governance
python -m venv .venv
python -m pip install -r requirements.txt
python -m pytest
python -m streamlit run app.py
```
""", encoding="utf-8")

Path("docs/FINAL_SUBMISSION_VERIFICATION.md").write_text("""# Final Submission Verification

Date: 2026-08-26  
Scope: final interview candidate

## Verified

- Clean GitHub Actions runner using Python 3.12
- Dependencies installed from `requirements.txt`, including `openpyxl`
- Full automated regression suite: **166 passed**
- `python -m compileall -q app.py src`: passed
- Streamlit headless startup and `/_stcore/health`: passed
- Browser-style Excel bytes normalize correctly through the business-data pipeline
- Explicit Synthetic Demo Dataset load produces the 50-partner portfolio
- Application starts without silently loading partner data
- Channel Overview, Partner 360 and Scenario Lab require an Active Dataset
- Policy Studio remains usable before partner data is loaded

## Final Product Guardrails

- Synthetic data only
- One explicit Active Dataset drives analysis views
- Missing data is not converted to zero
- Risk remains independent from Partner Score
- Gate signals take precedence over score-based recommendations
- Core scoring / governance / policy / evaluation modules are unchanged by the final UI/data-flow pass
- AI remains optional and explanatory; deterministic core requires no API key
- Refined Enterprise UI is presentation-only and does not alter business calculations
""", encoding="utf-8")

# AI usage record: add final productization activity.
ai = Path("AI_USAGE.md")
text = ai.read_text(encoding="utf-8")
row = "| 2026-08-26 | OpenAI Codex | Active Dataset and final UI productization | Identified startup demo-data leakage, inconsistent dataset sources, a RecommendedAction rendering bug, and Streamlit icon-font collision; drafted a single Active Dataset gateway, explicit demo loading, empty states, refined enterprise visual rules, regression tests, and release documentation. | Candidate discovered the issues through hands-on browser testing, approved the final business flow and presentation, and required brand-neutral naming. Core scoring/governance/policy/evaluation modules were intentionally left unchanged. | 166 tests pass; Python compile and Streamlit health checks pass; explicit-demo and empty-state regressions pass. |\n"
anchor = "\n## AI suggestions or tempting shortcuts rejected\n"
if row not in text:
    text = text.replace(anchor, "\n" + row + anchor, 1)
ai.write_text(text, encoding="utf-8")
