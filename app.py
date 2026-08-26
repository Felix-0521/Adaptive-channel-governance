"""Streamlit presentation layer for the deterministic governance engines."""

from pathlib import Path
import sys


ROOT = Path(__file__).parent
SRC_PATH = ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

import pandas as pd
import plotly.express as px
import streamlit as st

from channel_governance.data_normalizer import normalize_excel_templates, TemplateId
from channel_governance.evaluation import evaluate_partner, evaluate_portfolio
from channel_governance.insight_providers import OpenAIInsightProvider, generate_management_insight
from channel_governance.models import (
    LifecycleStage,
    MarketTier,
    PartnerType,
    Pillar,
    RiskSeverity,
    ScenarioScope,
    TargetRationaleInput,
)
from channel_governance.partner_management import (
    analyze_partner_import,
    create_partner,
    import_partners,
)
from channel_governance.policy import PolicyLifecycleManager
from channel_governance.scenario import ScenarioService
from channel_governance.storage import SQLitePartnerStore
from channel_governance.target_rationale import assess_target
from channel_governance.template_schema import TEMPLATES
from channel_governance.validation import require_valid_dataframe
from channel_governance.ui_theme import apply_visual_theme


POLICY_PATH = ROOT / "config" / "scoring_rules.yaml"
DATA_PATH = ROOT / "data" / "sample_partners.csv"
DATABASE_PATH = ROOT / "data" / "app.db"
SYNTHETIC_DIR = ROOT / "data" / "synthetic"
SUPPORTED_BUSINESS_LINES = (
    "AGRICULTURE", "GEOSPATIAL_SURVEYING", "LANDSCAPING", "CONSTRUCTION", "FACILITY",
)
ACTIVE_DATASET_FRAME_KEY = "active_dataset_frame"
ACTIVE_DATASET_SOURCE_KEY = "active_dataset_source"
PENDING_DATASET_FRAME_KEY = "pending_dataset_frame"
PENDING_DATASET_SOURCE_KEY = "pending_dataset_source"


@st.cache_data
def load_demo_data() -> pd.DataFrame:
    """Load the repository's synthetic demonstration data."""
    return pd.read_csv(DATA_PATH)


def load_partner_data(store: SQLitePartnerStore) -> pd.DataFrame:
    """Combine immutable demo rows with locally managed Partner records."""
    demo = load_demo_data()
    managed = store.list_partners()
    if not managed:
        return demo
    managed_frame = pd.DataFrame(
        [partner.model_dump(mode="json") for partner in managed]
    )
    return pd.concat([demo, managed_frame], ignore_index=True, sort=False)


def _frame_from_records(records) -> pd.DataFrame:
    return pd.DataFrame([record.model_dump(mode="json") for record in records])


@st.cache_data
def load_demo_portfolio_frame() -> pd.DataFrame:
    templates_by_id = {}
    for tid in TemplateId:
        path = SYNTHETIC_DIR / f"{tid.value}.xlsx"
        if path.exists():
            templates_by_id[tid] = pd.read_excel(path)
    result = normalize_excel_templates(templates_by_id)
    if not result.success or not result.partner_records:
        details = "; ".join(issue.message for issue in result.errors[:5])
        raise ValueError(f"Demo dataset failed normalization: {details or 'no partner records'}")
    return _frame_from_records(result.partner_records)


def set_active_dataset(frame: pd.DataFrame, source: str) -> None:
    require_valid_dataframe(frame)
    st.session_state[ACTIVE_DATASET_FRAME_KEY] = frame.copy()
    st.session_state[ACTIVE_DATASET_SOURCE_KEY] = source


def clear_active_dataset() -> None:
    for key in (ACTIVE_DATASET_FRAME_KEY, ACTIVE_DATASET_SOURCE_KEY, PENDING_DATASET_FRAME_KEY, PENDING_DATASET_SOURCE_KEY):
        st.session_state.pop(key, None)


def render_dataset_empty_state(feature_name: str) -> None:
    st.info(
        f"尚未加载业务数据 · No active dataset for {feature_name}. "
        "请前往 Data Center 上传业务模板，或手动加载 Synthetic Demo Dataset。"
    )


