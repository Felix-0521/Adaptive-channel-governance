from pathlib import Path

from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).parents[1]


def test_streamlit_app_executes_without_exception() -> None:
    app = AppTest.from_file(ROOT / "app.py").run(timeout=20)
    assert not app.exception
    assert any("合作伙伴管理" in tab.label and "Partner Management" in tab.label for tab in app.tabs)


def test_streamlit_primary_navigation_is_bilingual() -> None:
    app = AppTest.from_file(ROOT / "app.py").run(timeout=20)
    labels = [tab.label for tab in app.tabs]
    assert any("渠道总览" in label and "Executive Overview" in label for label in labels)
    assert any("合作伙伴全景分析" in label and "Partner 360" in label for label in labels)
    assert any("策略配置中心" in label and "Policy Studio" in label for label in labels)
    assert any("策略模拟实验室" in label and "Scenario Lab" in label for label in labels)
    assert "自适应渠道治理" in app.title[0].value
