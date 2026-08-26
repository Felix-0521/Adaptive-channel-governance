from pathlib import Path
import re

APP = Path("app.py")
THEME = Path("src/channel_governance/ui_theme.py")
text = APP.read_text(encoding="utf-8")

constants_anchor = 'SYNTHETIC_DIR = ROOT / "data" / "synthetic"\n'
constants = '''SYNTHETIC_DIR = ROOT / "data" / "synthetic"\nSUPPORTED_BUSINESS_LINES = (\n    "AGRICULTURE", "GEOSPATIAL_SURVEYING", "LANDSCAPING", "CONSTRUCTION", "FACILITY",\n)\nACTIVE_DATASET_FRAME_KEY = "active_dataset_frame"\nACTIVE_DATASET_SOURCE_KEY = "active_dataset_source"\nPENDING_DATASET_FRAME_KEY = "pending_dataset_frame"\nPENDING_DATASET_SOURCE_KEY = "pending_dataset_source"\n'''
if "ACTIVE_DATASET_FRAME_KEY" not in text:
    if constants_anchor not in text:
        raise RuntimeError("constants anchor missing")
    text = text.replace(constants_anchor, constants, 1)

helper_anchor = "\n\ndef render_partner_management(\n"
helpers = '''\n\ndef _frame_from_records(records) -> pd.DataFrame:\n    return pd.DataFrame([record.model_dump(mode="json") for record in records])\n\n\n@st.cache_data\ndef load_demo_portfolio_frame() -> pd.DataFrame:\n    templates_by_id = {}\n    for tid in TemplateId:\n        path = SYNTHETIC_DIR / f"{tid.value}.xlsx"\n        if path.exists():\n            templates_by_id[tid] = pd.read_excel(path)\n    result = normalize_excel_templates(templates_by_id)\n    if not result.success or not result.partner_records:\n        details = "; ".join(issue.message for issue in result.errors[:5])\n        raise ValueError(f"Demo dataset failed normalization: {details or 'no partner records'}")\n    return _frame_from_records(result.partner_records)\n\n\ndef set_active_dataset(frame: pd.DataFrame, source: str) -> None:\n    require_valid_dataframe(frame)\n    st.session_state[ACTIVE_DATASET_FRAME_KEY] = frame.copy()\n    st.session_state[ACTIVE_DATASET_SOURCE_KEY] = source\n\n\ndef clear_active_dataset() -> None:\n    for key in (ACTIVE_DATASET_FRAME_KEY, ACTIVE_DATASET_SOURCE_KEY, PENDING_DATASET_FRAME_KEY, PENDING_DATASET_SOURCE_KEY):\n        st.session_state.pop(key, None)\n\n\ndef render_dataset_empty_state(feature_name: str) -> None:\n    st.info(\n        f"尚未加载业务数据 · No active dataset for {feature_name}. "\n        "请前往 Data Center 上传业务模板，或手动加载 Synthetic Demo Dataset。"\n    )\n\n\ndef render_partner_management(\n'''
if "_frame_from_records" not in text:
    if helper_anchor not in text:
        raise RuntimeError("helper anchor missing")
    text = text.replace(helper_anchor, helpers, 1)

old_options = '''    business_lines = sorted({partner.business_line for partner in partners})\n    lifecycle_stages = sorted({partner.lifecycle_stage.value for partner in partners})\n    market_tiers = sorted({partner.market_tier.value for partner in partners})\n    partner_types = sorted({partner.partner_type.value for partner in partners})\n    country_codes = sorted({partner.country_code for partner in partners})\n'''
new_options = '''    if partners:\n        business_lines = sorted({partner.business_line for partner in partners})\n        lifecycle_stages = sorted({partner.lifecycle_stage.value for partner in partners})\n        market_tiers = sorted({partner.market_tier.value for partner in partners})\n        partner_types = sorted({partner.partner_type.value for partner in partners})\n        country_codes = sorted({partner.country_code for partner in partners})\n    else:\n        business_lines = list(SUPPORTED_BUSINESS_LINES)\n        lifecycle_stages = [item.value for item in LifecycleStage]\n        market_tiers = [item.value for item in MarketTier]\n        partner_types = [item.value for item in PartnerType]\n        country_codes = sorted({policy.match.get("country_code") for policy in manager.policies if policy.match.get("country_code")}) or ["PL"]\n'''
if old_options in text:
    text = text.replace(old_options, new_options, 1)