def render_partner_management(
    store: SQLitePartnerStore, existing_partners
) -> None:
    """Create or import Partners, then reuse the existing evaluation pipeline."""
    st.subheader("合作伙伴管理 · Partner Management")
    st.caption(
        "新增记录保存到本地 SQLite，并直接复用现有 Adaptive Policy、Partner Score、"
        "Risk、Gate、Tier、Recommended Action 与 Management Insight Engine。"
    )
    result = st.session_state.pop("partner_management_result", None)
    if result:
        st.success(result)

    create_tab, import_tab = st.tabs(
        ["创建新合作伙伴 · Create New Partner", "批量导入 · Partner Import"]
    )
    with create_tab:
        with st.form("create-partner-form", clear_on_submit=True):
            first_row = st.columns(3)
            partner_name = first_row[0].text_input("合作伙伴名称 · Partner Name")
            country_code = first_row[1].text_input("国家代码 · Country (2-letter code)", max_chars=2)
            region = first_row[2].text_input("区域 · Region")
            second_row = st.columns(4)
            business_line = second_row[0].selectbox(
                "业务线 · Business Line", sorted({partner.business_line for partner in existing_partners})
            )
            partner_type = PartnerType(
                second_row[1].selectbox("合作伙伴类型 · Partner Type", [item.value for item in PartnerType])
            )
            lifecycle_stage = LifecycleStage(
                second_row[2].selectbox("生命周期阶段 · Lifecycle Stage", [item.value for item in LifecycleStage])
            )
            market_tier = MarketTier(
                second_row[3].selectbox("市场等级 · Market Tier", [item.value for item in MarketTier])
            )
            submitted = st.form_submit_button("创建合作伙伴 · Create Partner", type="primary")
        if submitted:
            try:
                partner = create_partner(
                    store,
                    partner_name=partner_name,
                    country_code=country_code,
                    region=region,
                    business_line=business_line,
                    partner_type=partner_type,
                    lifecycle_stage=lifecycle_stage,
                    market_tier=market_tier,
                )
            except ValueError as error:
                st.error(f"创建失败 · Create failed: {error}")
            else:
                st.session_state["partner_management_result"] = (
                    f"✓ 已创建 Partner {partner.partner_name}，ID 为 {partner.partner_id}。"
                    "渠道总览与 Partner 360 已刷新。"
                )
                st.rerun()

    with import_tab:
        st.info(
            "当前依赖支持 CSV。Excel 文件请先另存为 CSV。必填字段 · Required fields: "
            "partner_name, country_code, region, business_line, partner_type, "
            "lifecycle_stage, market_tier。"
        )
        uploaded = st.file_uploader("上传合作伙伴 CSV · Upload Partner CSV", type=["csv"])
        if uploaded is not None:
            try:
                upload_frame = pd.read_csv(uploaded)
            except Exception as error:
                st.error(f"文件读取失败 · Upload could not be read: {error}")
            else:
                analysis = analyze_partner_import(upload_frame, list(existing_partners))
                st.markdown("#### 数据预览 · Preview")
                st.dataframe(analysis.preview, use_container_width=True, hide_index=True)
                st.markdown("#### 数据校验 · Validation")
                if analysis.issues:
                    st.error(f"⚠ 发现 {len(analysis.issues)} 个 Validation Issue。")
                    st.dataframe(
                        pd.DataFrame(
                            [
                                {"row": issue.row, "field": issue.field, "message": issue.message}
                                for issue in analysis.issues
                            ]
                        ),
                        use_container_width=True,
                        hide_index=True,
                    )
                else:
                    st.success(f"✓ {len(analysis.records)} 条 Partner 记录通过 Validation。")
                if analysis.warnings:
                    st.warning(f"⚠ 缺失数据 / Data Quality：{len(analysis.warnings)} 条 Warning")
                    for warning in analysis.warnings:
                        st.caption(warning)
                if st.button(
                    "确认导入 · Confirm Import",
                    type="primary",
                    disabled=not analysis.can_import,
                ):
                    try:
                        imported = import_partners(store, analysis)
                    except ValueError as error:
                        st.error(f"导入失败 · Import failed: {error}")
                    else:
                        st.session_state["partner_management_result"] = (
                            f"✓ 已导入 Partner：{imported}。渠道总览与 Partner 360 已刷新。"
                        )
                        st.rerun()


def render_overview(results: pd.DataFrame) -> None:
    """B1: Executive Dashboard — answer 'How is our channel health today?'"""
    scored = results["score"].dropna()
    high_risk = int(results["risk_level"].isin(["HIGH", "CRITICAL"]).sum())
    review_required = int(results["governance_status"].isin(["REVIEW", "HOLD"]).sum())
    strategic_count = int((results["tier"] == "STRATEGIC").sum())
    active_count = int((results["governance_status"] == "ACTIVE").sum())
    # Count partners with at least one recommended action
    action_col = "recommended_actions"
    has_action = results[action_col].apply(lambda x: bool(x))
    action_count = int(has_action.sum())

    st.markdown("##### 渠道健康仪表板 · Channel Health Dashboard")
    row1 = st.columns(6)
    row1[0].metric("合作伙伴总数\nTotal Partners", len(results))
    row1[1].metric("战略合作伙伴\nStrategic Partners", strategic_count)
    row1[2].metric("高/严重风险\nHigh / Critical Risk", high_risk)
    row1[3].metric("需要复核\nReview Required", review_required)
    row1[4].metric("活跃治理状态\nActive Governance", active_count)
    row1[5].metric("待处理建议\nRecommended Actions", action_count)

    # Governance status distribution
    status_counts = results["governance_status"].value_counts()
    gov_colors = {"ACTIVE": "#2E7D32", "MONITOR": "#ED9B25", "REVIEW": "#D66B2C", "HOLD": "#B3261E"}
    gov_data = status_counts.rename_axis("status").reset_index(name="count")
    gov_data["status_display"] = gov_data["status"].map({
        "ACTIVE": "活跃 Active", "MONITOR": "监控 Monitor",
        "REVIEW": "复核 Review", "HOLD": "暂停 Hold",
    })
    gov_fig = px.bar(
        gov_data, x="status_display", y="count", color="status",
        color_discrete_map=gov_colors, title="治理状态分布 · Governance Status Distribution",
        text_auto=True,
    )
    gov_fig.update_layout(showlegend=False, height=260)
    st.plotly_chart(gov_fig, use_container_width=True)

    # Score vs status horizontal bar
    status_colors = {
        "ACTIVE": "#2E7D32",
        "MONITOR": "#ED9B25",
        "REVIEW": "#D66B2C",
        "HOLD": "#B3261E",
    }
    score_chart = px.bar(
        results.sort_values("score", ascending=True),
        x="score",
        y="partner_name",
        color="governance_status",
        orientation="h",
        color_discrete_map=status_colors,
        labels={"score": "合作伙伴评分 · Partner Score", "partner_name": "合作伙伴 · Partner"},
        title="合作伙伴评分与治理状态 · Partner Score & Governance Status",
        hover_data=["policy_id", "confidence", "tier", "risk_codes"],
    )
    score_chart.update_layout(legend_title_text="Status", height=max(460, len(results) * 22))
    st.plotly_chart(score_chart, use_container_width=True)

    col_layout = st.columns(3)
    tier_counts = results["tier"].value_counts().rename_axis("tier").reset_index(name="partners")
    tier_chart = px.bar(
        tier_counts, x="tier", y="partners", color="tier",
        title="合作伙伴等级分布 · Partner Tier Distribution", text_auto=True,
    )
    tier_chart.update_layout(showlegend=False, height=260)
    col_layout[0].plotly_chart(tier_chart, use_container_width=True)

    risk_counts = results["risk_level"].value_counts().rename_axis("risk").reset_index(name="partners")
    risk_chart = px.bar(
        risk_counts, x="risk", y="partners", color="risk",
        title="风险分布 · Risk Distribution", text_auto=True,
        color_discrete_map={"LOW": "#2E7D32", "MEDIUM": "#ED9B25", "HIGH": "#D66B2C", "CRITICAL": "#B3261E"},
    )
    risk_chart.update_layout(showlegend=False, height=260)
    col_layout[1].plotly_chart(risk_chart, use_container_width=True)

    lifecycle_counts = results["lifecycle_stage"].value_counts().rename_axis("lifecycle").reset_index(name="partners")
    lc_chart = px.bar(
        lifecycle_counts, x="lifecycle", y="partners", color="lifecycle",
        title="生命周期分布 · Lifecycle Distribution", text_auto=True,
    )
    lc_chart.update_layout(showlegend=False, height=260)
    col_layout[2].plotly_chart(lc_chart, use_container_width=True)

    st.subheader("治理工作清单 · Governance Worklist")
    st.caption("按治理状态与评分排序 · Sorted by governance status and score")
    st.dataframe(
        results.sort_values(["governance_status", "score"], ascending=[False, True]),
        use_container_width=True,
        hide_index=True,
        column_config={
            "score": st.column_config.NumberColumn(format="%.1f"),
            "confidence": st.column_config.ProgressColumn(min_value=0, max_value=1, format="%.0f%%"),
        },
    )


