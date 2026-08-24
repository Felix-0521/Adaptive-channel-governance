from pathlib import Path

from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).parents[1]


def test_streamlit_app_executes_without_exception() -> None:
    app = AppTest.from_file(ROOT / "app.py").run(timeout=20)
    assert not app.exception

