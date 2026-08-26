from pathlib import Path
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).parents[1]

def test_app_starts_without_automatic_partner_dataset() -> None:
    app = AppTest.from_file(ROOT / "app.py").run(timeout=30)
    assert not app.exception
    info_values = [item.value for item in app.info]
    assert any("No active dataset for Channel Overview" in value for value in info_values)
    assert any("No active dataset for Partner 360" in value for value in info_values)
    assert any("No active dataset for Scenario Lab" in value for value in info_values)
    assert not any("合作伙伴总数" in metric.label for metric in app.metric)

def test_demo_dataset_requires_explicit_click_and_drives_dashboard() -> None:
    app = AppTest.from_file(ROOT / "app.py").run(timeout=30)
    button = next(item for item in app.button if "Load Demo Dataset" in item.label)
    app = button.click().run(timeout=45)
    assert not app.exception
    totals = [m for m in app.metric if "合作伙伴总数" in m.label and "Total Partners" in m.label]
    assert totals
    assert totals[0].value == "50"