new_data_center = r'''def render_data_center(policy_repository) -> None:
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
'''
pattern = r'def render_data_center\(policy_repository\) -> None:\n.*?\n\nst\.set_page_config'
text, count = re.subn(pattern, new_data_center + '\n\nst.set_page_config', text, count=1, flags=re.S)
if count != 1:
    raise RuntimeError(f"data center replacement count={count}")

text = text.replace('actions[0].value if actions else "NONE"', 'actions[0].action.value if actions else "NONE"')

old_main = '''source_frame = load_partner_data(partner_store)\npartner_records = require_valid_dataframe(source_frame)\nportfolio_results = evaluate_portfolio(source_frame, policy_repository)\nevaluation_map = {\n    partner.partner_id: evaluate_partner(partner, policy_repository) for partner in partner_records\n}\n'''
new_main = '''active_dataset = st.session_state.get(ACTIVE_DATASET_FRAME_KEY)\nif isinstance(active_dataset, pd.DataFrame) and not active_dataset.empty:\n    source_frame = active_dataset.copy()\n    partner_records = require_valid_dataframe(source_frame)\n    portfolio_results = evaluate_portfolio(source_frame, policy_repository)\n    evaluation_map = {partner.partner_id: evaluate_partner(partner, policy_repository) for partner in partner_records}\nelse:\n    source_frame = pd.DataFrame()\n    partner_records = []\n    portfolio_results = pd.DataFrame()\n    evaluation_map = {}\n'''
if old_main not in text:
    raise RuntimeError("main dataset block missing")
text = text.replace(old_main, new_main, 1)

old_tabs = '''with overview_tab:\n    render_overview(portfolio_results)\nwith partner_tab:\n    render_partner_360(partner_records, evaluation_map, policy_repository)\nwith data_center_tab:\n    render_data_center(policy_repository)\nwith policy_tab:\n    render_policy_studio(policy_manager, partner_records)\nwith scenario_tab:\n    render_scenario_lab(policy_manager, source_frame, partner_records)\nwith audit_tab:\n    render_audit_log(policy_manager)\n'''
new_tabs = '''with overview_tab:\n    if partner_records:\n        render_overview(portfolio_results)\n    else:\n        render_dataset_empty_state("Channel Overview")\nwith partner_tab:\n    if partner_records:\n        render_partner_360(partner_records, evaluation_map, policy_repository)\n    else:\n        render_dataset_empty_state("Partner 360")\nwith data_center_tab:\n    render_data_center(policy_repository)\nwith policy_tab:\n    render_policy_studio(policy_manager, partner_records)\nwith scenario_tab:\n    if partner_records:\n        render_scenario_lab(policy_manager, source_frame, partner_records)\n    else:\n        render_dataset_empty_state("Scenario Lab")\nwith audit_tab:\n    render_audit_log(policy_manager)\n'''
if old_tabs not in text:
    raise RuntimeError("tab rendering block missing")
text = text.replace(old_tabs, new_tabs, 1)
APP.write_text(text, encoding="utf-8")

css = THEME.read_text(encoding="utf-8")
if "Preserve Streamlit Material Symbol glyphs" not in css:
    icon_guard = '''\n        /* Preserve Streamlit Material Symbol glyphs. */\n        [data-testid="stIconMaterial"],\n        [data-testid="stIconMaterial"] span,\n        .material-symbols-rounded,\n        .material-icons {\n          font-family: "Material Symbols Rounded", "Material Icons" !important;\n          font-weight: normal !important;\n          font-style: normal !important;\n          letter-spacing: normal !important;\n          text-transform: none !important;\n        }\n'''
    css = css.replace("        </style>", icon_guard + "        </style>", 1)
THEME.write_text(css, encoding="utf-8")
