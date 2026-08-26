"""Presentation-only visual system for the Streamlit prototype.

The theme provides a clean, restrained enterprise visual system with
clear hierarchy, comfortable spacing, neutral surfaces and a focused accent.
It changes presentation only and never touches governance or scoring behavior.
"""

import streamlit as st


def apply_visual_theme() -> None:
    """Apply typography, spacing, surfaces and component styling."""
    st.markdown(
        """
        <style>
        :root {
          --ui-bg: #f7f7f7;
          --ui-surface: #ffffff;
          --ui-soft: #f2f2f2;
          --ui-text: #191919;
          --ui-text-2: #5f5f5f;
          --ui-muted: #8a8a8a;
          --ui-line: #e8e8e8;
          --ui-accent: #ff6900;
          --ui-radius-xl: 20px;
          --ui-radius-lg: 16px;
          --ui-radius-md: 12px;
        }

        html, body, [data-testid="stAppViewContainer"], [data-testid="stSidebar"] {
          font-family: "Inter", "SF Pro Display", "Segoe UI",
            "PingFang SC", "Microsoft YaHei", Arial, sans-serif;
        }

        [data-testid="stAppViewContainer"] {
          background: var(--ui-bg);
          color: var(--ui-text);
        }

        [data-testid="stHeader"] {
          background: rgba(247,247,247,.86);
          backdrop-filter: blur(18px);
          -webkit-backdrop-filter: blur(18px);
        }

        [data-testid="stSidebar"] {
          background: #f1f1f1;
          border-right: 1px solid var(--ui-line);
        }

        .block-container {
          max-width: 1480px;
          padding-top: 34px;
          padding-bottom: 64px;
          padding-left: clamp(20px, 3.2vw, 52px);
          padding-right: clamp(20px, 3.2vw, 52px);
        }

        h1, h2, h3, h4, h5, h6 {
          color: var(--ui-text);
          letter-spacing: -0.02em;
        }

        h1 {
          font-size: clamp(31px, 2.5vw, 39px) !important;
          line-height: 1.16 !important;
          font-weight: 650 !important;
          letter-spacing: -0.035em !important;
          margin: 2px 0 8px 0 !important;
        }

        h1::before {
          content: "CHANNEL GOVERNANCE / DECISION SUPPORT";
          display: block;
          color: var(--ui-accent);
          font-size: 11px;
          line-height: 1.4;
          font-weight: 700;
          letter-spacing: .13em;
          margin-bottom: 10px;
        }

        h2 {
          font-size: 24px !important;
          line-height: 1.28 !important;
          font-weight: 620 !important;
          margin-top: 24px !important;
          margin-bottom: 12px !important;
        }

        h3 {
          font-size: 18px !important;
          line-height: 1.4 !important;
          font-weight: 620 !important;
          margin-top: 20px !important;
          margin-bottom: 10px !important;
        }

        h4, h5, h6 {
          font-size: 15px !important;
          line-height: 1.45 !important;
          font-weight: 620 !important;
        }

        p, li, label {
          font-size: 14px;
          line-height: 1.62;
        }

        [data-testid="stCaptionContainer"],
        [data-testid="stCaptionContainer"] p {
          color: var(--ui-muted) !important;
          font-size: 12.5px !important;
          line-height: 1.55 !important;
          margin-bottom: 10px !important;
        }

        div[data-baseweb="tab-list"] {
          gap: 4px;
          background: var(--ui-surface);
          border: 1px solid var(--ui-line);
          border-radius: var(--ui-radius-lg);
          padding: 5px;
          margin-top: 18px;
          margin-bottom: 20px;
          box-shadow: 0 1px 2px rgba(0,0,0,.02);
        }

        button[data-baseweb="tab"] {
          min-height: 48px;
          border-radius: 11px;
          padding: 6px 15px;
          color: var(--ui-text-2);
          font-size: 12.5px;
          font-weight: 560;
        }

        button[data-baseweb="tab"] p {
          white-space: pre-line !important;
          line-height: 1.24 !important;
          text-align: left;
        }

        button[data-baseweb="tab"][aria-selected="true"] {
          background: var(--ui-soft);
          color: var(--ui-text);
          font-weight: 650;
        }

        button[data-baseweb="tab"][aria-selected="true"] p {
          color: var(--ui-text) !important;
        }

        [data-testid="stMetric"] {
          background: var(--ui-surface);
          border: 1px solid var(--ui-line);
          border-radius: var(--ui-radius-lg);
          padding: 17px 18px 16px;
          min-height: 104px;
          box-shadow: 0 1px 2px rgba(0,0,0,.018);
        }

        [data-testid="stMetricLabel"],
        [data-testid="stMetricLabel"] p {
          color: var(--ui-muted) !important;
          font-size: 12.5px !important;
          line-height: 1.4 !important;
          font-weight: 520 !important;
        }

        [data-testid="stMetricValue"],
        [data-testid="stMetricValue"] div {
          color: var(--ui-text) !important;
          font-size: 27px !important;
          line-height: 1.25 !important;
          font-weight: 650 !important;
          letter-spacing: -0.025em !important;
        }

        .stButton > button,
        .stDownloadButton > button,
        button[data-testid^="stBaseButton"] {
          min-height: 42px;
          border-radius: 999px !important;
          padding: 0 20px !important;
          border: 1px solid #dddddd;
          background: var(--ui-surface);
          color: var(--ui-text);
          font-size: 13px;
          font-weight: 620;
          box-shadow: none;
          transition: border-color 120ms ease, background 120ms ease;
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover,
        button[data-testid^="stBaseButton"]:hover {
          border-color: #c8c8c8;
          background: #fafafa;
        }

        button[data-testid="stBaseButton-primary"],
        .stButton > button[kind="primary"] {
          background: var(--ui-text) !important;
          color: #ffffff !important;
          border-color: var(--ui-text) !important;
        }

        button[data-testid="stBaseButton-primary"]:hover,
        .stButton > button[kind="primary"]:hover {
          background: #303030 !important;
          border-color: #303030 !important;
        }

        [data-baseweb="input"] > div,
        [data-baseweb="select"] > div,
        [data-baseweb="textarea"] > div {
          min-height: 44px;
          border-radius: var(--ui-radius-md) !important;
          border-color: var(--ui-line) !important;
          background: var(--ui-surface) !important;
          box-shadow: none !important;
        }

        [data-baseweb="input"] > div:focus-within,
        [data-baseweb="select"] > div:focus-within,
        [data-baseweb="textarea"] > div:focus-within {
          border-color: rgba(255,105,0,.72) !important;
          box-shadow: 0 0 0 3px rgba(255,105,0,.08) !important;
        }

        [data-testid="stFileUploader"] section {
          border: 1px dashed #d7d7d7;
          border-radius: var(--ui-radius-lg);
          background: rgba(255,255,255,.72);
          padding: 18px;
        }

        [data-testid="stAlert"] {
          border-radius: var(--ui-radius-md);
          border-width: 1px;
          box-shadow: none;
        }

        [data-testid="stExpander"],
        [data-testid="stForm"] {
          background: var(--ui-surface);
          border: 1px solid var(--ui-line) !important;
          border-radius: var(--ui-radius-lg) !important;
          box-shadow: none;
        }

        [data-testid="stForm"] {
          padding: 20px;
        }

        [data-testid="stDataFrame"] {
          border: 1px solid var(--ui-line);
          border-radius: var(--ui-radius-lg);
          overflow: hidden;
          background: var(--ui-surface);
        }

        [data-testid="stPlotlyChart"] {
          background: var(--ui-surface);
          border: 1px solid var(--ui-line);
          border-radius: var(--ui-radius-lg);
          padding: 8px;
        }

        hr { border-color: var(--ui-line) !important; }

        a {
          color: var(--ui-text);
          text-decoration-color: rgba(255,105,0,.55);
          text-underline-offset: 3px;
        }

        @media (max-width: 900px) {
          .block-container {
            padding-top: 22px;
            padding-left: 18px;
            padding-right: 18px;
          }
          div[data-baseweb="tab-list"] {
            overflow-x: auto;
            flex-wrap: nowrap;
          }
          [data-testid="stMetric"] { min-height: 96px; }
        }

        /* Preserve Streamlit Material Symbol glyphs. */
        [data-testid="stIconMaterial"],
        [data-testid="stIconMaterial"] span,
        .material-symbols-rounded,
        .material-icons {
          font-family: "Material Symbols Rounded", "Material Icons" !important;
          font-weight: normal !important;
          font-style: normal !important;
          letter-spacing: normal !important;
          text-transform: none !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
