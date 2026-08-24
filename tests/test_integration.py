from pathlib import Path

import pandas as pd

from channel_governance.evaluation import evaluate_portfolio


ROOT = Path(__file__).parents[1]


def test_synthetic_dataset_evaluates_end_to_end(policies) -> None:
    frame = pd.read_csv(ROOT / "data" / "sample_partners.csv")
    results = evaluate_portfolio(frame, policies)
    assert len(results) == 12
    assert results["partner_id"].is_unique
    assert results["score"].between(0, 100).all()
    assert {"ACTIVE", "MONITOR", "REVIEW", "HOLD"}.issuperset(set(results["governance_status"]))
    assert (results.loc[results["partner_id"] == "P-009", "governance_status"] == "HOLD").all()
    assert (results.loc[results["partner_id"] == "P-009", "risk_level"] == "CRITICAL").all()
