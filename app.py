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
from channel_governance.validation import require_valid_dataframe


POLICY_PATH = ROOT / "config" / "scoring_rules.yaml"
DATA_PATH = ROOT / "data" / "sample_partners.csv"
DATABASE_PATH = ROOT / "data" / "app.db"


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


def render_partner_management(
    store: SQLitePartnerStore, existing_partners
) -> None:
    """Create or import Partners, then reuse the existing evaluation pipeline."""
    st.subheader("Partner Management")
    st.caption(
        "New records are stored in local SQLite and evaluated by the existing "
        "Adaptive Policy, Score, Risk, Gate, Tier, Action, and Insight engines."
    )
    result = st.session_state.pop("partner_management_result", None)
    if result:
        st.success(result)

    create_tab, import_tab = st.tabs(["Create New Partner", "Partner Import"])
    with create_tab:
        with st.form("create-partner-form", clear_on_submit=True):
            first_row = st.columns(3)
            partner_name = first_row[0].text_input("Partner Name")
            country_code = first_row[1].text_input("Country (2-letter code)", max_chars=2)
            region = first_row[2].text_input("Region")
            second_row = st.columns(4)
            business_line = second_row[0].selectbox(
                "Business Line", sorted({partner.business_line for partner in existing_partners})
            )
            partner_type = PartnerType(
                second_row[1].selectbox("Partner Type", [item.value for item in PartnerType])
            )
            lifecycle_stage = LifecycleStage(
                second_row[2].selectbox("Lifecycle Stage", [item.value for item in LifecycleStage])
            )
            market_tier = MarketTier(
                second_row[3].selectbox("Market Tier", [item.value for item in MarketTier])
            )
            submitted = st.form_submit_button("Create Partner", type="primary")
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
                st.error(f"Create failed: {error}")
            else:
                st.session_state["partner_management_result"] = (
                    f"✓ Partner {partner.partner_name} created with ID {partner.partner_id}. "
                    "Dashboard and Partner 360 have been refreshed."
                )
                st.rerun()

    with import_tab:
        st.info(
            "CSV is supported by the current dependency baseline. For Excel, save the "
            "worksheet as CSV before upload. Required fields: partner_name, country_code, "
            "region, business_line, partner_type, lifecycle_stage, market_tier."
        )
        uploaded = st.file_uploader("Upload Partner CSV", type=["csv"])
        if uploaded is not None:
            try:
                upload_frame = pd.read_csv(uploaded)
            except Exception as error:
                st.error(f"Upload could not be read: {error}")
            else:
                analysis = analyze_partner_import(upload_frame, list(existing_partners))
                st.markdown("#### Preview")
                st.dataframe(analysis.preview, use_container_width=True, hide_index=True)
                st.markdown("#### Validation")
                if analysis.issues:
                    st.error(f"⚠ {len(analysis.issues)} validation issue(s) found.")
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
                    st.success(f"✓ {len(analysis.records)} Partner row(s) passed validation.")
                if analysis.warnings:
                    st.warning(f"⚠ Missing Data / Data Quality: {len(analysis.warnings)} warning(s)")
                    for warning in analysis.warnings:
                        st.caption(warning)
                if st.button(
                    "Confirm Import",
                    type="primary",
                    disabled=not analysis.can_import,
                ):
                    try:
                        imported = import_partners(store, analysis)
                    except ValueError as error:
                        st.error(f"Import failed: {error}")
                    else:
                        st.session_state["partner_management_result"] = (
                            f"✓ Imported Partners: {imported}. Dashboard and Partner 360 refreshed."
                        )
                        st.rerun()


