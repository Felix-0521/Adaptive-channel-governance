"""Chinese-first presentation helpers.

This module translates display values only. Domain enums, rules, persisted values,
and scoring/governance behavior remain unchanged.
"""

from __future__ import annotations

import re
from typing import Any


TIER_LABELS = {
    "STRATEGIC": "战略级 · Strategic",
    "CORE": "核心级 · Core",
    "DEVELOPMENT": "发展级 · Development",
    "WATCHLIST": "观察级 · Watchlist",
    "UNRATED": "暂未评级 · Unrated",
}

RISK_LABELS = {
    "LOW": "低风险 · Low",
    "MEDIUM": "中等风险 · Medium",
    "HIGH": "高风险 · High",
    "CRITICAL": "严重风险 · Critical",
}

GOVERNANCE_LABELS = {
    "ACTIVE": "正常推进 · Active",
    "MONITOR": "持续观察 · Monitor",
    "REVIEW": "需要复核 · Review",
    "HOLD": "暂停推进 · Hold",
}

LIFECYCLE_LABELS = {
    "ENTRY": "进入期 · Entry",
    "BUILD": "建设期 · Build",
    "EMERGING": "起步期 · Emerging",
    "GROWTH": "增长期 · Growth",
    "MATURE": "成熟期 · Mature",
    "MAINTENANCE": "维护期 · Maintenance",
    "RENEWAL": "续约期 · Renewal",
    "DECLINE": "衰退期 · Decline",
}

MARKET_TIER_LABELS = {
    "HIGH_VALUE": "高价值市场 · High Value",
    "GROWTH_VALUE": "增长价值市场 · Growth Value",
    "MID_VALUE": "中等价值市场 · Mid Value",
    "DEVELOPING": "发展中市场 · Developing",
}

PARTNER_TYPE_LABELS = {
    "DISTRIBUTOR": "分销商 · Distributor",
    "DEALER": "经销商 · Dealer",
}

BUSINESS_LINE_LABELS = {
    "AGRICULTURE": "农业业务 · Agriculture",
    "GEOSPATIAL_SURVEYING": "测绘业务 · Geospatial Surveying",
    "LANDSCAPING": "园林业务 · Landscaping",
    "CONSTRUCTION": "工程建设 · Construction",
    "FACILITY": "设施服务 · Facility",
}

PILLAR_LABELS = {
    "COMMERCIAL_PERFORMANCE": "商业表现 · Commercial Performance",
    "MARKET_CAPABILITY": "市场能力 · Market Capability",
    "OPERATIONAL_HEALTH": "运营健康 · Operational Health",
    "FINANCIAL_HEALTH": "财务健康 · Financial Health",
    "SERVICE_TECH_CAPABILITY": "服务与技术能力 · Service & Tech Capability",
    "COMPLIANCE_GOVERNANCE": "合规治理 · Compliance Governance",
}

METRIC_LABELS = {
    "annual_revenue": "年度收入 · Annual Revenue",
    "target_achievement_pct": "目标达成率 · Target Achievement",
    "yoy_growth_pct": "同比增长 · YoY Growth",
    "new_product_contribution_pct": "新品贡献率 · New Product Contribution",
    "active_dealers": "活跃经销商数 · Active Dealers",
    "geographic_coverage_pct": "区域覆盖率 · Geographic Coverage",
    "inventory_days": "库存天数 · Inventory Days",
    "sell_out_performance_pct": "Sell-out 表现 · Sell-out Performance",
    "forecast_accuracy_pct": "预测准确率 · Forecast Accuracy",
    "payment_on_time_pct": "按时付款率 · Payment On Time",
    "ar_overdue_90d_pct": "逾期 90 天应收占比 · AR Overdue 90d",
    "certified_engineers": "认证工程师数 · Certified Engineers",
    "training_completion_pct": "培训完成率 · Training Completion",
    "demo_capability": "Demo 能力 · Demo Capability",
    "data_reporting_quality_pct": "数据上报质量 · Reporting Quality",
    "pricing_violations": "价格纪律异常 · Pricing Signals",
    "unauthorized_sales_incidents": "未授权销售事件 · Unauthorized Sales",
    "sanctions_match": "制裁名单信号 · Sanctions Signal",
    "material_contract_breach": "重大合同违约 · Contract Breach",
    "confidence": "数据置信度 · Confidence",
}