def render_partner_360(partners, evaluations, policies) -> None:
    """B4: Partner 360 — answer 'Why this result? What to do next?'

    Reading path:
      1. Partner Selector
      2. Partner Profile  (who / context)
      3. Score Overview   (score / confidence / tier / risk / status)
      4. Pillar Breakdown (how score is derived)
      5. Management Insight (why this result)
      6. Risk & Recommended Action (what to do)
      7. Target Rationale (is the proposed target realistic?)
      8. Audit Trail (metric-level evidence)
    """
    # ── 1. Partner Selector ────────────────────────────────────────────────
    st.subheader("合作伙伴全景 · Partner 360")
    labels = {
        item.partner_id: f"{item.partner_name} · {item.country_code} · {item.business_line}"
        for item in partners
    }
    selected_id = st.selectbox(
        "选择合作伙伴 · Select Partner",
        options=list(labels), format_func=labels.__getitem__,
    )
    partner = next(item for item in partners if item.partner_id == selected_id)
    result = evaluations[selected_id]
    policy = policies.resolve(partner)
    severity_rank = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}
    risk_level = max(
        (risk.severity.value for risk in result.risks),
        key=severity_rank.__getitem__,
        default="LOW",
    )

    # ── 2. Partner Profile ────────────────────────────────────────────────
    st.markdown("#### 📋 合作伙伴档案 · Partner Profile")
    col_p1, col_p2 = st.columns(2)
    col_p1.markdown(
        f"**{partner.partner_name}**  \n"
        f"{partner.business_line} · {partner.country_code} · {partner.partner_type.value}"
    )
    col_p2.markdown(
        f"Lifecycle: **{partner.lifecycle_stage.value}**  \n"
        f"Market Tier: **{partner.market_tier.value}**  \n"
        f"Policy: `{result.policy_id}` v{result.policy_version}"
    )

    # ── 3. Score Overview ────────────────────────────────────────────────
    st.markdown("#### 📊 评分总览 · Score Overview")
    sc1, sc2, sc3, sc4, sc5 = st.columns(5)
    sc1.metric("合作伙伴评分\nPartner Score",
                f"{result.score:.1f}" if result.score is not None else "N/A")
    sc2.metric("数据置信度\nConfidence", f"{result.confidence:.0%}")
    sc3.metric("合作伙伴等级\nPartner Tier", result.tier.title())
    sc4.metric("风险等级\nRisk Level", risk_level.title())
    sc5.metric("治理状态\nGovernance Status", result.governance_status.value.title())

    # ── 4. Pillar Breakdown ─────────────────────────────────────────────
    st.markdown("#### 🔍 维度评分拆解 · Pillar Breakdown")
    breakdown = pd.DataFrame(
        [
            {"维度 Pillar": pillar.replace("_", " ").title(), "评分 Score": score}
            for pillar, score in result.pillar_scores.items()
            if score is not None
        ]
    )
    if not breakdown.empty:
        chart = px.bar(
            breakdown,
            x="维度 Pillar",
            y="评分 Score",
            range_y=[0, 100],
            color="评分 Score",
            color_continuous_scale="RdYlGn",
            title="各维度得分 · Pillar Scores",
            text_auto=".1f",
        )
        chart.update_layout(coloraxis_showscale=False)
        st.plotly_chart(chart, use_container_width=True)

    # ── Insight mode (computed here so section 5 can use it) ─────────────
    ai_provider = OpenAIInsightProvider()
    insight_options = ["Rules-based", "AI-enhanced"] if ai_provider.available else ["Rules-based"]
    insight_mode = st.radio(
        "洞察模式 · Insight Mode", insight_options, horizontal=True,
    )
    st.caption(
        "AI Insight：已禁用 · OPENAI_API_KEY 不可用。"
        if not ai_provider.available
        else "AI Insight：可用 · 仅结构化管理摘要会发送给 AI Provider。"
    )
    insight = generate_management_insight(
        partner, result, policy,
        ai_provider if insight_mode == "AI-enhanced" else None,
    )

    # ── 5. Management Insight ────────────────────────────────────────────
    st.markdown("#### 💡 管理洞察 · Management Insight")
    st.caption(
        f"模式 Mode: **{insight.source.replace('_', ' ').title()}** · "
        f"严重程度 Severity: **{insight.severity.value}**"
    )
    with st.container(border=True):
        st.markdown("**摘要 · Executive Summary**")
        st.write(insight.executive_summary)

    with st.expander("关键驱动因素 · Key Drivers", expanded=False):
        for driver in insight.key_drivers:
            st.markdown(
                f"• **{driver.metric}** — {driver.explanation}  \n"
                f"  Current: `{driver.current_value}` · Benchmark: `{driver.benchmark}` · "
                f"Impact: `{driver.impact}`"
            )

    with st.expander("管理层关注 · Management Attention", expanded=False):
        st.write(insight.management_attention)

    with st.expander("建议下一步 · Recommended Next Step", expanded=False):
        st.write(insight.recommended_next_step)

    with st.expander("数据限制 · Data Limitations", expanded=False):
        for item in insight.data_limitations:
            st.write(f"• {item}")

    # ── 6. Risk & Recommended Action ─────────────────────────────────────
    st.markdown("#### ⚠️ 风险与行动 · Risk & Action")
    col_risk, col_action = st.columns(2)
    with col_risk:
        st.subheader("风险信号 · Risk Signals")
        if result.risks:
            _emojis = {"LOW": "✅", "MEDIUM": "⚠️", "HIGH": "🔶", "CRITICAL": "🚨"}
            for risk in result.risks:
                st.warning(
                    f"{_emojis.get(risk.severity.value, '')} **{risk.code}** "
                    f"({risk.severity.value}): {risk.message}"
                )
        else:
            st.success("✅ 当前数据未检测到 Policy Risk Signal。")
        if result.gate_codes:
            for gate in result.gate_codes:
                st.error(f"🚧 已触发 Gate：{gate}")
        st.caption("风险信号由 Policy Rule Engine 驱动，需要人工复核。")

    with col_action:
        st.subheader("管理建议 · Recommended Action")
        if result.recommended_actions:
            for action in result.recommended_actions:
                with st.container(border=True):
                    st.markdown(f"**{action.action.value}** · {action.priority.value}")
                    st.write(action.reason)
                    st.caption(
                        f"证据 Evidence: {action.evidence} · "
                        f"人工复核 Human Review: "
                        f"{'是 · Yes' if action.human_review_required else '否 · No'}"
                    )
        else:
            st.info("当前无主动管理建议。")

    # ── 7. Target Rationale ─────────────────────────────────────────────
    with st.expander("🎯 目标合理性分析 · Target Rationale", expanded=True):
        st.caption(
            "仅用于决策支持与 Target Sanity Check；系统不会制定或批准销售目标。"
        )
        target_columns = st.columns(4)
        default_target = round((partner.annual_revenue or 0) * 1.10, 2) or None
        proposed_target = target_columns[0].number_input(
            "拟议目标 · Proposed Target (USD)", min_value=0.01, value=default_target, step=10_000.0,
        )
        pipeline_value = target_columns[1].number_input(
            "销售管道金额 · Pipeline Value (USD)", min_value=0.0, value=None, step=10_000.0,
        )
        new_customer_plan = target_columns[2].number_input(
            "新客户计划 · New Customer Plan", min_value=0, value=None, step=1,
        )
        resource_label = target_columns[3].selectbox(
            "资源承诺 · Resource Commitment",
            ["Unknown", "Confirmed", "Not confirmed"],
        )
        rationale = assess_target(
            TargetRationaleInput(
                current_revenue=partner.annual_revenue,
                proposed_target=proposed_target,
                historical_growth_pct=partner.yoy_growth_pct,
                current_sell_out_pct=partner.sell_out_performance_pct,
                lifecycle_stage=partner.lifecycle_stage,
                market_capability_score=result.pillar_scores.get("MARKET_CAPABILITY"),
                pipeline_value=pipeline_value,
                new_customer_plan=new_customer_plan,
                coverage_pct=partner.geographic_coverage_pct,
                new_product_potential_pct=partner.new_product_contribution_pct,
                resource_commitment={"Confirmed": True, "Not confirmed": False}.get(resource_label),
                inventory_days=partner.inventory_days,
                ar_overdue_90d_pct=partner.ar_overdue_90d_pct,
                risk_level=RiskSeverity(risk_level),
                gate_codes=tuple(result.gate_codes),
            ),
            policy,
        )
        tm = st.columns(4)
        tm[0].metric(
            "拟议目标\nProposed Target",
            f"{rationale.proposed_target:,.0f}" if rationale.proposed_target else "N/A",
        )
        tm[1].metric(
            "所需增长\nRequired Growth",
            f"{rationale.required_growth_pct:+.1f}%"
            if rationale.required_growth_pct is not None else "N/A",
        )
        tm[2].metric("评估结论\nAssessment", rationale.assessment.value.replace("_", " ").title())
        tm[3].metric("目标置信度\nConfidence", f"{rationale.confidence:.0%}")
        tl, tr = st.columns(2)
        with tl:
            st.markdown("**支持因素 · Supporting Drivers**")
            for item in rationale.supporting_drivers:
                st.write(f"• {item}")
            st.markdown("**制约因素 · Constraining Drivers**")
            for item in rationale.constraining_drivers:
                st.write(f"• {item}")
        with tr:
            st.markdown("**必要假设 · Required Assumptions**")
            for item in (rationale.required_assumptions or []):
                st.write(f"• {item}")
            if not rationale.required_assumptions:
                st.caption("当前证据未产生额外假设。")
            st.markdown("**管理复核 · Management Review**")
            st.write(rationale.management_review)

    # ── 8. Audit Trail ───────────────────────────────────────────────────
    with st.expander("📐 指标级审计轨迹 · Metric-level Audit Trail"):
        metric_rows = [
            {"metric": metric, "observed_value": getattr(partner, metric, None),
             "normalized_score": score}
            for metric, score in result.metric_scores.items()
        ]
        if metric_rows:
            st.dataframe(pd.DataFrame(metric_rows), use_container_width=True, hide_index=True)
        else:
            st.caption("无详细指标轨迹记录。")