def render_overview(results: pd.DataFrame) -> None:
    """Render an executive portfolio summary without domain rules in the UI."""
    scored = results["score"].dropna()
    high_risk = int(results["risk_level"].isin(["HIGH", "CRITICAL"]).sum())
    review_required = int(results["governance_status"].isin(["REVIEW", "HOLD"]).sum())
    columns = st.columns(4)
    columns[0].metric("Total Partners", len(results))
    columns[1].metric("Average Partner Score", f"{scored.mean():.1f}" if not scored.empty else "N/A")
    columns[2].metric("High / Critical Risk", high_risk)
    columns[3].metric("Review Required", review_required)

    st.markdown("#### Portfolio Governance View")
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
        labels={"score": "Partner score", "partner_name": "Partner"},
        title="Partner score and governance status",
        hover_data=["policy_id", "confidence", "tier", "risk_codes"],
    )
    score_chart.update_layout(legend_title_text="Status", height=460)
    st.plotly_chart(score_chart, use_container_width=True)

    tier_counts = results["tier"].value_counts().rename_axis("tier").reset_index(name="partners")
    tier_chart = px.bar(
        tier_counts,
        x="tier",
        y="partners",
        color="tier",
        title="Portfolio tier mix",
        text_auto=True,
    )
    tier_chart.update_layout(showlegend=False, height=330)
    risk_counts = results["risk_level"].value_counts().rename_axis("risk").reset_index(name="partners")
    risk_chart = px.bar(
        risk_counts, x="risk", y="partners", color="risk",
        title="Risk Distribution", text_auto=True,
        color_discrete_map={"LOW": "#2E7D32", "MEDIUM": "#ED9B25", "HIGH": "#D66B2C", "CRITICAL": "#B3261E"},
    )
    risk_chart.update_layout(showlegend=False, height=330)
    lifecycle_counts = results["lifecycle_stage"].value_counts().rename_axis("lifecycle").reset_index(name="partners")
    lifecycle_chart = px.bar(
        lifecycle_counts, x="lifecycle", y="partners", color="lifecycle",
        title="Lifecycle Distribution", text_auto=True,
    )
    lifecycle_chart.update_layout(showlegend=False, height=330)
    chart_columns = st.columns(3)
    chart_columns[0].plotly_chart(tier_chart, use_container_width=True)
    chart_columns[1].plotly_chart(risk_chart, use_container_width=True)
    chart_columns[2].plotly_chart(lifecycle_chart, use_container_width=True)

    st.subheader("Governance worklist")
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
    """Explain one evaluation from context through recommended human action."""
    labels = {
        item.partner_id: f"{item.partner_name} · {item.country_code} · {item.business_line}"
        for item in partners
    }
    selected_id = st.selectbox("Partner", options=list(labels), format_func=labels.__getitem__)
    partner = next(item for item in partners if item.partner_id == selected_id)
    result = evaluations[selected_id]
    policy = policies.resolve(partner)
    severity_rank = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}
    risk_level = max(
        (risk.severity.value for risk in result.risks),
        key=severity_rank.__getitem__,
        default="LOW",
    )
    ai_provider = OpenAIInsightProvider()
    insight_options = ["Rules-based", "AI-enhanced"] if ai_provider.available else ["Rules-based"]
    insight_mode = st.radio("Insight Mode", insight_options, horizontal=True)
    if ai_provider.available:
        st.caption(
            "AI Insight: Available · Only structured management summaries are sent to the "
            "configured AI provider. Raw uploaded datasets are not sent."
        )
    else:
        st.caption("AI Insight: Disabled · OPENAI_API_KEY or the optional AI dependency is unavailable.")
    insight = generate_management_insight(
        partner, result, policy, ai_provider if insight_mode == "AI-enhanced" else None
    )

    st.info(
        f"**Context** · {partner.business_line} · {partner.country_code} · "
        f"{partner.lifecycle_stage.value} · {partner.market_tier.value} · "
        f"{partner.partner_type.value}  \n**Policy Source** · {result.policy_source} · "
        f"`{result.policy_id}` v{result.policy_version}"
    )
    columns = st.columns(5)
    columns[0].metric("Partner Score", f"{result.score:.1f}" if result.score is not None else "N/A")
    columns[1].metric("Confidence", f"{result.confidence:.0%}")
    columns[2].metric("Partner Tier", result.tier.title())
    columns[3].metric("Risk", risk_level.title())
    columns[4].metric("Governance Status", result.governance_status.value.title())

    breakdown = pd.DataFrame(
        [
            {"pillar": pillar.replace("_", " ").title(), "score": score}
            for pillar, score in result.pillar_scores.items()
            if score is not None
        ]
    )
    chart = px.bar(
        breakdown,
        x="pillar",
        y="score",
        range_y=[0, 100],
        color="score",
        color_continuous_scale="RdYlGn",
        title="Pillar Breakdown",
        text_auto=".1f",
    )
    chart.update_layout(coloraxis_showscale=False)
    st.plotly_chart(chart, use_container_width=True)

    st.subheader("Management Insight")
    st.caption(f"{insight.source.replace('_', ' ').title()} · Severity: {insight.severity.value}")
    st.markdown("**Executive Summary**")
    st.write(insight.executive_summary)
    st.markdown("**Key Drivers**")
    for driver in insight.key_drivers:
        st.write(
            f"• {driver.metric}: {driver.explanation} "
            f"(Current: {driver.current_value}; Benchmark: {driver.benchmark}; Impact: {driver.impact})"
        )
    st.markdown("**Management Attention**")
    st.write(insight.management_attention)
    st.markdown("**Recommended Next Step**")
    st.write(insight.recommended_next_step)
    st.markdown("**Data Confidence**")
    st.write(" ".join(insight.data_limitations))

    action_left, action_right = st.columns(2)
    with action_left:
        st.subheader("Risk & Gate Signals")
        if result.risks:
            for risk in result.risks:
                st.warning(f"{risk.severity.value} · {risk.code}: {risk.message}")
        else:
            st.success("No policy risk signal detected in the supplied observations.")
        for gate in result.gate_codes:
            st.error(f"Gate triggered: {gate}")
    with action_right:
        st.subheader("Recommended Action")
        for action in result.recommended_actions:
            with st.container(border=True):
                st.markdown(f"**{action.action.value} · {action.priority.value}**")
                st.write(action.reason)
                st.caption(
                    f"Evidence: {action.evidence} · Human Review Required: "
                    f"{'Yes' if action.human_review_required else 'No'}"
                )

    with st.expander("Target Rationale", expanded=True):
        st.caption(
            "Decision-support sanity check only · The system does not set or approve sales targets."
        )
        target_columns = st.columns(4)
        default_target = round((partner.annual_revenue or 0) * 1.10, 2) or None
        proposed_target = target_columns[0].number_input(
            "Proposed Target", min_value=0.01, value=default_target, step=10_000.0
        )
        pipeline_value = target_columns[1].number_input(
            "Pipeline Value", min_value=0.0, value=None, step=10_000.0
        )
        new_customer_plan = target_columns[2].number_input(
            "New Customer Plan", min_value=0, value=None, step=1
        )
        resource_label = target_columns[3].selectbox(
            "Resource Commitment", ["Unknown", "Confirmed", "Not confirmed"]
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
        metrics = st.columns(4)
        metrics[0].metric("Proposed Target", f"{rationale.proposed_target:,.0f}" if rationale.proposed_target else "N/A")
        metrics[1].metric("Required Growth", f"{rationale.required_growth_pct:+.1f}%" if rationale.required_growth_pct is not None else "N/A")
        metrics[2].metric("Assessment", rationale.assessment.value.replace("_", " ").title())
        metrics[3].metric("Confidence", f"{rationale.confidence:.0%}")
        target_left, target_right = st.columns(2)
        with target_left:
            st.markdown("**Supporting Drivers**")
            for item in rationale.supporting_drivers:
                st.write(f"• {item}")
            st.markdown("**Constraining Drivers**")
            for item in rationale.constraining_drivers:
                st.write(f"• {item}")
        with target_right:
            st.markdown("**Required Assumptions**")
            if rationale.required_assumptions:
                for item in rationale.required_assumptions:
                    st.write(f"• {item}")
            else:
                st.write("No additional assumption was generated from the supplied evidence.")
            st.markdown("**Management Review**")
            st.write(rationale.management_review)

    with st.expander("Metric-level audit trail"):
        metric_rows = [
            {
                "metric": metric,
                "observed_value": getattr(partner, metric),
                "normalized_score": score,
            }
            for metric, score in result.metric_scores.items()
        ]
        st.dataframe(pd.DataFrame(metric_rows), use_container_width=True, hide_index=True)


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
    st.info("Missing observations reduce confidence; they are never scored as zero.")
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
    st.subheader("Policy Studio")
    st.caption("Two-level weights · explicit inheritance · Draft → Scenario → Activate · SQLite persisted")
    st.info(
        "**Level 1 — Pillar Weight** controls the importance of six governance dimensions.  \n"
        "**Level 2 — Metric Weight** controls the indicators inside each Pillar."
    )

    business_lines = sorted({partner.business_line for partner in partners})
    lifecycle_stages = sorted({partner.lifecycle_stage.value for partner in partners})
    market_tiers = sorted({partner.market_tier.value for partner in partners})
    partner_types = sorted({partner.partner_type.value for partner in partners})
    country_codes = sorted({partner.country_code for partner in partners})

    selectors = st.columns(5)
    business_line = selectors[0].selectbox("Business Line", business_lines)
    lifecycle_stage = selectors[1].selectbox("Lifecycle Stage", lifecycle_stages)
    market_tier = selectors[2].selectbox("Market Tier", market_tiers)
    partner_type = selectors[3].selectbox("Partner Type", partner_types)
    country_override = selectors[4].selectbox("Country Override", ["None", *country_codes])

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
        f"Policy Source: **{active.source_label}** · `{active.policy_id}` v{active.version}"
    )
    epoch = st.session_state.get("policy_editor_epoch", 0)
    editor_key = f"{active.policy_id}-{active.version}-{hash(tuple(sorted(context.items())))}-{epoch}"

    st.markdown("#### Level 1 — Pillar Weights")
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
        st.success("Pillar Total: 100%")
    else:
        st.error(f"Pillar Total: {pillar_total:.0%} — must equal 100%")

    st.markdown("#### ↓ Level 2 — Metric Weights (expand each Pillar)")
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
                st.success(f"{pillar.value.replace('_', ' ').title()} Metric Total: 100%")
            else:
                st.error(
                    f"{pillar.value.replace('_', ' ').title()} Metric Total: "
                    f"{metric_totals[pillar]:.0%} — must equal 100%"
                )

    valid_weights = abs(pillar_total - 1) < 1e-9 and all(
        abs(total - 1) < 1e-9 for total in metric_totals.values()
    )
    actor = st.text_input("Actor", value="Felix-0521", key=f"actor-{editor_key}")
    change_reason = st.text_input(
        "Change reason", placeholder="Explain the business reason for this draft", key=f"reason-{editor_key}"
    )
    controls = st.columns(4)
    if controls[0].button(
        "Save as Draft",
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
        st.success(f"Saved `{draft.policy_id}` v{draft.version} as DRAFT. Active scores are unchanged.")

    if controls[1].button("Reset Changes"):
        st.session_state["policy_editor_epoch"] = epoch + 1
        st.rerun()

    selected_ref = st.session_state.get("selected_draft")
    selected_draft = manager.get(*selected_ref) if selected_ref else None
    if controls[2].button("Test in Scenario", disabled=selected_draft is None):
        st.session_state["scenario_draft"] = selected_ref
        st.info("Draft selected. Open Scenario Lab to choose the evaluation scope.")

    can_activate = selected_draft is not None and selected_draft.scenario_tested
    if controls[3].button("Activate Policy", disabled=not can_activate):
        manager.activate(
            selected_draft.policy_id,
            selected_draft.version,
            actor=actor,
            change_reason=change_reason,
        )
        st.session_state.pop("selected_draft", None)
        st.session_state.pop("scenario_draft", None)
        st.success("Draft activated; the previous exact-context policy was archived.")
        st.rerun()

    if selected_draft:
        st.caption(
            f"Selected Draft: `{selected_draft.policy_id}` v{selected_draft.version} · "
            f"Scenario Tested: {'Yes' if selected_draft.scenario_tested else 'No'}"
        )


def render_scenario_lab(
    manager: PolicyLifecycleManager,
    source_frame: pd.DataFrame,
    partners,
) -> None:
    """Compare an isolated draft with active policy across three scopes."""
    st.subheader("Scenario Lab")
    st.info("**Baseline = Current Active Policy**  ↔  **Scenario = Draft Policy**")
    st.caption("Active data is read-only. Scenario results never overwrite official evaluations.")
    drafts = manager.drafts()
    if not drafts:
        st.warning("Create a Draft in Policy Studio before running a scenario.")
        return

    draft_refs = [(draft.policy_id, draft.version) for draft in drafts]
    preferred = st.session_state.get("scenario_draft")
    default_index = draft_refs.index(preferred) if preferred in draft_refs else len(draft_refs) - 1
    selected_ref = st.selectbox(
        "Draft Policy",
        draft_refs,
        index=default_index,
        format_func=lambda ref: f"{ref[0]} v{ref[1]}",
    )
    scope = ScenarioScope(
        st.radio(
            "Scope",
            [item.value for item in ScenarioScope],
            format_func=lambda value: value.replace("_", " ").title(),
            horizontal=True,
        )
    )

    partner_id = None
    filters: dict[str, str] = {}
    if scope == ScenarioScope.SINGLE_PARTNER:
        labels = {partner.partner_id: f"{partner.partner_name} · {partner.country_code}" for partner in partners}
        partner_id = st.selectbox("Partner", list(labels), format_func=labels.__getitem__)
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

    if st.button("Run Scenario", type="primary"):
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
        st.success("Scenario completed. Active Policy and official partner results were not modified.")

    report = st.session_state.get("scenario_report")
    if report is None or (report.draft_policy_id, report.draft_version) != selected_ref:
        return
    summary = report.summary
    metrics = st.columns(5)
    metrics[0].metric("Average Score Change", f"{summary.average_score_change:+.2f}")
    metrics[1].metric("Partners Upgraded", summary.partners_upgraded)
    metrics[2].metric("Partners Downgraded", summary.partners_downgraded)
    positive = summary.largest_positive_impact
    negative = summary.largest_negative_impact
    metrics[3].metric(
        "Largest Positive",
        f"{positive['partner_id']} {positive['score_change']:+.2f}" if positive else "N/A",
    )
    metrics[4].metric(
        "Largest Negative",
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
        title="Tier count before / after",
        text_auto=True,
    )
    st.plotly_chart(tier_chart, use_container_width=True)
    if summary.tier_migration:
        st.write("Tier Migration", summary.tier_migration)


def render_audit_log(manager: PolicyLifecycleManager) -> None:
    st.subheader("Persistent Policy Audit Log")
    if not manager.audit_records:
        st.info("No policy lifecycle event has been recorded yet.")
        return
    st.dataframe(
        pd.DataFrame([record.model_dump() for record in manager.audit_records]),
        use_container_width=True,
        hide_index=True,
    )


st.set_page_config(page_title="Adaptive Channel Governance", page_icon="◈", layout="wide")
st.title("Adaptive Channel Governance")
st.caption("Synthetic data · deterministic rules · explainable human decision support")

if "policy_manager" not in st.session_state:
    st.session_state["policy_manager"] = PolicyLifecycleManager.from_yaml_and_sqlite(
        POLICY_PATH, DATABASE_PATH
    )
policy_manager: PolicyLifecycleManager = st.session_state["policy_manager"]
partner_store = SQLitePartnerStore(DATABASE_PATH)
policy_repository = policy_manager.active_repository()
source_frame = load_partner_data(partner_store)
partner_records = require_valid_dataframe(source_frame)
portfolio_results = evaluate_portfolio(source_frame, policy_repository)
evaluation_map = {
    partner.partner_id: evaluate_partner(partner, policy_repository) for partner in partner_records
}

overview_tab, management_tab, partner_tab, quality_tab, policy_tab, scenario_tab, audit_tab = st.tabs(
    [
        "Executive overview",
        "Partner Management",
        "Partner 360",
        "Data quality",
        "Policy Studio",
        "Scenario Lab",
        "Audit Log",
    ]
)
with overview_tab:
    render_overview(portfolio_results)
with management_tab:
    render_partner_management(partner_store, partner_records)
with partner_tab:
    render_partner_360(partner_records, evaluation_map, policy_repository)
with quality_tab:
    render_data_quality(partner_records, evaluation_map)
with policy_tab:
    render_policy_studio(policy_manager, partner_records)
with scenario_tab:
    render_scenario_lab(policy_manager, source_frame, partner_records)
with audit_tab:
    render_audit_log(policy_manager)
