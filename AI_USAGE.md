# AI-Assisted Development Record

这个项目使用了 AI 辅助开发，但我希望把 AI 的角色说清楚：

**AI 是开发加速器，不是产品负责人，也不是业务决策者。**

我负责确定项目要解决什么问题、哪些规则合理、哪些边界不能越，以及最终哪些内容可以进入仓库。AI 主要帮助我更快地拆需求、写初稿、补测试、找问题和整理文档。

## 我负责什么

这个项目里，以下内容由我确定并负责最终判断：

- 项目方向和业务问题；
- 产品范围和优先级；
- Channel Governance 的核心逻辑；
- `Risk ≠ Score`、`Gate > Score`、`NULL ≠ 0` 等设计原则；
- 哪些判断必须保留 Human Review；
- Synthetic Data 和保密边界；
- UI 和数据流程是否符合真实使用习惯；
- 是否接受 AI 生成的代码或方案；
- 最终提交版本。

我不会因为 AI “能写出来”就直接接受。项目里多次出现过 AI 初稿在技术上可运行、但业务表达或产品逻辑不够合理的情况，最后都通过实际运行、测试和人工判断继续修改。

## AI 主要帮助了什么

AI 参与的工作主要包括：

- 把业务想法拆成可开发的模块和任务；
- 讨论数据结构和软件架构；
- 草拟 Python / Streamlit 代码；
- 设计自动化测试；
- Debugging 和代码一致性检查；
- 帮助整理 README、Demo Guide 和技术说明；
- 对 UI、数据流和边界条件提出改进建议。

AI 没有负责最终商业判断，也没有权限自动决定价格、返点、授信、终止合作、销售目标或合规结论。

## 开发过程中的几个实际例子

| 阶段 | AI 的帮助 | 我的判断 / 修改 | 最终结果 |
|---|---|---|---|
| Requirement & Architecture | 把渠道治理需求拆成 Policy、Score、Risk、Gate、Action 等模块 | 确认项目不是 CRM，也不是自动商业决策系统 | 形成清晰的软件边界和模块结构 |
| Scoring Engine | 草拟可配置权重、评分和 Confidence 逻辑 | 明确缺失值不能当 0，评分必须 deterministic | Score 和 Confidence 可解释、可测试 |
| Governance Logic | 草拟 Risk、Gate、Tier 和 Recommended Action | 明确 Risk 必须独立于 Score，Gate 优先级更高 | 高分 + 高风险 + HOLD 可以同时存在 |
| Policy Studio | 草拟两层权重和 Policy Lifecycle | 要求 Draft 不能直接影响正式评价，必须先 Scenario Test | Draft → Test → Activate 的完整流程 |
| AI Insight | 草拟可选 AI Provider 和 Prompt | 限制 AI 只能解释结构化结果，不能修改核心判断 | AI 不可用时自动 fallback 到规则输出 |
| Data Center | 帮助设计 Excel 模板识别、Validation 和 Normalization | 实际测试后发现 Demo 数据和上传数据混用风险，要求重做数据主链路 | 一个明确的 Active Dataset 统一驱动全系统 |
| UI Productization | 草拟样式和布局规则 | 通过真实浏览器测试不断调整字号、间距、按钮和空状态 | 形成 Refined Enterprise UI |
| Debugging | 帮助定位 RecommendedAction 属性错误、图标字体冲突等问题 | 逐项复现并验证修复 | 页面稳定运行，回归测试覆盖问题 |

## 我刻意没有采用的做法

有些方案实现起来很容易，但不适合这个项目，所以明确没有采用：

1. **用 AI 直接生成 Partner Score**  
   评分必须能解释、能复算、能审计，所以核心评分由规则完成。

2. **把缺失值自动当成 0**  
   “不知道”不等于“表现差”。缺失信息降低 Confidence，而不是制造负面事实。

3. **Score 直接对应返点、价格或授信**  
   这些属于真实商业决策，不能由一个原型自动执行。

4. **把 Compliance Risk 藏进总分里**  
   高分 Partner 仍然可能有重大当前风险，所以 Risk 必须独立存在。

5. **认为库存越低越好**  
   渠道库存也承担本地供货功能，因此采用合理区间，而不是简单追求最低库存。

6. **为了满足代码量而增加无意义代码**  
   项目优先保证完整性、测试和可解释性，而不是人为堆行数。

7. **让核心产品依赖 AI API**  
   没有 API Key 时系统仍然可以完整运行。AI 是可选能力，不是运行前提。

## 我怎么验证 AI 生成的内容

我使用了几层验证，而不是只看代码“看起来对不对”：

```text
业务逻辑判断
→ Pydantic 数据约束
→ Pytest 自动化测试
→ Python Compile
→ Streamlit Headless Startup
→ 浏览器实际操作
→ 再调整产品逻辑和 UI
```

最终版本包含 **166 个自动化测试**，并通过 Python 编译、Streamlit 启动、Excel 浏览器式上传、Synthetic Demo Dataset、Empty State 和 Active Dataset 流程验证。

## 运行时 AI 的边界

应用本身不要求 AI API Key。

默认的 Management Insight 使用 deterministic rules，可以离线运行。可选的 AI-enhanced Insight 只接收经过筛选的结构化摘要，用于解释和改写文字。

AI 不会接管：

- Partner Score；
- Risk Severity；
- Gate；
- Tier；
- Governance Status；
- 最终销售目标；
- 商业条款；
- 法律或合规结论。

如果 AI Provider 不可用，系统会自动回退到 Rules-based Insight。

## 最后说明

我使用 AI 的目的不是证明“AI 可以替我完成开发”，而是证明：

**我能够把业务问题拆清楚，知道哪些事情适合让 AI 加速，哪些判断必须由人负责，并且能通过测试和实际运行把 AI 生成的内容变成一个自己理解、能够解释、也能够承担结果的软件项目。**