def render_data_quality(partners, evaluations) -> None:
    rows = []
    for partner in partners:
        result = evaluations[partner.partner_id]
        missing = [metric for metric, score in result.metric_scores.items() if score is None]
        rows.append(
            {
                "partner_id": partner.partner_id,
                "partner_name": partner.partner_name,
                "confidence": result.confidence,
                "missing_scored_metrics": ", ".join(missing) or "None",
            }
        )
    quality = pd.DataFrame(rows).sort_values("confidence")
    st.info("缺失数据会降低 Confidence，但不会被当作零分处理（NULL ≠ 0）。")
    st.dataframe(
        quality,
        use_container_width=True,
        hide_index=True,
        column_config={
            "confidence": st.column_config.ProgressColumn(min_value=0, max_value=1, format="%.0f%%")
        },
    )


def _policy_id_for_context(context: dict[str, str]) -> str:
    order = ["business_line", "lifecycle_stage", "market_tier", "partner_type", "country_code"]
    return "POL-" + "-".join(context[key] for key in order if key in context)


def render_policy_studio(manager: PolicyLifecycleManager, partners) -> None:
    """Edit isolated drafts; only explicit activation can change active scoring."""
    st.subheader("策略配置中心 · Policy Studio")
    st.caption("两层权重 · Two-level Weights · 显式继承 · Draft → Scenario → Activate · SQLite 持久化")
    st.info(
        "**Level 1 — Pillar Weight**：调整六大治理维度的重要性。  \n"
        "**Level 2 — Metric Weight**：调整每个 Pillar 内部指标的重要性。"
    )

    if partners:
        business_lines = sorted({partner.business_line for partner in partners})
        lifecycle_stages = sorted({partner.lifecycle_stage.value for partner in partners})
        market_tiers = sorted({partner.market_tier.value for partner in partners})
        partner_types = sorted({partner.partner_type.value for partner in partners})
        country_codes = sorted({partner.country_code for partner in partners})
    else:
        business_lines = list(SUPPORTED_BUSINESS_LINES)
        lifecycle_stages = [item.value for item in LifecycleStage]
        market_tiers = [item.value for item in MarketTier]
        partner_types = [item.value for item in PartnerType]
        country_codes = sorted({policy.match.get("country_code") for policy in manager.policies if policy.match.get("country_code")}) or ["PL"]

    selectors = st.columns(5)
    business_line = selectors[0].selectbox("业务线 · Business Line", business_lines)
    lifecycle_stage = selectors[1].selectbox("生命周期阶段 · Lifecycle Stage", lifecycle_stages)
    market_tier = selectors[2].selectbox("市场等级 · Market Tier", market_tiers)
    partner_type = selectors[3].selectbox("合作伙伴类型 · Partner Type", partner_types)
    country_override = selectors[4].selectbox("国家覆盖 · Country Override", ["None", *country_codes])

    context = {
        "business_line": business_line,
        "lifecycle_stage": lifecycle_stage,
        "market_tier": market_tier,
        "partner_type": partner_type,
    }
    if country_override != "None":
        context["country_code"] = country_override

    active = manager.active_repository().resolve_context(context)
    st.info(
        f"策略来源 · Policy Source：**{active.source_label}** · `{active.policy_id}` v{active.version}"
    )
    epoch = st.session_state.get("policy_editor_epoch", 0)
    editor_key = f"{active.policy_id}-{active.version}-{hash(tuple(sorted(context.items())))}-{epoch}"

    st.markdown("#### 第一层：维度权重 · Level 1 — Pillar Weights")
    pillar_values: dict[Pillar, float] = {}
    pillar_columns = st.columns(3)
    for index, pillar in enumerate(Pillar):
        pillar_values[pillar] = (
            pillar_columns[index % 3].number_input(
                pillar.value.replace("_", " ").title(),
                min_value=0.0,
                max_value=100.0,
                value=float(active.pillar_weights[pillar] * 100),
                step=1.0,
                key=f"pillar-{editor_key}-{pillar.value}",
            )
            / 100
        )
    pillar_total = sum(pillar_values.values())
    if abs(pillar_total - 1) < 1e-9:
        st.success("Pillar 权重合计 · Pillar Total：100%")
    else:
        st.error(f"Pillar 权重合计 · Pillar Total：{pillar_total:.0%} — 必须等于 100%")

    st.markdown("#### ↓ 第二层：指标权重 · Level 2 — Metric Weights（展开 Pillar）")
    metric_values = {}
    metric_totals: dict[Pillar, float] = {}
    for pillar in Pillar:
        rules = [(name, rule) for name, rule in active.metrics.items() if rule.pillar == pillar]
        with st.expander(pillar.value.replace("_", " ").title(), expanded=False):
            for name, rule in rules:
                metric_values[name] = (
                    st.number_input(
                        name.replace("_", " ").title(),
                        min_value=0.0,
                        max_value=100.0,
                        value=float(rule.weight * 100),
                        step=1.0,
                        key=f"metric-{editor_key}-{name}",
                    )
                    / 100
                )
            metric_totals[pillar] = sum(metric_values[name] for name, _ in rules)
            if abs(metric_totals[pillar] - 1) < 1e-9:
                st.success(f"{pillar.value.replace('_', ' ').title()} 指标合计 · Metric Total：100%")
            else:
                st.error(
                    f"{pillar.value.replace('_', ' ').title()} 指标合计 · Metric Total："
                    f"{metric_totals[pillar]:.0%} — 必须等于 100%"
                )

    valid_weights = abs(pillar_total - 1) < 1e-9 and all(
        abs(total - 1) < 1e-9 for total in metric_totals.values()
    )
    actor = st.text_input("操作人 · Actor", value="Felix-0521", key=f"actor-{editor_key}")
    change_reason = st.text_input(
        "修改原因 · Change Reason", placeholder="说明本次 Draft 的业务原因", key=f"reason-{editor_key}"
    )
    controls = st.columns(4)
    if controls[0].button(
        "保存为草稿 · Save as Draft",
        type="primary",
        disabled=not valid_weights or not actor.strip() or not change_reason.strip(),
    ):
        updated_metrics = {
            name: rule.model_copy(update={"weight": metric_values[name]})
            for name, rule in active.metrics.items()
        }
        target_id = (
            active.policy_id
            if active.match == context
            else _policy_id_for_context(context)
        )
        draft = manager.save_draft(
            active,
            pillar_weights=pillar_values,
            metrics=updated_metrics,
            actor=actor,
            change_reason=change_reason,
            match=context,
            policy_id=target_id,
        )
        st.session_state["selected_draft"] = (draft.policy_id, draft.version)
        st.success(f"已保存 `{draft.policy_id}` v{draft.version} 为 DRAFT；Active Score 不受影响。")

    if controls[1].button("重置修改 · Reset Changes"):
        st.session_state["policy_editor_epoch"] = epoch + 1
        st.rerun()

    selected_ref = st.session_state.get("selected_draft")
    selected_draft = manager.get(*selected_ref) if selected_ref else None
    if controls[2].button("进入模拟测试 · Test in Scenario", disabled=selected_draft is None):
        st.session_state["scenario_draft"] = selected_ref
        st.info("已选择 Draft，请在 Scenario Lab 中选择评估 Scope。")

    can_activate = selected_draft is not None and selected_draft.scenario_tested
    if controls[3].button("激活策略 · Activate Policy", disabled=not can_activate):
        manager.activate(
            selected_draft.policy_id,
            selected_draft.version,
            actor=actor,
            change_reason=change_reason,
        )
        st.session_state.pop("selected_draft", None)
        st.session_state.pop("scenario_draft", None)
        st.success("Draft 已激活；上一版 Exact-context Policy 已归档。")
        st.rerun()

    if selected_draft:
        st.caption(
            f"已选草稿 · Selected Draft：`{selected_draft.policy_id}` v{selected_draft.version} · "
            f"已完成模拟 · Scenario Tested：{'是 · Yes' if selected_draft.scenario_tested else '否 · No'}"
        )


