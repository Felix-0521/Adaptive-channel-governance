from pathlib import Path

app = Path('app.py')
text = app.read_text(encoding='utf-8')

anchor = 'from channel_governance.ui_theme import apply_visual_theme\n'
imports = '''from channel_governance.ui_theme import apply_visual_theme
from channel_governance.display_labels import (
    action_label,
    action_reason,
    business_line_label,
    format_evidence,
    gate_label,
    governance_label,
    insight_severity_label,
    lifecycle_label,
    localize_text,
    market_tier_label,
    metric_label,
    partner_type_label,
    pillar_label,
    priority_label,
    risk_code_label,
    risk_label,
    risk_message,
    scenario_scope_label,
    target_assessment_label,
    tier_label,
)
'''
if 'from channel_governance.display_labels import (' not in text:
    text = text.replace(anchor, imports, 1)

text = text.replace(
'''def render_dataset_empty_state(feature_name: str) -> None:
    st.info(
        f"尚未加载业务数据 · No active dataset for {feature_name}. "
        "请前往 Data Center 上传业务模板，或手动加载 Synthetic Demo Dataset。"
    )
''',
'''def render_dataset_empty_state(feature_name: str) -> None:
    st.info(
        f"{feature_name} 暂无可分析的数据。请先前往【数据中心】上传并确认业务数据，"
        "或手动加载演示数据集。"
    )
''')

# Overview display layer.
text = text.replace(
'''    st.markdown("##### 渠道健康仪表板 · Channel Health Dashboard")
    row1 = st.columns(6)
''',
'''    display_results = results.copy()
    display_results["等级"] = display_results["tier"].map(tier_label)
    display_results["风险等级"] = display_results["risk_level"].map(risk_label)
    display_results["治理状态"] = display_results["governance_status"].map(governance_label)
    display_results["生命周期"] = display_results["lifecycle_stage"].map(lifecycle_label)

    st.markdown("##### 渠道健康仪表板 · Channel Health Dashboard")
    row1 = st.columns(6)
''')
text = text.replace('row1[5].metric("待处理建议\\nRecommended Actions", action_count)', 'row1[5].metric("有管理建议\\nRecommended Actions", action_count)')
text = text.replace(
'''    gov_data["status_display"] = gov_data["status"].map({
        "ACTIVE": "活跃 Active", "MONITOR": "监控 Monitor",
        "REVIEW": "复核 Review", "HOLD": "暂停 Hold",
    })
''',
'''    gov_data["status_display"] = gov_data["status"].map(governance_label)
''')
text = text.replace('legend_title_text="Status"', 'legend_title_text="治理状态"')
text = text.replace(
'''        results.sort_values("score", ascending=True),
        x="score",
        y="partner_name",
        color="governance_status",
''',
'''        display_results.sort_values("score", ascending=True),
        x="score",
        y="partner_name",
        color="治理状态",
''')
text = text.replace('color_discrete_map=status_colors,', 'color_discrete_map={governance_label(k): v for k, v in status_colors.items()},', 1)
text = text.replace('hover_data=["policy_id", "confidence", "tier", "risk_codes"],', 'hover_data=["policy_id", "confidence", "等级", "风险等级"],')
text = text.replace(
'''    tier_counts = results["tier"].value_counts().rename_axis("tier").reset_index(name="partners")
    tier_chart = px.bar(
        tier_counts, x="tier", y="partners", color="tier",
''',
'''    tier_counts = results["tier"].value_counts().rename_axis("tier").reset_index(name="partners")
    tier_counts["等级"] = tier_counts["tier"].map(tier_label)
    tier_chart = px.bar(
        tier_counts, x="等级", y="partners", color="等级",
''')
text = text.replace(
'''    risk_counts = results["risk_level"].value_counts().rename_axis("risk").reset_index(name="partners")
    risk_chart = px.bar(
        risk_counts, x="risk", y="partners", color="risk",
        title="风险分布 · Risk Distribution", text_auto=True,
        color_discrete_map={"LOW": "#2E7D32", "MEDIUM": "#ED9B25", "HIGH": "#D66B2C", "CRITICAL": "#B3261E"},
''',
'''    risk_counts = results["risk_level"].value_counts().rename_axis("risk").reset_index(name="partners")
    risk_counts["风险等级"] = risk_counts["risk"].map(risk_label)
    risk_chart = px.bar(
        risk_counts, x="风险等级", y="partners", color="风险等级",
        title="风险分布 · Risk Distribution", text_auto=True,
        color_discrete_map={risk_label("LOW"): "#2E7D32", risk_label("MEDIUM"): "#ED9B25", risk_label("HIGH"): "#D66B2C", risk_label("CRITICAL"): "#B3261E"},
''')
text = text.replace(
'''    lifecycle_counts = results["lifecycle_stage"].value_counts().rename_axis("lifecycle").reset_index(name="partners")
    lc_chart = px.bar(
        lifecycle_counts, x="lifecycle", y="partners", color="lifecycle",
''',
'''    lifecycle_counts = results["lifecycle_stage"].value_counts().rename_axis("lifecycle").reset_index(name="partners")
    lifecycle_counts["生命周期"] = lifecycle_counts["lifecycle"].map(lifecycle_label)
    lc_chart = px.bar(
        lifecycle_counts, x="生命周期", y="partners", color="生命周期",
''')
old_worklist = '''    st.dataframe(
        results.sort_values(["governance_status", "score"], ascending=[False, True]),
        use_container_width=True,
        hide_index=True,
        column_config={
            "score": st.column_config.NumberColumn(format="%.1f"),
            "confidence": st.column_config.ProgressColumn(min_value=0, max_value=1, format="%.0f%%"),
        },
    )
'''
new_worklist = '''    worklist = display_results.sort_values(["governance_status", "score"], ascending=[False, True])[
        ["partner_name", "business_line", "country_code", "score", "confidence", "等级", "风险等级", "治理状态"]
    ].rename(columns={
        "partner_name": "合作伙伴", "business_line": "业务线", "country_code": "国家",
        "score": "评分", "confidence": "置信度",
    })
    worklist["业务线"] = worklist["业务线"].map(business_line_label)
    st.dataframe(
        worklist,
        use_container_width=True,
        hide_index=True,
        column_config={
            "评分": st.column_config.NumberColumn(format="%.1f"),
            "置信度": st.column_config.ProgressColumn(min_value=0, max_value=1, format="%.0f%%"),
        },
    )
'''
text = text.replace(old_worklist, new_worklist)