ACTION_LABELS = {
    "BRANDING_MDF": "品牌与市场活动支持 · Branding / MDF",
    "ENGINEER_SUPPORT": "工程师支持 · Engineer Support",
    "DEMO_SUPPORT": "样机与演示支持 · Demo Support",
    "TRAINING_CERTIFICATION": "培训与认证 · Training & Certification",
    "NEW_PRODUCT_ENABLEMENT": "新品导入支持 · New Product Enablement",
    "CHANNEL_EXPANSION": "渠道拓展 · Channel Expansion",
    "JOINT_BUSINESS_PLANNING": "联合业务规划 · Joint Business Planning",
    "AFTERSALES_CAPABILITY": "售后能力建设 · Aftersales Capability",
    "INVENTORY_OPTIMIZATION": "库存优化 · Inventory Optimization",
    "CREDIT_REVIEW": "授信复核 · Credit Review",
    "DATA_QUALITY_IMPROVEMENT": "数据质量改善 · Data Quality Improvement",
    "CORRECTIVE_ACTION_PLAN": "改善行动计划 · Corrective Action Plan",
    "COMPLIANCE_REVIEW": "合规复核 · Compliance Review",
    "NO_ADDITIONAL_SUPPORT": "暂缓额外支持 · No Additional Support",
}

PRIORITY_LABELS = {
    "HIGH": "高优先级 · High",
    "MEDIUM": "中优先级 · Medium",
    "LOW": "低优先级 · Low",
}

INSIGHT_SEVERITY_LABELS = {
    "INFO": "信息 · Info",
    "ATTENTION": "需要关注 · Attention",
    "WARNING": "重点关注 · Warning",
    "CRITICAL": "严重 · Critical",
}

TARGET_ASSESSMENT_LABELS = {
    "SUPPORTED": "依据较充分 · Supported",
    "STRETCH": "有挑战但可讨论 · Stretch",
    "REVIEW_REQUIRED": "需要管理层复核 · Review Required",
    "INSUFFICIENT_EVIDENCE": "依据不足 · Insufficient Evidence",
}

SCENARIO_SCOPE_LABELS = {
    "SINGLE_PARTNER": "单个合作伙伴 · Single Partner",
    "SELECTED_MARKET": "指定市场 · Selected Market",
    "FULL_PORTFOLIO": "全部合作伙伴 · Full Portfolio",
}

RISK_CODE_LABELS = {
    "EXCESS_INVENTORY": "库存偏高 · Excess Inventory",
    "SUPPLY_COVERAGE": "库存覆盖不足 · Supply Coverage",
    "OVERDUE_AR": "长期逾期应收 · Overdue AR",
    "LOW_DATA_QUALITY": "数据质量偏低 · Low Data Quality",
    "PRICING_DISCIPLINE": "价格纪律信号 · Pricing Discipline",
    "UNAUTHORIZED_SALES": "未授权销售 · Unauthorized Sales",
    "SANCTIONS_MATCH": "制裁名单信号 · Sanctions Match",
    "MATERIAL_CONTRACT_BREACH": "重大合同违约 · Material Contract Breach",
}

GATE_LABELS = {
    "GATE_SANCTIONS_REVIEW": "制裁名单复核门槛 · Sanctions Review Gate",
    "GATE_CONTRACT_REVIEW": "合同风险复核门槛 · Contract Review Gate",
    "GATE_UNAUTHORIZED_SALES_REVIEW": "未授权销售复核门槛 · Unauthorized Sales Review Gate",
}