def render_scenario_lab(
    manager: PolicyLifecycleManager,
    source_frame: pd.DataFrame,
    partners,
) -> None:
    """Compare an isolated draft with active policy across three scopes."""
    st.subheader("策略模拟实验室 · Scenario Lab")
    st.info("**基准 · Baseline = Current Active Policy**  ↔  **模拟 · Scenario = Draft Policy**")
    st.caption("Active Data 只读；Scenario Result 不会覆盖正式评价。")
    drafts = manager.drafts()
    if not drafts:
        st.warning("运行 Scenario 前，请先在 Policy Studio 创建 Draft。")
        return

    draft_refs = [(draft.policy_id, draft.version) for draft in drafts]
    preferred = st.session_state.get("scenario_draft")
    default_index = draft_refs.index(preferred) if preferred in draft_refs else len(draft_refs) - 1
    selected_ref = st.selectbox(
        "草稿策略 · Draft Policy",
        draft_refs,
        index=default_index,
        format_func=lambda ref: f"{ref[0]} v{ref[1]}",
    )
    scope = ScenarioScope(
        st.radio(
            "模拟范围 · Scope",
            [item.value for item in ScenarioScope],
            format_func=lambda value: value.replace("_", " ").title(),
            horizontal=True,
        )
    )

    partner_id = None
    filters: dict[str, str] = {}
    if scope == ScenarioScope.SINGLE_PARTNER:
        labels = {partner.partner_id: f"{partner.partner_name} · {partner.country_code}" for partner in partners}
        partner_id = st.selectbox("合作伙伴 · Partner", list(labels), format_func=labels.__getitem__)
    elif scope == ScenarioScope.SELECTED_MARKET:
        columns = st.columns(4)
        filter_options = {
            "country_code": sorted({partner.country_code for partner in partners}),
            "business_line": sorted({partner.business_line for partner in partners}),
            "market_tier": sorted({partner.market_tier.value for partner in partners}),
            "lifecycle_stage": sorted({partner.lifecycle_stage.value for partner in partners}),
        }
        for column, (field, options) in zip(columns, filter_options.items()):
            selected = column.selectbox(field.replace("_", " ").title(), ["All", *options])
            if selected != "All":
                filters[field] = selected

    if st.button("运行模拟 · Run Scenario", type="primary"):
        try:
            report = ScenarioService.run(
                source_frame,
                manager,
                draft_policy_id=selected_ref[0],
                draft_version=selected_ref[1],
                scope=scope,
                partner_id=partner_id,
                filters=filters,
            )
        except ValueError as error:
            st.error(str(error))
            return
        manager.mark_scenario_tested(*selected_ref)
        st.session_state["scenario_report"] = report
        st.session_state["selected_draft"] = selected_ref
        st.success("Scenario 已完成；Active Policy 与正式 Partner Result 未被修改。")

    report = st.session_state.get("scenario_report")
    if report is None or (report.draft_policy_id, report.draft_version) != selected_ref:
        return
    summary = report.summary
    metrics = st.columns(5)
    metrics[0].metric("平均分变化 · Average Score Change", f"{summary.average_score_change:+.2f}")
    metrics[1].metric("等级提升 · Partners Upgraded", summary.partners_upgraded)
    metrics[2].metric("等级下降 · Partners Downgraded", summary.partners_downgraded)
    positive = summary.largest_positive_impact
    negative = summary.largest_negative_impact
    metrics[3].metric(
        "最大正向影响 · Largest Positive",
        f"{positive['partner_id']} {positive['score_change']:+.2f}" if positive else "N/A",
    )
    metrics[4].metric(
        "最大负向影响 · Largest Negative",
        f"{negative['partner_id']} {negative['score_change']:+.2f}" if negative else "N/A",
    )

    comparisons = pd.DataFrame([item.model_dump() for item in report.comparisons])
    st.dataframe(comparisons, use_container_width=True, hide_index=True)
    tier_mix = pd.DataFrame(
        [
            {
                "tier": tier,
                "Baseline": summary.tier_counts_before[tier],
                "Scenario": summary.tier_counts_after[tier],
            }
            for tier in summary.tier_counts_before
        ]
    ).melt(id_vars="tier", var_name="policy", value_name="partners")
    tier_chart = px.bar(
        tier_mix,
        x="tier",
        y="partners",
        color="policy",
        barmode="group",
        title="等级变化前后对比 · Tier Count Before / After",
        text_auto=True,
    )
    st.plotly_chart(tier_chart, use_container_width=True)
    if summary.tier_migration:
        st.write("等级迁移 · Tier Migration", summary.tier_migration)


