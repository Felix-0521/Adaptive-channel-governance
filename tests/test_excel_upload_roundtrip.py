"""Regression coverage for the browser-style Excel upload path."""

from io import BytesIO
from pathlib import Path

import pandas as pd

from channel_governance.data_normalizer import normalize_excel_templates
from channel_governance.template_schema import TemplateId


ROOT = Path(__file__).parents[1]
SYNTHETIC_DIR = ROOT / "data" / "synthetic"


def test_browser_style_excel_bytes_normalize_full_portfolio() -> None:
    """Uploaded xlsx bytes must preserve the header expected by the normalizer."""
    app_source = (ROOT / "app.py").read_text(encoding="utf-8")
    assert "pd.read_excel(BytesIO(uploaded.read()), header=None)" not in app_source

    templates = {}
    for tid in TemplateId:
        payload = (SYNTHETIC_DIR / f"{tid.value}.xlsx").read_bytes()
        templates[tid] = pd.read_excel(BytesIO(payload))

    result = normalize_excel_templates(templates)
    assert result.success is True
    assert len(result.partner_records) == 50
    assert len(result.errors) == 0