RISK_MESSAGES = {
    "Inventory is above the policy optimal band.": "库存高于当前策略设定的健康区间，建议结合 Sell-out 与库存结构进一步检查。",
    "Inventory is below the policy optimal band.": "库存低于当前策略设定的健康区间，需要关注本地供货覆盖能力。",
    "Over-90-day receivables require finance review.": "90 天以上逾期应收已达到风险条件，建议优先进行财务与授信复核。",
    "Reported data quality is below the policy threshold.": "当前上报数据质量低于策略阈值，评价可靠性可能受到影响。",
    "A pricing-discipline signal requires human investigation.": "系统识别到价格纪律异常信号，需要人工调查确认；该信号本身不代表法律结论。",
    "An unauthorized-sales signal requires compliance review.": "系统识别到未授权销售风险信号，需要优先进行合规复核。",
    "A synthetic sanctions-match signal requires immediate review.": "Synthetic Data 中出现制裁名单匹配信号，需要立即人工复核。",
    "A material contract-breach signal requires legal review.": "系统识别到重大合同违约信号，需要法务或专业人员复核。",
}

ACTION_REASONS = {
    "A critical gate requires specialist review before any growth action.": "已触发严重治理门槛。在继续增长支持之前，应先完成相关专业复核。",
    "Discretionary support should pause until the gate is reviewed by a human.": "在治理门槛完成人工复核前，建议暂缓非必要的额外支持。",
    "Material overdue receivables take priority over growth support.": "长期逾期应收的处理优先级高于增长支持，建议先完成授信与回款风险复核。",
    "Inventory exceeds the configured optimal band and requires a sell-out-led plan.": "库存已超过策略设定的健康区间，建议以 Sell-out 改善为核心制定库存优化计划。",
    "The pricing-discipline signal requires investigation without presuming a legal finding.": "价格纪律信号需要进一步调查，但不能仅凭该信号直接作出违规或法律结论。",
    "Reporting quality is below the configured threshold.": "数据上报质量低于设定阈值，建议先提升数据完整性和准确性。",
    "Early-stage market coverage is below the capability benchmark.": "当前处于市场建设阶段，但渠道覆盖低于能力基准，建议优先拓展有效覆盖。",
    "The partner lacks demo capability required for early market creation.": "当前合作伙伴缺少市场早期拓展所需的 Demo 能力，建议补充样机与演示支持。",
    "Technical staffing is insufficient for the current lifecycle stage.": "当前技术人员配置不足以支撑现阶段业务发展，建议增加工程师支持。",
    "Training completion is below the enablement benchmark.": "培训完成率低于能力建设基准，建议优先完成培训与认证。",
    "A healthy mature partner has new-product contribution below the policy benchmark.": "该成熟合作伙伴整体经营健康，但新品贡献低于策略基准，适合优先推进新品导入。",
    "Brand activation can support the reviewed new-product enablement plan.": "在新品导入计划经人工确认后，可通过品牌与市场活动增强落地效果。",
    "No overriding risk or capability gap is present; maintain a reviewed joint plan.": "当前未发现需要优先处理的重大风险或能力缺口，建议保持定期联合业务规划。",
    "No targeted growth action is justified; define measurable improvement priorities.": "当前证据不足以支持明确的增长动作，建议先制定可量化的改善目标并持续复核。",
}


def _label(mapping: dict[str, str], value: Any) -> str:
    raw = getattr(value, "value", value)
    if raw is None:
        return "暂无 · N/A"
    raw = str(raw)
    return mapping.get(raw, raw.replace("_", " ").title())


def tier_label(value: Any) -> str:
    return _label(TIER_LABELS, value)


def risk_label(value: Any) -> str:
    return _label(RISK_LABELS, value)


def governance_label(value: Any) -> str:
    return _label(GOVERNANCE_LABELS, value)


def lifecycle_label(value: Any) -> str:
    return _label(LIFECYCLE_LABELS, value)


def market_tier_label(value: Any) -> str:
    return _label(MARKET_TIER_LABELS, value)


def partner_type_label(value: Any) -> str:
    return _label(PARTNER_TYPE_LABELS, value)


def business_line_label(value: Any) -> str:
    return _label(BUSINESS_LINE_LABELS, value)


def pillar_label(value: Any) -> str:
    return _label(PILLAR_LABELS, value)


def metric_label(value: Any) -> str:
    return _label(METRIC_LABELS, value)


