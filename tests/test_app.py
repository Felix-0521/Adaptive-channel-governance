from pathlib import Path

from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).parents[1]


def test_streamlit_app_executes_without_exception() -> None:
    """Verify app loads without exception and all 6 main nav tabs are present."""
    app = AppTest.from_file(ROOT / "app.py").run(timeout=20)
    assert not app.exception
    # B2 nav: Data Center, Channel Overview, Partner 360, Policy Studio, Scenario Lab, Audit Log
    tab_labels = {tab.label for tab in app.tabs}
    assert any("数据中心" in label and "Data Center" in label for label in tab_labels)
    assert any("渠道总览" in label and "Channel Overview" in label for label in tab_labels)
    assert any("合作伙伴全景分析" in label and "Partner 360" in label for label in tab_labels)
    assert any("策略配置中心" in label and "Policy Studio" in label for label in tab_labels)
    assert any("策略模拟实验室" in label and "Scenario Lab" in label for label in tab_labels)
    assert any("审计日志" in label and "Audit Log" in label for label in tab_labels)


def test_streamlit_primary_navigation_is_bilingual() -> None:
    """Verify all tab labels are bilingual (Chinese + English)."""
    app = AppTest.from_file(ROOT / "app.py").run(timeout=20)
    labels = [tab.label for tab in app.tabs]
    # Data Center is now first per B2 nav order
    assert any("数据中心" in label and "Data Center" in label for label in labels)
    assert any("渠道总览" in label and "Channel Overview" in label for label in labels)
    assert any("合作伙伴全景分析" in label and "Partner 360" in label for label in labels)
    assert any("策略配置中心" in label and "Policy Studio" in label for label in labels)
    assert any("策略模拟实验室" in label and "Scenario Lab" in label for label in labels)
    assert "自适应渠道治理" in app.title[0].value