def render_audit_log(manager: PolicyLifecycleManager) -> None:
    st.subheader("持久化策略审计日志 · Persistent Policy Audit Log")
    if not manager.audit_records:
        st.info("尚未记录 Policy Lifecycle Event。")
        return
    st.dataframe(
        pd.DataFrame([record.model_dump() for record in manager.audit_records]),
        use_container_width=True,
        hide_index=True,
    )


def render_data_center(policy_repository) -> None:
    """Single gateway for templates, validation and the active analysis dataset."""
    st.subheader("数据中心 · Data Center")
    st.caption("下载模板 → 填写 → 上传 → 验证 → 确认当前数据集 → 驱动所有治理分析。")

    active_frame = st.session_state.get(ACTIVE_DATASET_FRAME_KEY)
    active_source = st.session_state.get(ACTIVE_DATASET_SOURCE_KEY)
    status_col, demo_col, clear_col = st.columns([3, 1, 1])
    if isinstance(active_frame, pd.DataFrame) and not active_frame.empty:
        status_col.success(f"当前数据集 · Active Dataset: {active_source or 'Business Data'} · {len(active_frame)} Partners")
    else:
        status_col.info("当前数据集 · Active Dataset: None")

    if demo_col.button("加载演示数据 · Load Demo Dataset", use_container_width=True):
        try:
            demo_frame = load_demo_portfolio_frame()
            set_active_dataset(demo_frame, "Synthetic Demo Dataset")
        except Exception as exc:
            st.error(f"演示数据加载失败 · Demo load failed: {exc}")
        else:
            st.session_state.pop(PENDING_DATASET_FRAME_KEY, None)
            st.session_state.pop(PENDING_DATASET_SOURCE_KEY, None)
            st.rerun()

    if clear_col.button("清空当前数据 · Clear Dataset", disabled=not isinstance(active_frame, pd.DataFrame) or active_frame.empty, use_container_width=True):
        clear_active_dataset()
        st.rerun()

    mode = st.radio(
        "操作模式 · Operation Mode",
        ["模板下载 · Template Download", "数据上传与评估 · Upload & Evaluate"],
        horizontal=True,
        index=0,
        label_visibility="collapsed",
    )

    if mode == "模板下载 · Template Download":
        st.markdown("#### 下载业务模板 · Download Business Templates")
        st.info("下载标准 Excel 模板并填写。系统不会在后台自动加载 Demo 数据。")
        template_links = [
            ("01_Partner_Master.xlsx", "合作伙伴主数据 · Partner Master"),
            ("02_Commercial_Performance.xlsx", "商业绩效 · Commercial Performance"),
            ("03_Operational_Health.xlsx", "运营健康 · Operational Health"),
            ("04_Financial_Health.xlsx", "财务健康 · Financial Health"),
            ("05_Service_Capability.xlsx", "服务能力 · Service Capability"),
            ("06_Compliance_Governance.xlsx", "合规治理 · Compliance Governance"),
            ("07_Target_Rationale.xlsx", "目标规划 · Target Rationale"),
        ]
        cols = st.columns(2)
        for idx, (fname, label) in enumerate(template_links):
            src = SYNTHETIC_DIR / fname
            with cols[idx % 2]:
                if src.exists():
                    st.download_button(label=label, data=src.read_bytes(), file_name=fname, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key=f"dl_{fname}", use_container_width=True)
                else:
                    st.warning(f"模板未找到 · Template not found: {fname}")
        with st.expander("模板填写说明 · Template Filling Guide"):
            st.markdown("""
            **核心规则 · Core rules**
            - `Partner_ID` 是七张模板的唯一关联键。
            - 百分比字段可使用 `85%`；缺失值保持为空，不按 0 处理。
            - 建议保留下载时的标准文件名，以便系统自动识别模板类型。
            - Warning 不阻塞评估；Blocking Error 必须先修正。
            """)
        return

    st.markdown("#### 上传业务数据 · Upload Business Data")
    uploaded_files = st.file_uploader(
        "上传业务模板 · Upload business templates",
        type=["xlsx", "csv"],
        accept_multiple_files=True,
        help="上传后先验证。只有点击 Confirm Active Dataset 后，其他分析页面才会切换到这批数据。",
    )

    if st.button("运行数据验证 · Run Validation", type="primary"):
        if not uploaded_files:
            st.warning("尚未上传文件。请先上传业务模板，或使用 Load Demo Dataset。")
        else:
            from io import BytesIO
            template_map = {Path(tid.value).stem: tid for tid in TemplateId}
            templates_by_id = {}
            for uploaded in uploaded_files:
                tid = template_map.get(Path(uploaded.name).stem)
                if tid is None:
                    st.warning(f"未识别模板文件 · Unrecognized template: {uploaded.name}")
                    continue
                payload = uploaded.getvalue()
                try:
                    frame = pd.read_excel(BytesIO(payload)) if uploaded.name.lower().endswith(".xlsx") else pd.read_csv(BytesIO(payload))
                except Exception as exc:
                    st.error(f"文件读取失败 · Failed to read {uploaded.name}: {exc}")
                    continue
                templates_by_id[tid] = frame

            if not templates_by_id:
                st.error("没有可识别的业务模板 · No recognized business templates were provided.")
            else:
                norm_result = normalize_excel_templates(templates_by_id)
                summary = st.columns(4)
                summary[0].metric("合作伙伴 · Partners", len(norm_result.partner_records))
                summary[1].metric("警告 · Warnings", len(norm_result.warnings))
                summary[2].metric("错误 · Errors", len(norm_result.errors))
                summary[3].metric("数据质量 · Data Quality", f"{norm_result.data_quality_score:.0%}")
                if norm_result.errors:
                    st.error("存在 Blocking Error，当前数据不能设为 Active Dataset。")
                    st.dataframe(pd.DataFrame([{"Row": item.row, "Field": item.field, "Message": item.message} for item in norm_result.errors]), hide_index=True, use_container_width=True)
                if norm_result.warnings:
                    st.warning("存在非阻塞 Warning；可以继续评估，但 Confidence 可能降低。")
                    st.dataframe(pd.DataFrame([{"Row": item.row, "Field": item.field, "Message": item.message} for item in norm_result.warnings[:50]]), hide_index=True, use_container_width=True)
                if norm_result.success and norm_result.partner_records:
                    st.session_state[PENDING_DATASET_FRAME_KEY] = _frame_from_records(norm_result.partner_records)
                    st.session_state[PENDING_DATASET_SOURCE_KEY] = "Uploaded Business Data"
                else:
                    st.session_state.pop(PENDING_DATASET_FRAME_KEY, None)
                    st.session_state.pop(PENDING_DATASET_SOURCE_KEY, None)

    pending_frame = st.session_state.get(PENDING_DATASET_FRAME_KEY)
    if isinstance(pending_frame, pd.DataFrame) and not pending_frame.empty:
        st.markdown("#### 待确认数据集 · Validated Dataset Preview")
        preview_columns = ["partner_id", "partner_name", "business_line", "country_code", "lifecycle_stage", "market_tier", "annual_revenue", "inventory_days"]
        st.dataframe(pending_frame.head(10)[preview_columns], hide_index=True, use_container_width=True)
        pending_results = evaluate_portfolio(pending_frame, policy_repository)
        metrics = st.columns(4)
        metrics[0].metric("待确认 Partners", len(pending_results))
        metrics[1].metric("平均评分 · Avg Score", f"{pending_results['score'].dropna().mean():.1f}" if not pending_results['score'].dropna().empty else "N/A")
        metrics[2].metric("高/严重风险 · High/Critical", int(pending_results["risk_level"].isin(["HIGH", "CRITICAL"]).sum()))
        metrics[3].metric("平均置信度 · Avg Confidence", f"{pending_results['confidence'].mean():.0%}")
        if st.button("确认并设为当前数据集 · Confirm Active Dataset", type="primary"):
            set_active_dataset(pending_frame, st.session_state.get(PENDING_DATASET_SOURCE_KEY, "Uploaded Business Data"))
            st.session_state.pop(PENDING_DATASET_FRAME_KEY, None)
            st.session_state.pop(PENDING_DATASET_SOURCE_KEY, None)
            st.rerun()


