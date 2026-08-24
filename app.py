"""Streamlit presentation layer for the deterministic governance engines."""

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from channel_governance.evaluation import evaluate_partner, evaluate_portfolio
from channel_governance.policy import PolicyRepository
from channel_governance.validation import require_valid_dataframe


ROOT = Path(__file__).parent
POLICY_PATH = ROOT / "config" / "scoring_rules.yaml"
DATA_PATH = ROOT / "data" / "sample_partners.csv"


@st.cache_data
def load_demo_data() -> pd.DataFrame:
    """Load the repository's synthetic demonstration data."""
    return pd.read_csv(DATA_PATH)


def render_overview(results: pd.DataFrame) -> None:
    """Render an executive portfolio summary without domain rules in the UI."""
    scored = results["score"].dropna()
    columns = st.columns(4)
    columns[0].metric("Synthetic partners", len(results))
    columns[1].metric("Average score", f"{scored.mean():.1f}" if not scored.empty else "N/A")
    columns[2].metric("Average confidence", f"{results['confidence'].mean():.0%}")
    columns[3].metric(
        "Review / Hold",
        int(results["governance_status"].isin(["REVIEW", "HOLD"]).sum()),
    )

    left, right = st.columns((2, 1))
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
    left.plotly_chart(score_chart, use_container_width=True)

    tier_counts = results["tier"].value_counts().rename_axis("tier").reset_index(name="partners")
    tier_chart = px.bar(
        tier_counts,
        x="tier",
        y="partners",
        color="tier",
        title="Portfolio tier mix",
        text_auto=True,
    )
    tier_chart.update_layout(showlegend=False, height=460)
    right.plotly_chart(tier_chart, use_container_width=True)

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


def render_partner_360(partners, evaluations) -> None:
    """Explain one evaluation from context through recommended human action."""
    labels = {
        item.partner_id: f"{item.partner_name} · {item.country_code} · {item.business_line}"
        for item in partners
    }
    selected_id = st.selectbox("Partner", options=list(labels), format_func=labels.__getitem__)
    partner = next(item for item in partners if item.partner_id == selected_id)
    result = evaluations[selected_id]

    st.caption(
        f"Policy {result.policy_id} · {partner.lifecycle_stage.value} · "
        f"{partner.partner_type.value}"
    )
    columns = st.columns(4)
    columns[0].metric("Score", f"{result.score:.1f}" if result.score is not None else "N/A")
    columns[1].metric("Confidence", f"{result.confidence:.0%}")
    columns[2].metric("Tier", result.tier.title())
    columns[3].metric("Governance status", result.governance_status.value.title())

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
        title="Explainable pillar score breakdown",
        text_auto=".1f",
    )
    chart.update_layout(coloraxis_showscale=False)
    st.plotly_chart(chart, use_container_width=True)

    left, right = st.columns(2)
    with left:
        st.subheader("Risk and gate signals")
        if result.risks:
            for risk in result.risks:
                st.warning(f"{risk.severity.value} · {risk.code}: {risk.message}")
        else:
            st.success("No policy risk signal detected in the supplied observations.")
        for gate in result.gate_codes:
            st.error(f"Gate triggered: {gate}")
    with right:
        st.subheader("Recommended human actions")
        for action in result.recommendations:
            st.write(f"- {action}")

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


st.set_page_config(page_title="Adaptive Channel Governance", page_icon="◈", layout="wide")
st.title("Adaptive Channel Governance")
st.caption("Synthetic data · deterministic rules · explainable human decision support")

policy_repository = PolicyRepository.from_yaml(POLICY_PATH)
source_frame = load_demo_data()
partner_records = require_valid_dataframe(source_frame)
portfolio_results = evaluate_portfolio(source_frame, policy_repository)
evaluation_map = {
    partner.partner_id: evaluate_partner(partner, policy_repository) for partner in partner_records
}

overview_tab, partner_tab, quality_tab = st.tabs(
    ["Executive overview", "Partner 360", "Data quality"]
)
with overview_tab:
    render_overview(portfolio_results)
with partner_tab:
    render_partner_360(partner_records, evaluation_map)
with quality_tab:
    render_data_quality(partner_records, evaluation_map)

