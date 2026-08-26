# Adaptive Channel Governance & Partner Scoring Platform

> 一个把渠道管理规则、伙伴评价、风险判断和 AI 辅助解释串成完整流程的决策支持原型。

[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-166%20passing-2E7D32)](tests/)
[![Fresh Clone](https://img.shields.io/badge/fresh--clone-passed-2E7D32)](docs/FINAL_SUBMISSION_VERIFICATION.md)
[![Data](https://img.shields.io/badge/data-synthetic%20only-555555)](data/sample_partners.csv)

## 30 秒看懂这个项目

我想解决的不是“做一个更复杂的渠道评分表”，而是一个更实际的问题：

**当业务线、市场阶段和经销商情况都不一样时，Sales Platform 应该如何用一套可解释、可调整、可验证的规则去做渠道治理？**

这个原型把渠道管理拆成一条清晰的链路：

```text
业务数据
→ 适用规则（Adaptive Policy）
→ Partner Score + Confidence
→ Risk + Gate
→ Tier + Governance Status
→ Recommended Action
→ Management Insight / Target Rationale
```

它的核心不是让 AI 替管理者做决定，而是把原本依赖经验的判断变成**有规则、有证据、能解释、能测试**的管理流程。

| 项目 | 说明 |
|---|---|
| 产品形态 | 可运行的 Streamlit Web App 原型 |
| 主要用户 | Sales Platform / Sales Operations / Channel Management |
| 数据入口 | Data Center，支持标准 Excel/CSV 模板 |
| Demo 数据 | 50 个完全虚构的 Synthetic Partners |
| 核心判断 | 规则驱动，不由 AI 打分 |
| AI 的角色 | 可选的解释与总结层 |
| 自动化测试 | 166 tests passed |
| 数据安全 | 仓库不包含真实公司或客户业务数据 |

## 为什么做这个项目

渠道管理里有一个很常见的矛盾：大家都希望“有统一标准”，但真正落到业务上，又不能用同一把尺子评价所有伙伴。

例如：

- 新业务收入暂时不高，不代表没有潜力；
- 成熟业务销售额很高，但库存或应收风险可能已经需要治理；
- 某些国家需要不同的渠道规则；
- 数据缺失和表现差不是一回事；
- 高分伙伴也可能同时存在严重风险。

所以这个项目先判断 **Business Context**，再决定“应该用什么规则评价”，而不是先给所有 Partner 套同一套分数。

## 我最看重的 5 个设计原则

1. **Rule-driven, not AI-driven**  
   Score、Risk、Gate、Tier 都来自明确规则。AI 不参与评分。

2. **Business context before evaluation**  
   Business Line、Lifecycle Stage、Market Tier、Partner Type 和 Country Override 会影响适用 Policy。

3. **Risk ≠ Score**  
   一个销售表现很好的 Partner，也可能因为库存、财务或合规问题进入 REVIEW / HOLD。

4. **NULL ≠ 0**  
   缺数据代表“证据不足”，不会被系统直接当成“表现为零”。缺失数据会降低 Confidence。

5. **Decision support, not automatic decision making**  
   系统给出 Recommended Action 和分析依据，但不会自动决定价格、返点、授信、终止合作或最终销售目标。

## 产品怎么用

### 1. Data Center：先把数据边界说清楚

应用首次启动时：

```text
Active Dataset = None
```

系统不会偷偷加载 Demo 数据。

用户可以选择：

```text
A. Load Demo Dataset
   → 显式加载 50 个 Synthetic Partners

B. Upload Business Data
   → 下载标准模板
   → 填写并上传
   → Validation
   → Preview
   → Confirm Active Dataset
```

只有被确认的数据集，才会统一驱动 Channel Overview、Partner 360 和 Scenario Lab。

### 2. Channel Overview：先看整体渠道健康度

Dashboard 用来回答几个管理层最关心的问题：

- 现在有多少 Partner？
- 哪些 Partner 是 Strategic？
- 哪些存在 High / Critical Risk？
- 哪些需要 Review？
- Score、Tier、Risk、Governance Status 的整体分布是什么样？

### 3. Partner 360：解释“为什么”

选择一个 Partner 后，可以按固定顺序往下看：

```text
Partner Profile
→ Applied Policy
→ Score / Confidence / Tier / Risk / Governance Status
→ Pillar Breakdown
→ Management Insight
→ Risk & Recommended Action
→ Target Rationale
```

重点不是只告诉用户“这个 Partner 得了多少分”，而是让结果可以追溯到具体指标、权重和风险信号。

### 4. Policy Studio：规则可以调整，但不能随便生效

Policy Context：

```text
Business Line
× Lifecycle Stage
× Market Tier
× Partner Type
× optional Country Override
```

系统支持两层权重：

```text
Level 1: Pillar Weight
Level 2: Metric Weight
```

修改规则不会直接覆盖正式 Policy，而是经过：

```text
Active Policy
→ Draft
→ Scenario Test
→ Activate
→ Previous Version Archived
```

### 5. Scenario Lab：先模拟，再决定是否启用

支持三种范围：

```text
Single Partner
Selected Market
Full Portfolio
```

用户可以比较 Baseline vs Scenario，看 Score Change、Tier Migration 和 Portfolio Impact，而不影响当前 Active Policy。

### 6. Management Insight：AI 是解释层，不是裁判

默认使用离线的 Rules-based Insight，不需要 API Key。

可选 AI-enhanced Insight 只接收结构化摘要，用来：

- 解释；
- 总结；
- 突出重点；
- 比较结果。

AI 不会修改 Score、Risk、Gate、Tier，也不会生成最终商业决策。AI 不可用时，系统自动回退到 deterministic output。

## 一个简单例子

假设某个 Partner：

```text
Revenue: 很高
Partner Score: 89
Tier: STRATEGIC
Inventory Days: 过高
Risk: CRITICAL
```

系统可以同时给出：

```text
Tier: STRATEGIC
Governance Status: HOLD
Recommended Action: INVENTORY_OPTIMIZATION / REVIEW
```

这正是项目希望表达的逻辑：**表现好，不等于当前没有风险。**

## 5 分钟面试演示路线

```text
1. Data Center
   先展示 Active Dataset = None，说明系统不会混用 Demo 与上传数据

2. Load Demo Dataset
   手动加载 50 个 Synthetic Partners

3. Channel Overview
   看整体渠道健康度和风险分布

4. Partner 360
   选一个 Partner，解释 Score、Risk、Gate 和 Recommended Action

5. Policy Studio + Scenario Lab
   改一个权重 → 保存 Draft → 模拟影响 → 再决定是否 Activate
```

更完整的演示话术见 [FINAL_DEMO_GUIDE.md](docs/FINAL_DEMO_GUIDE.md)。

## 本地运行

标准环境：**Python 3.12**

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

Streamlit 启动后，打开终端里显示的本地网址即可。首次运行会自动创建本地 SQLite 文件 `data/app.db`。

> Core functionality does not require an AI API key.

### 可选 AI 配置

如需体验 AI-enhanced Insight：

```bash
pip install -r requirements-ai.txt
```

然后在本地环境变量中配置：

```text
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-5-mini
```

真实 API Key 不应提交到 Git。

## 技术结构

```text
app.py                         Streamlit presentation layer
config/scoring_rules.yaml      Adaptive Policy configuration
data/synthetic/                7 Excel templates + synthetic portfolio
src/channel_governance/
  models.py                    Pydantic data contracts
  validation.py                Data validation
  policy.py                    Policy resolution and lifecycle
  scoring.py                   Score and Confidence
  governance.py                Risk, Gate, Tier, Status, Action
  evaluation.py                Evaluation orchestration
  data_normalizer.py           Business template normalization
  scenario.py                  Baseline vs Scenario
  insight.py                   Deterministic Management Insight
  insight_providers.py         Optional AI provider + fallback
  target_rationale.py          Target sanity check
  storage.py                   SQLite persistence / audit
tests/                         Unit + integration tests
```

展示层使用 **Refined Enterprise UI**：统一字号、留白、按钮、卡片、Tab、表格和 Empty State，但不改变业务引擎的计算逻辑。

## 工程验证

| 检查项 | 结果 |
|---|---:|
| Automated Tests | **166 passed** |
| Python Compile | Passed |
| Streamlit Headless Startup | Passed |
| Excel Browser-style Roundtrip | Passed |
| Explicit Demo Dataset Test | Passed |
| Empty State / No Auto-load Test | Passed |
| Core AI API Requirement | None |

详细验证记录见 [FINAL_SUBMISSION_VERIFICATION.md](docs/FINAL_SUBMISSION_VERIFICATION.md)。

## AI 是怎么参与开发的

这个项目确实使用了 AI 辅助开发，但我把 AI 当成“加速器”，不是项目负责人。

AI 主要参与：

- 需求拆解和架构讨论；
- 代码草拟；
- 测试用例设计；
- Debugging；
- 文档整理和一致性检查。

我负责确定业务问题、规则边界、产品取舍，并通过实际运行和自动化测试决定哪些 AI 输出可以进入最终版本。

详细记录见 [AI_USAGE.md](AI_USAGE.md)。

## 数据与项目边界

- 仓库内的 Partner、销售、库存、授信、Policy 参数均为 Synthetic Data；
- 不包含任何公司的真实客户数据、销售数据或内部系统数据；
- 不连接真实 CRM / ERP；
- 暂无用户登录、角色权限和正式审批流；
- SQLite 用于本地原型，不代表生产级多用户数据库；
- Target Rationale 是合理性检查，不是自动目标制定；
- 这是一个可运行的软件原型，不声称已经是 production-ready enterprise system。

## 最后一句话

这个项目想展示的是：

**如何把复杂的渠道管理经验，转化成一套可以被系统执行、被管理者理解、被数据验证、也能继续迭代的治理方法。**