st.set_page_config(page_title="Adaptive Channel Governance", page_icon="◈", layout="wide")
apply_visual_theme()
st.title("自适应渠道治理与合作伙伴评分 · Adaptive Channel Governance")
st.caption("Synthetic Data · Deterministic Rules · 可解释的 Human-in-the-loop 决策支持")

if "policy_manager" not in st.session_state:
    st.session_state["policy_manager"] = PolicyLifecycleManager.from_yaml_and_sqlite(
        POLICY_PATH, DATABASE_PATH
    )
policy_manager: PolicyLifecycleManager = st.session_state["policy_manager"]
partner_store = SQLitePartnerStore(DATABASE_PATH)
policy_repository = policy_manager.active_repository()
active_dataset = st.session_state.get(ACTIVE_DATASET_FRAME_KEY)
if isinstance(active_dataset, pd.DataFrame) and not active_dataset.empty:
    source_frame = active_dataset.copy()
    partner_records = require_valid_dataframe(source_frame)
    portfolio_results = evaluate_portfolio(source_frame, policy_repository)
    evaluation_map = {partner.partner_id: evaluate_partner(partner, policy_repository) for partner in partner_records}
else:
    source_frame = pd.DataFrame()
    partner_records = []
    portfolio_results = pd.DataFrame()
    evaluation_map = {}

# B2: Final tab order — Data Center first (data input),
# then analysis views, then policy/scenario, then audit.
data_center_tab, overview_tab, partner_tab, policy_tab, scenario_tab, audit_tab = st.tabs(
    [
        "数据中心\nData Center",
        "渠道总览\nChannel Overview",
        "合作伙伴全景分析\nPartner 360",
        "策略配置中心\nPolicy Studio",
        "策略模拟实验室\nScenario Lab",
        "审计日志\nAudit Log",
    ]
)
with overview_tab:
    if partner_records:
        render_overview(portfolio_results)
    else:
        render_dataset_empty_state("Channel Overview")
with partner_tab:
    if partner_records:
        render_partner_360(partner_records, evaluation_map, policy_repository)
    else:
        render_dataset_empty_state("Partner 360")
with data_center_tab:
    render_data_center(policy_repository)
with policy_tab:
    render_policy_studio(policy_manager, partner_records)
with scenario_tab:
    if partner_records:
        render_scenario_lab(policy_manager, source_frame, partner_records)
    else:
        render_dataset_empty_state("Scenario Lab")
with audit_tab:
    render_audit_log(policy_manager)