# Partner 360 profile and score cards.
text = text.replace(
'''        f"**{partner.partner_name}**  \\n"
        f"{partner.business_line} · {partner.country_code} · {partner.partner_type.value}"
''',
'''        f"**{partner.partner_name}**  \\n"
        f"{business_line_label(partner.business_line)} · {partner.country_code} · {partner_type_label(partner.partner_type)}"
''')
text = text.replace(
'''        f"Lifecycle: **{partner.lifecycle_stage.value}**  \\n"
        f"Market Tier: **{partner.market_tier.value}**  \\n"
        f"Policy: `{result.policy_id}` v{result.policy_version}"
''',
'''        f"生命周期：**{lifecycle_label(partner.lifecycle_stage)}**  \\n"
        f"市场等级：**{market_tier_label(partner.market_tier)}**  \\n"
        f"适用策略：`{result.policy_id}` v{result.policy_version}"
''')
text = text.replace('sc3.metric("合作伙伴等级\\nPartner Tier", result.tier.title())', 'sc3.metric("合作伙伴等级\\nPartner Tier", tier_label(result.tier))')
text = text.replace('sc4.metric("风险等级\\nRisk Level", risk_level.title())', 'sc4.metric("风险等级\\nRisk Level", risk_label(risk_level))')
text = text.replace('sc5.metric("治理状态\\nGovernance Status", result.governance_status.value.title())', 'sc5.metric("治理状态\\nGovernance Status", governance_label(result.governance_status))')
text = text.replace('{"维度 Pillar": pillar.replace("_", " ").title(), "评分 Score": score}', '{"治理维度": pillar_label(pillar), "评分": score}')
text = text.replace('x="维度 Pillar",\n            y="评分 Score",', 'x="治理维度",\n            y="评分",')
text = text.replace('color="评分 Score",', 'color="评分",')

