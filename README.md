# Adaptive Channel Governance & Partner Scoring Platform

> 基于规则、数据与 AI 辅助诊断的全球渠道治理与经销商决策支持平台

[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-66%20passing-2E7D32)](tests/)
[![Fresh Clone](https://img.shields.io/badge/fresh--clone-passed-2E7D32)](docs/FINAL_BUILD_REPORT.md)
[![Data](https://img.shields.io/badge/data-synthetic%20only-555555)](data/sample_partners.csv)

**Adaptive Channel Governance & Partner Scoring Platform 是一个可运行的 Sales Operations 决策支持系统原型，通过 Adaptive Policy、Partner Score、Risk、Gate、Scenario Simulation 与 Management Insight，帮助管理者对不同业务阶段和市场环境下的渠道伙伴进行差异化治理。**

> **Synthetic Data 声明：本仓库中的 Partner、Distributor、销售、库存、授信、评分参数和 Policy 数据均为 Synthetic Data，仅用于项目演示，不包含任何公司的真实商业数据。**
> All datasets and commercial parameters in this repository are synthetic and created solely for demonstration purposes.

本项目是一个 independently designed software prototype，不是任何公司的 Official System、Production System、Internal Tool 或真实 Distributor Deployment。

## 项目背景

全球渠道管理面对的问题不只是“哪个 Distributor 销售额最高”。不同的 Business Line、Country、Market Tier、Lifecycle Stage 和 Partner Type，需要不同的治理重点。

传统统一评分容易忽略：

- 新业务与成熟业务的评价差异；
- Sell-in、Sell-out 与 Inventory 健康度之间的关系；
- Financial Risk、Technical Capability 与 Compliance；
- 不同国家与市场的战略价值；
- 高 Partner Score 与当前重大 Risk 可能同时存在。

本项目把渠道管理经验转化为**可配置、可解释、可测试、可追溯**的系统规则，形成完整链路：

```text
Data → Adaptive Policy → Partner Score → Risk / Gate
     → Governance Status → Recommended Action
     → Management Insight / Target Rationale
```

## 核心设计理念

- **Rule-driven, not AI-driven**：核心判断由透明规则完成，AI 不参与评分。
- **Explainable, not black-box**：每个 Score、Risk、Gate 和 Action 都能追溯到输入与 Policy。
- **Configurable, not hard-coded**：两层权重和目标判断阈值来自版本化配置。
- **Decision support, not automatic decision making**：不自动决定价格、返点、授信、冻结、终止或销售目标。
- **Human-in-the-loop**：所有 Recommended Action 与管理结论都要求人工复核。

## 核心产品能力

### 1. Adaptive Policy

系统不会让所有 Distributor 使用同一套评分标准。Policy Context 由以下维度组成：

```text
Business Line × Lifecycle Stage × Market Tier × Partner Type × Country Override
```

规则解析顺序为：

```text
Country Override → Exact Context → Business + Lifecycle → Lifecycle → Global Default
```

Partner 360 和 Policy Studio 会显示最终采用的 Policy Source，避免静默继承。

### 2. Two-level Weight Configuration

这是项目最核心的差异化能力之一。

Level 1 — **Pillar Weight**：

```text
Operational Health = 25%
Financial Health   = 15%
```

Level 2 — **Metric Weight**：

```text
Operational Health
├── Inventory Health       40%
├── Sell-out Performance   35%
├── Forecast Accuracy      15%
└── Reporting Quality      10%
```

管理者不仅可以调整六大评价维度，还可以继续深入调整维度内部指标，从而实现更加精细的 Channel Governance。Pillar Weight 与 Metric Weight 分别校验 100%，互不自动修改。

### 3. Country Override 与 Policy Lifecycle

市场默认继承上级 Policy；特定国家需要差异化时，可通过 Country Override 覆盖规则。

```text
Active Policy → Draft → Scenario Test → Activate → Previous Version Archived
```

修改权重不会立即影响正式评价结果。Draft 必须经过 Scenario Test 才能 Activate；Policy 版本、状态、权重、Scenario Tested 状态和 Audit Log 均保存到本地 SQLite。

### 4. Partner Score 与 Confidence

```text
Metric Score × Metric Weight → Pillar Score
Pillar Score × Pillar Weight → Partner Score
```

Partner Score 是 deterministic / explainable calculation，不由 AI 生成。

```text
NULL ≠ 0
```

数据缺失会降低 Confidence，而不是被自动当作零分，因此系统能够区分“表现差”和“证据不足”。

### 5. Risk、Gate 与 Governance Status

```text
Risk ≠ Score
Gate > Score-based Recommendation
```

因此以下结果完全可能同时成立：

```text
Partner Score:      89
Partner Tier:       STRATEGIC
Risk:               CRITICAL
Governance Status:  HOLD
```

Risk 独立于 Partner Score；Critical Gate 会优先触发人工治理 Review，阻止系统仅凭高分给出增长建议。

### 6. Recommended Action

Recommended Action 回答“评价完成后，管理层下一步应该重点关注什么？”输出包含 Priority、Reason、Evidence 与 Human Review Required。

```text
ENGINEER_SUPPORT       DEMO_SUPPORT
NEW_PRODUCT_ENABLEMENT BRANDING_MDF
CHANNEL_EXPANSION      INVENTORY_OPTIMIZATION
CREDIT_REVIEW          COMPLIANCE_REVIEW
```

Action 不是 Partner Score 的简单映射。Gate 与 High Risk 优先于增长支持。

### 7. Scenario Lab

支持 `Single Partner`、`Selected Market` 和 `Full Portfolio` 三个 Scope。在不修改 Active Policy 的情况下比较 **Baseline vs Scenario**，输出 Score Change、Tier Migration、Portfolio Impact、Upgraded Partners 和 Downgraded Partners。

### 8. Management Insight

- **Rules-based / Deterministic Insight**：默认模式，完全离线，无需 API；
- **AI-enhanced Insight**：可选，仅对结构化管理摘要进行解释和改写。

AI 只允许 Explain、Summarize、Highlight、Compare；不参与 Score、Risk、Partner Tier、Gate 或最终商业决策。Raw Data、DataFrame 和 CSV 不会发送给 AI Provider，任何 AI 错误都会自动 fallback 到 Deterministic Insight。

### 9. Target Rationale / Target Sanity Check

系统不会自动制定或批准销售目标，而是回答：

> Proposed Target 是否具有足够业务依据？

```text
SUPPORTED | STRETCH | REVIEW_REQUIRED | INSUFFICIENT_EVIDENCE
```

ENTRY/BUILD/EMERGING 更关注 Pipeline、First Customer、Market Capability 与 Coverage；MATURE/DECLINE 更关注 Historical Growth、Sell-out、Inventory 与 Financial Risk。

## Synthetic Data 业务示例

### Case A — Mature Agriculture Partner

```text
Business Line: AGRICULTURE
Lifecycle Stage: MATURE
Market Tier: HIGH_VALUE
```

假设该 Partner 的 Revenue、Inventory 与 Financial Health 稳健，但 New Product Penetration 偏低，系统可以在 CORE / STRATEGIC Tier 下给出：

```text
NEW_PRODUCT_ENABLEMENT — HIGH
```

### Case B — Emerging Surveying Partner

该 Partner 当前 Revenue 不高，但 Technical Capability 强、Market Coverage 较低。系统不会简单因规模较小而判定失败，而可能给出：

```text
CHANNEL_EXPANSION — HIGH
DEMO_SUPPORT      — HIGH
```

相同销售额在不同 Lifecycle Stage 中代表不同业务含义，这正是 Adaptive 的核心。

## 产品界面

- **Executive Overview**：Partner 数量、平均分、高风险、Review Worklist，以及 Tier/Risk/Lifecycle 分布；
- **Partner 360**：Context → Score/Confidence/Tier/Risk/Status → Pillar → Insight → Action → Target；
- **Policy Studio**：Country Override、Pillar Weight、可展开 Metric Weight 和 Draft/Activate；
- **Scenario Lab**：三个 Scope 的 Baseline vs Scenario；
- **Data Quality**：显示缺失字段如何影响 Confidence；
- **Audit Log**：显示 SQLite 持久化的 Policy 生命周期事件。

## 5 分钟本地运行

Python 3.12 是标准运行环境。

```bash
git clone https://github.com/Felix-0521/Adaptive-channel-governance.git
cd Adaptive-channel-governance
python -m venv .venv
```

Windows PowerShell：

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pytest
python -m streamlit run app.py
```

macOS / Linux：

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest
python -m streamlit run app.py
```

打开 Streamlit 输出的本地网址即可。首次启动会自动创建 `data/app.db`，无需手工执行 SQL。

> **Core functionality does not require an AI API key.**

### Optional AI Configuration

AI-enhanced Insight 默认关闭。需要体验时先执行：

```bash
pip install -r requirements-ai.txt
```

然后在本地环境变量中设置，禁止把真实 Key 提交到 Git：

```text
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-5-mini
```

未配置 Key、依赖或网络时，应用会自动使用 Rules-based Insight。

## 技术架构

```text
app.py                         Streamlit presentation layer
config/scoring_rules.yaml      Adaptive Policy configuration
data/sample_partners.csv       Synthetic Data
data/app.db                    Local SQLite runtime state（自动创建，不提交）
src/channel_governance/
  models.py                    Pydantic contracts
  validation.py                Data validation boundary
  policy.py                    Resolution, lifecycle, persistence hooks
  scoring.py                   Metric/Pillar Score and Confidence
  governance.py                Risk, Gate, Tier, Status, Action
  evaluation.py                Application orchestration
  scenario.py                  Baseline vs Scenario
  insight.py                   Deterministic Management Insight
  insight_providers.py         Optional AI provider and fallback
  target_rationale.py          Target Sanity Check
  storage.py                   SQLite Policy/Audit persistence
tests/                         Pytest unit and integration tests
```

核心业务逻辑与 Streamlit UI 分离，可独立测试。SQLite 是本地运行状态，不包含真实商业数据。

## 工程质量与验证

| 指标 | 最终结果 |
|---|---:|
| Python Product Code | 2,245 LOC |
| Total Python + Tests | 3,085 LOC |
| Python Files | 29 |
| Automated Tests | 66 passed |
| Fresh-clone Validation | Passed |
| Streamlit Startup Check | Passed |
| Core AI API Requirement | None |

测试覆盖 Adaptive Policy、两层权重、Country Override、Policy Lifecycle、SQLite restart persistence、Scenario isolation、Score、Confidence、Risk、Gate、Recommended Action、Management Insight、AI fallback/privacy、Target Rationale、Synthetic portfolio 与 Streamlit 执行。

详细验证结果见 [FINAL_BUILD_REPORT.md](docs/FINAL_BUILD_REPORT.md)。

## AI-assisted Development

AI 在本项目中实际参与了 Requirement Decomposition、Architecture Discussion、Code Generation Assistance、Debugging、Test Case Design 与 Documentation Optimization。

所有核心业务规则、产品边界与最终判断均由开发者确认，AI-generated code 经过自动化测试和人工验证后才进入项目。完整过程、保留的边界和拒绝的捷径见 [AI_USAGE.md](AI_USAGE.md)。

## 产品边界与已知限制

- 仅使用 Synthetic Data，不连接真实 CRM / ERP；
- 无 Authentication、Role Permission、Email 或 Approval Workflow；
- SQLite 适合本地原型，不代表生产级多用户数据库；
- AI-enhanced Insight 是可选解释层，不是业务决策引擎；
- Target Rationale 是 evidence sanity check，不是自动目标制定或审批；
- 本项目不声称 production-ready enterprise deployment。

项目的目标是展示：如何把复杂渠道治理问题转化为一个可运行、可解释、可测试、可审计并能在面试中清晰演示的软件原型。
