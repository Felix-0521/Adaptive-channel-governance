# Adaptive Channel Governance & Partner Scoring Platform

> 基于规则、数据与 AI 辅助诊断的全球渠道治理与经销商决策支持平台

[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-73%20passing-2E7D32)](tests/)
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

### 0. Partner Management

系统支持通过表单创建 Partner，或按照 `Upload → Validation → Preview → Confirm Import` 流程导入 CSV。Partner ID 自动生成，数据保存到本地 SQLite；Missing Fields、Invalid Values、Duplicate Partner 与 Data Quality Warning 会在确认前展示。

新 Partner 直接进入现有 Adaptive Policy 与 Governance Engine，不创建第二套评分逻辑。仅录入管理 Context 而尚未补充经营指标时，系统会降低 Confidence 并显示 `UNRATED`，不会伪造 Partner Score。当前依赖基线支持 CSV；Excel 可先另存为 CSV。

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

**流程化 Tab 顺序（业务流程：数据输入 → 分析 → 决策 → 模拟 → 审计）：**

1. **数据中心 · Data Center** — 下载模板、上传 Excel、数据校验、规范化、评估运行
2. **渠道总览 · Channel Overview** — Executive Dashboard，6 KPI，回答"渠道健康状态如何？"
3. **合作伙伴全景分析 · Partner 360** — 为什么这个 Partner 是这个结果？下一步应该做什么？
4. **策略配置中心 · Policy Studio** — Country Override、Two-level Weight、Draft → Activate
5. **策略模拟实验室 · Scenario Lab** — 三个 Scope 的 Baseline vs Scenario 对比
6. **审计日志 · Audit Log** — SQLite 持久化的 Policy 生命周期事件

历史 Tab（可通过侧栏访问）：
- **合作伙伴管理 · Partner Management** — 创建 Partner、CSV Validation/Preview/Import
- **数据质量 · Data Quality** — 缺失字段如何影响 Confidence

## 5 分钟演示流程

快速体验完整渠道治理分析流程：

**Minute 0-1 · Business Problem**
打开应用，直接进入 **Data Center**。页面说明：渠道管理面临数据分散、标准不一致、经验依赖等问题。本系统将渠道数据转化为可配置、可解释、可测试的治理决策。

**Minute 1-2 · Upload Partner Data**
点击 **模板下载** 下载 7 个 Excel 模板（或直接使用 Synthetic Portfolio）。点击 **数据上传与评估 → 运行数据验证**。系统展示 Import Summary：检测到合作伙伴数量、警告数（非阻塞）、错误数（阻塞）、数据质量分。

**Minute 2-3 · Partner Evaluation**
点击 **执行评估**。系统对每个 Partner 调用评分引擎：Metric Score × Weight → Pillar Score → Partner Score。同时计算 Confidence、Risk Severity、Gate Signal、Tier、Governance Status、Recommended Action。评估完成后展示评分分布直方图与风险分布饼图。

**Minute 3-4 · Partner 360 Deep Dive**
进入 **Partner 360**。选择任意 Partner，按固定阅读路径查看：
- 合作伙伴档案（谁）
- 评分总览（得了几分）
- 维度评分拆解（如何得出分数）
- 管理洞察（为什么是这个结果）
- 风险信号 + 管理建议（应该做什么）
- 目标合理性分析（拟议目标是否合理）

**Minute 4-5 · Policy Scenario & Management Insight**
进入 **Policy Studio** 修改权重（例：将 Financial Health 从 15% 调至 25%），保存为 Draft。进入 **Scenario Lab**，选择 Full Portfolio Scope，对比 Baseline vs Scenario。观察哪些 Partner 的 Tier 发生了变化，哪些 Partner 升级，哪些 Partner 降级。



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
  partner_management.py        Partner create/import validation workflow
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
| Python Product Code | ~2,700 LOC |
| Total Python + Tests | ~3,600 LOC |
| Python Files | 30+ |
| Automated Tests | **163 passed** |
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