# Insight mode and content.
text = text.replace(
'''    insight_options = ["Rules-based", "AI-enhanced"] if ai_provider.available else ["Rules-based"]
    insight_mode = st.radio(
        "洞察模式 · Insight Mode", insight_options, horizontal=True,
    )
''',
'''    insight_options = ["Rules-based", "AI-enhanced"] if ai_provider.available else ["Rules-based"]
    insight_mode = st.radio(
        "洞察模式 · Insight Mode", insight_options, horizontal=True,
        format_func=lambda value: "规则解释 · Rules-based" if value == "Rules-based" else "AI 辅助解释 · AI-enhanced",
    )
''')
text = text.replace(
'''        f"模式 Mode: **{insight.source.replace('_', ' ').title()}** · "
        f"严重程度 Severity: **{insight.severity.value}**"
''',
'''        f"生成方式：**{'规则引擎 · Rules-based' if 'RULE' in insight.source.upper() else 'AI 辅助 · AI-enhanced'}** · "
        f"关注级别：**{insight_severity_label(insight.severity)}**"
''')
text = text.replace('st.write(insight.executive_summary)', 'st.write(localize_text(insight.executive_summary))')
text = text.replace(
'''                f"• **{driver.metric}** — {driver.explanation}  \\n"
                f"  Current: `{driver.current_value}` · Benchmark: `{driver.benchmark}` · "
                f"Impact: `{driver.impact}`"
''',
'''                f"• **{metric_label(driver.metric) if driver.category == 'METRIC' else (risk_code_label(driver.metric) if driver.category == 'RISK' else gate_label(driver.metric) if driver.category == 'GATE' else metric_label(driver.metric))}** — {localize_text(driver.explanation)}  \\n"
                f"  当前值：`{driver.current_value}` · 参考基准：`{driver.benchmark}` · "
                f"影响：`{driver.impact}`"
''')
text = text.replace('st.write(insight.management_attention)', 'st.write(localize_text(insight.management_attention))')
text = text.replace('st.write(insight.recommended_next_step)', 'st.write(action_reason(insight.recommended_next_step))')
text = text.replace('st.write(f"• {item}")\n\n    # ── 6. Risk', 'st.write(f"• {localize_text(item)}")\n\n    # ── 6. Risk', 1)

# Risk / actions.
text = text.replace(
'''                    f"{_emojis.get(risk.severity.value, '')} **{risk.code}** "
                    f"({risk.severity.value}): {risk.message}"
''',
'''                    f"{_emojis.get(risk.severity.value, '')} **{risk_code_label(risk.code)}** "
                    f"（{risk_label(risk.severity)}）：{risk_message(risk.message)}"
''')
text = text.replace('st.error(f"🚧 已触发 Gate：{gate}")', 'st.error(f"🚧 已触发治理门槛：{gate_label(gate)}")')
text = text.replace('st.markdown(f"**{action.action.value}** · {action.priority.value}")', 'st.markdown(f"**{action_label(action.action)}** · {priority_label(action.priority)}")')
text = text.replace('st.write(action.reason)', 'st.write(action_reason(action.reason))')
text = text.replace(
'''                        f"证据 Evidence: {action.evidence} · "
                        f"人工复核 Human Review: "
''',
'''                        f"证据：{format_evidence(action.evidence)} · "
                        f"需要人工复核："
''')