def action_label(value: Any) -> str:
    return _label(ACTION_LABELS, value)


def priority_label(value: Any) -> str:
    return _label(PRIORITY_LABELS, value)


def insight_severity_label(value: Any) -> str:
    return _label(INSIGHT_SEVERITY_LABELS, value)


def target_assessment_label(value: Any) -> str:
    return _label(TARGET_ASSESSMENT_LABELS, value)


def scenario_scope_label(value: Any) -> str:
    return _label(SCENARIO_SCOPE_LABELS, value)


def risk_code_label(value: Any) -> str:
    return _label(RISK_CODE_LABELS, value)


def gate_label(value: Any) -> str:
    return _label(GATE_LABELS, value)


def risk_message(text: str) -> str:
    return RISK_MESSAGES.get(text, localize_text(text))


def action_reason(text: str) -> str:
    return ACTION_REASONS.get(text, localize_text(text))


def format_evidence(evidence: dict[str, Any]) -> str:
    if not evidence:
        return "暂无额外证据"
    parts = []
    for key, value in evidence.items():
        key_label = METRIC_LABELS.get(key, GATE_LABELS.get(key, key.replace("_", " ").title()))
        if isinstance(value, list):
            value_text = ", ".join(gate_label(item) for item in value)
        elif isinstance(value, bool):
            value_text = "是" if value else "否"
        elif isinstance(value, float):
            value_text = f"{value:.2f}".rstrip("0").rstrip(".")
        else:
            value_text = str(value)
        parts.append(f"{key_label}: {value_text}")
    return "；".join(parts)