# Target rationale.
text = text.replace('["Unknown", "Confirmed", "Not confirmed"],', '["Unknown", "Confirmed", "Not confirmed"],\n            format_func=lambda value: {"Unknown": "暂不确定", "Confirmed": "已确认", "Not confirmed": "未确认"}[value],')
text = text.replace('tm[2].metric("评估结论\\nAssessment", rationale.assessment.value.replace("_", " ").title())', 'tm[2].metric("评估结论\\nAssessment", target_assessment_label(rationale.assessment))')
# Target text loops: safe exact replacements scoped by distinctive variables.
text = text.replace('for item in rationale.supporting_drivers:\n                st.write(f"• {item}")', 'for item in rationale.supporting_drivers:\n                st.write(f"• {localize_text(item)}")')
text = text.replace('for item in rationale.constraining_drivers:\n                st.write(f"• {item}")', 'for item in rationale.constraining_drivers:\n                st.write(f"• {localize_text(item)}")')
text = text.replace('for item in (rationale.required_assumptions or []):\n                st.write(f"• {item}")', 'for item in (rationale.required_assumptions or []):\n                st.write(f"• {localize_text(item)}")')
text = text.replace('st.write(rationale.management_review)', 'st.write(localize_text(rationale.management_review))')
text = text.replace(
'''            {"metric": metric, "observed_value": getattr(partner, metric, None),
             "normalized_score": score}
''',
'''            {"指标": metric_label(metric), "观测值": getattr(partner, metric, None),
             "标准化得分": score}
''')

# Policy Studio localized option display and weights.
text = text.replace('business_line = selectors[0].selectbox("业务线 · Business Line", business_lines)', 'business_line = selectors[0].selectbox("业务线 · Business Line", business_lines, format_func=business_line_label)')
text = text.replace('lifecycle_stage = selectors[1].selectbox("生命周期阶段 · Lifecycle Stage", lifecycle_stages)', 'lifecycle_stage = selectors[1].selectbox("生命周期阶段 · Lifecycle Stage", lifecycle_stages, format_func=lifecycle_label)')
text = text.replace('market_tier = selectors[2].selectbox("市场等级 · Market Tier", market_tiers)', 'market_tier = selectors[2].selectbox("市场等级 · Market Tier", market_tiers, format_func=market_tier_label)')
text = text.replace('partner_type = selectors[3].selectbox("合作伙伴类型 · Partner Type", partner_types)', 'partner_type = selectors[3].selectbox("合作伙伴类型 · Partner Type", partner_types, format_func=partner_type_label)')
text = text.replace('country_override = selectors[4].selectbox("国家覆盖 · Country Override", ["None", *country_codes])', 'country_override = selectors[4].selectbox("国家覆盖 · Country Override", ["None", *country_codes], format_func=lambda value: "无国家覆盖 · None" if value == "None" else value)')
text = text.replace('pillar.value.replace("_", " ").title(),\n                min_value=0.0,', 'pillar_label(pillar),\n                min_value=0.0,')
text = text.replace('with st.expander(pillar.value.replace("_", " ").title(), expanded=False):', 'with st.expander(pillar_label(pillar), expanded=False):')
text = text.replace('name.replace("_", " ").title(),\n                        min_value=0.0,', 'metric_label(name),\n                        min_value=0.0,')
text = text.replace('f"{pillar.value.replace(\'_\', \' \').title()} 指标合计 · Metric Total：100%"', 'f"{pillar_label(pillar)} 指标权重合计：100%"')
text = text.replace('f"{pillar.value.replace(\'_\', \' \').title()} 指标合计 · Metric Total："', 'f"{pillar_label(pillar)} 指标权重合计："')

# Scenario localization.
text = text.replace('format_func=lambda value: value.replace("_", " ").title(),', 'format_func=scenario_scope_label,')
text = text.replace('selected = column.selectbox(field.replace("_", " ").title(), ["All", *options])', '''label_map = {"country_code": "国家", "business_line": "业务线", "market_tier": "市场等级", "lifecycle_stage": "生命周期"}
            value_formatters = {"business_line": business_line_label, "market_tier": market_tier_label, "lifecycle_stage": lifecycle_label}
            selected = column.selectbox(label_map[field], ["All", *options], format_func=lambda value, field=field: "全部" if value == "All" else value_formatters.get(field, lambda x: x)(value))''')
old_comparison = 'comparisons = pd.DataFrame([item.model_dump() for item in report.comparisons])\n    st.dataframe(comparisons, use_container_width=True, hide_index=True)'
new_comparison = '''comparisons = pd.DataFrame([item.model_dump() for item in report.comparisons])
    comparisons["baseline_tier"] = comparisons["baseline_tier"].map(tier_label)
    comparisons["scenario_tier"] = comparisons["scenario_tier"].map(tier_label)
    comparisons["baseline_risk"] = comparisons["baseline_risk"].map(risk_label)
    comparisons["scenario_risk"] = comparisons["scenario_risk"].map(risk_label)
    comparisons["baseline_governance_status"] = comparisons["baseline_governance_status"].map(governance_label)
    comparisons["scenario_governance_status"] = comparisons["scenario_governance_status"].map(governance_label)
    comparisons = comparisons.rename(columns={
        "partner_id": "合作伙伴 ID", "partner_name": "合作伙伴", "baseline_score": "基准评分",
        "scenario_score": "模拟评分", "score_change": "评分变化", "baseline_tier": "基准等级",
        "scenario_tier": "模拟等级", "baseline_risk": "基准风险", "scenario_risk": "模拟风险",
        "baseline_governance_status": "基准治理状态", "scenario_governance_status": "模拟治理状态",
    })
    st.dataframe(comparisons, use_container_width=True, hide_index=True)'''
text = text.replace(old_comparison, new_comparison)
text = text.replace('"tier": tier,\n                "Baseline":', '"等级": tier_label(tier),\n                "基准 · Baseline":')
text = text.replace('"Scenario": summary.tier_counts_after[tier],', '"模拟 · Scenario": summary.tier_counts_after[tier],')
text = text.replace(').melt(id_vars="tier", var_name="policy", value_name="partners")', ').melt(id_vars="等级", var_name="策略", value_name="合作伙伴数量")')
text = text.replace('x="tier",\n        y="partners",\n        color="policy",', 'x="等级",\n        y="合作伙伴数量",\n        color="策略",')
text = text.replace('st.write("等级迁移 · Tier Migration", summary.tier_migration)', 'st.write("等级迁移 · Tier Migration", {f"{tier_label(k.split(\'->\')[0])} → {tier_label(k.split(\'->\')[1])}" if "->" in k else k: v for k, v in summary.tier_migration.items()})')

# Data Center source wording.
text = text.replace('set_active_dataset(demo_frame, "Synthetic Demo Dataset")', 'set_active_dataset(demo_frame, "演示数据 · Synthetic Demo Dataset")')
text = text.replace('st.session_state.get(PENDING_DATASET_SOURCE_KEY, "Uploaded Business Data")', 'st.session_state.get(PENDING_DATASET_SOURCE_KEY, "用户上传数据 · Uploaded Business Data")')
text = text.replace('st.session_state[PENDING_DATASET_SOURCE_KEY] = "Uploaded Business Data"', 'st.session_state[PENDING_DATASET_SOURCE_KEY] = "用户上传数据 · Uploaded Business Data"')

app.write_text(text, encoding='utf-8')

# Layout protection for longer Chinese-first labels.
theme = Path('src/channel_governance/ui_theme.py')
css = theme.read_text(encoding='utf-8')
insert = '''
        /* Chinese-first readability: allow long bilingual labels to wrap safely. */
        [data-testid="stMetric"] {
          min-width: 0;
          min-height: 118px;
        }
        [data-testid="stMetricLabel"], [data-testid="stMetricLabel"] p,
        [data-testid="stMetricValue"], [data-testid="stMetricValue"] div {
          white-space: normal !important;
          overflow-wrap: anywhere !important;
          word-break: break-word !important;
        }
        [data-testid="column"] { min-width: 0 !important; }
        .stButton > button p, .stDownloadButton > button p {
          white-space: normal !important;
          overflow-wrap: anywhere !important;
          line-height: 1.35 !important;
          text-align: center;
        }
        [data-testid="stExpander"] summary p,
        [data-baseweb="select"] span,
        [data-baseweb="input"] input {
          overflow-wrap: anywhere !important;
        }
        @media (max-width: 1180px) {
          [data-testid="stMetricValue"], [data-testid="stMetricValue"] div {
            font-size: 23px !important;
          }
          [data-testid="stMetricLabel"], [data-testid="stMetricLabel"] p {
            font-size: 12px !important;
          }
        }
'''
if 'Chinese-first readability' not in css:
    css = css.replace('        /* Preserve Streamlit Material Symbol glyphs. */', insert + '\n        /* Preserve Streamlit Material Symbol glyphs. */', 1)
theme.write_text(css, encoding='utf-8')