def localize_text(text: str) -> str:
    """Translate deterministic engine prose without changing the engine output."""
    if not text:
        return text
    if text in RISK_MESSAGES:
        return RISK_MESSAGES[text]
    if text in ACTION_REASONS:
        return ACTION_REASONS[text]

    direct = {
        "Insufficient evidence to determine the primary cause.": "现有证据不足，暂时无法可靠判断最主要的原因。",
        "A triggered governance gate takes precedence over commercial support review.": "已触发治理门槛，相关风险复核的优先级高于商业支持或增长动作。",
        "Missing scored observations reduce the reliability of the evaluation.": "部分评分指标缺失，因此本次评价的可靠性会下降。",
        "No new action is generated; management should review the existing evaluation.": "当前没有新增管理动作，建议管理者结合现有评价结果进行复核。",
        "No historical observations were supplied; this insight does not claim period-over-period change.": "当前未提供历史周期数据，因此本分析不会推断环比或同比变化趋势。",
        "The proposed target lacks enough observed evidence for a reliable sanity check.": "当前可用证据不足，暂时无法对该目标做出可靠的合理性判断。",
        "The target requires management review because governance constraints conflict with growth execution.": "当前治理风险与增长执行存在冲突，建议由管理层进一步复核目标。",
        "Early-stage evidence supports the proposed target, subject to execution of the stated market-building plan.": "现有市场建设证据基本支持该目标，但前提是既定的市场拓展计划能够按计划执行。",
        "The early-stage target is a stretch supported by capability or pipeline evidence, not by the low historical base.": "该目标具有一定挑战性，主要由当前能力或 Pipeline 证据支撑，而不是由较低的历史基数支撑。",
        "The early-stage target needs review because market-building evidence is weak.": "当前市场建设证据偏弱，该目标需要进一步复核。",
        "An aggressive growth target conflicts with the decline lifecycle context and requires management review.": "当前处于衰退阶段，激进增长目标与生命周期背景存在冲突，需要管理层复核。",
        "The proposed growth conflicts with mature-business capacity or operating constraints.": "拟议增长目标与成熟业务当前的经营能力或运营约束存在冲突。",
        "Observable trend and capacity evidence are broadly consistent with the proposed target.": "现有趋势和能力证据与拟议目标总体一致。",
        "The target is plausible only if the listed execution assumptions are achieved.": "只有在列出的执行假设能够兑现时，该目标才具有合理性。",
        "Required resources are recorded as committed.": "所需资源已明确承诺。",
        "Required resources are not recorded as committed.": "所需资源尚未明确承诺。",
        "High-priority governance signals require review before relying on growth assumptions.": "存在高优先级治理信号，在采用增长假设前应先完成风险复核。",
        "Inventory is above the configured operating band.": "库存高于当前策略设定的运营健康区间。",
        "Over-90-day receivables are above the configured risk threshold.": "90 天以上逾期应收高于当前策略设定的风险阈值。",
        "No material supporting driver was observed in the supplied fields.": "当前字段中未观察到明显的目标支持因素。",
        "No material constraint was observed in the supplied fields.": "当前字段中未观察到明显的目标制约因素。",
        "Management must validate the incremental growth assumptions.": "管理层需要进一步验证增量增长假设。",
        "Pipeline conversion and planned footprint expansion must be delivered.": "需要按计划实现 Pipeline 转化和市场覆盖扩张。",
        "Incremental pipeline conversion must close the gap above the historical trend.": "需要依靠新增 Pipeline 转化弥补高于历史趋势的增长缺口。",
        "Management must confirm the resources required for execution.": "管理层需要确认实现目标所需的资源投入。",
    }
    if text in direct:
        return direct[text]

    match = re.fullmatch(
        r"(.+?) is classified as ([A-Z_]+) with a score of (.+?)\. Governance status is ([A-Z_]+) under (.+)\.",
        text,
    )
    if match:
        name, tier, score, status, source = match.groups()
        return (
            f"{name} 当前评为 {tier_label(tier)}，综合评分为 {score}。"
            f"治理状态为 {governance_label(status)}，本次评价采用 {source} 规则。"
        )

    match = re.fullmatch(r"Management should review ([A-Z_]+): (.+)", text)
    if match:
        code, message = match.groups()
        return f"管理层应重点复核 {risk_code_label(code)}：{risk_message(message)}"

    match = re.fullmatch(r"The largest observable weakness is (.+) relative to policy\.", text)
    if match:
        return f"相对当前策略，最明显的薄弱项是 {metric_label(match.group(1))}。"

    match = re.fullmatch(r"Missing observations: (.+)\.", text)
    if match:
        metrics = "、".join(metric_label(item.strip()) for item in match.group(1).split(","))
        return f"缺失指标：{metrics}。"

    match = re.fullmatch(r"Overall score confidence is (.+)\.", text)
    if match:
        return f"本次整体评分置信度为 {match.group(1)}。"

    match = re.fullmatch(r"(.+) is ([0-9.]+) weighted score points below its configured benchmark\.", text)
    if match:
        return f"{metric_label(match.group(1))} 相对策略基准造成约 {match.group(2)} 个加权分的缺口。"

    match = re.fullmatch(r"(.+) contributes ([0-9.]+) weighted score points\.", text)
    if match:
        return f"{metric_label(match.group(1))} 当前贡献约 {match.group(2)} 个加权分。"

    match = re.fullmatch(r"([A-Z_]+) is triggered and requires specialist review\.", text)
    if match:
        return f"{gate_label(match.group(1))} 已触发，需要相关专业人员复核。"

    match = re.fullmatch(r"Pipeline coverage is ([0-9.]+)x, above the supported threshold\.", text)
    if match:
        return f"Pipeline 覆盖为 {match.group(1)}x，高于当前策略的充分支持阈值。"
    match = re.fullmatch(r"Pipeline coverage is ([0-9.]+)x, providing partial support\.", text)
    if match:
        return f"Pipeline 覆盖为 {match.group(1)}x，可为目标提供部分支撑。"
    match = re.fullmatch(r"Pipeline coverage is only ([0-9.]+)x of the proposed target\.", text)
    if match:
        return f"Pipeline 仅覆盖拟议目标的 {match.group(1)}x，支撑力度偏弱。"
    match = re.fullmatch(r"Market capability score is ([0-9.]+)\.", text)
    if match:
        return f"市场能力评分为 {match.group(1)}。"
    match = re.fullmatch(r"The plan includes ([0-9]+) new customers\.", text)
    if match:
        return f"当前计划包含 {match.group(1)} 个新客户目标。"

    return text
