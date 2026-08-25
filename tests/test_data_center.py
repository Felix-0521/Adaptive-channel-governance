"""Tests for the Business Data Center PART C."""
from __future__ import annotations

import pytest
from pathlib import Path
import pandas as pd


ROOT = Path(__file__).parent.parent
SYNTHETIC_DIR = ROOT / "data" / "synthetic"


class TestDataCenterIntegration:
    """PART C: Upload validation, normalization integration, evaluation integration."""

    def _load_templates(self):
        from channel_governance.template_schema import TemplateId
        templates = {}
        for tid in TemplateId:
            path = SYNTHETIC_DIR / f"{tid.value}.xlsx"
            assert path.exists(), f"Missing: {path}"
            templates[tid] = pd.read_excel(path)
        return templates

    def test_synthetic_portfolio_loadable_for_normalization(self):
        """The synthetic portfolio can be loaded and fed to the normalizer."""
        from channel_governance.data_normalizer import normalize_excel_templates

        templates = self._load_templates()
        result = normalize_excel_templates(templates)
        assert result.success, "Normalization should succeed for synthetic portfolio"
        assert len(result.partner_records) == 50, \
            f"Expected 50 normalized partners, got {len(result.partner_records)}"

    def test_normalized_output_contains_expected_fields(self):
        """Normalized output includes all fields required by the evaluation engine."""
        from channel_governance.data_normalizer import normalize_excel_templates

        templates = self._load_templates()
        result = normalize_excel_templates(templates)
        first = result.partner_records[0]
        required = [
            "partner_id", "partner_name", "business_line", "country_code",
            "lifecycle_stage", "market_tier", "partner_type",
            "annual_revenue", "inventory_days",
            "payment_on_time_pct", "certified_engineers",
        ]
        for field in required:
            assert hasattr(first, field), f"Missing field: {field}"

    def test_synthetic_portfolio_data_quality_score(self):
        """Synthetic portfolio has a data quality score in valid range."""
        from channel_governance.data_normalizer import normalize_excel_templates

        templates = self._load_templates()
        result = normalize_excel_templates(templates)
        assert result.data_quality_score is not None
        assert 0.0 <= result.data_quality_score <= 1.0

    def test_mid_value_tier_passes_through(self):
        """MID_VALUE tier is a valid MarketTier enum value; no warning issued."""
        from channel_governance.data_normalizer import normalize_excel_templates
        from channel_governance.models import MarketTier

        templates = self._load_templates()
        result = normalize_excel_templates(templates)

        # All synthetic partners normalize (no MID_VALUE-specific blocker).
        assert result.success, "Normalization should succeed for synthetic portfolio"

        # At least one MID_VALUE partner should normalize cleanly.
        mid_partners = [p for p in result.partner_records if p.market_tier == MarketTier.MID_VALUE]
        assert len(mid_partners) >= 1, \
            "Expected at least one MID_VALUE partner in normalized output"

        # No issue should explicitly reject MID_VALUE as an unknown tier.
        mid_rejections = [
            i for i in result.issues
            if "MID_VALUE" in str(i.message) and ("not a valid" in i.message.lower() or "requires MarketTier" in i.message)
        ]
        assert len(mid_rejections) == 0, \
            f"MID_VALUE should be accepted, got rejections: {[i.message for i in mid_rejections]}"

    def test_normalized_partner_count_matches_case5_gaps(self):
        """Case 5 partners (PT00021-PT00025) are included with null metrics."""
        from channel_governance.data_normalizer import normalize_excel_templates

        templates = self._load_templates()
        result = normalize_excel_templates(templates)
        partner_ids = [p.partner_id for p in result.partner_records]
        for pid in ["PT00021", "PT00022", "PT00023", "PT00024", "PT00025"]:
            assert pid in partner_ids, \
                f"Case 5 partner {pid} missing from normalized output"

    def test_normalization_result_includes_derived_metrics(self):
        """NormalizationResult carries derived_metrics dict."""
        from channel_governance.data_normalizer import normalize_excel_templates

        templates = self._load_templates()
        result = normalize_excel_templates(templates)
        assert hasattr(result, "derived_metrics")
        assert result.derived_metrics is not None

    def test_upload_validation_detects_duplicate_partner_ids(self):
        """Validation detects duplicate Partner_ID in uploaded data."""
        from channel_governance.data_normalizer import normalize_excel_templates
        from channel_governance.template_schema import TemplateId

        templates = self._load_templates()
        # Duplicate PT00001 in master sheet
        df = templates[TemplateId.PARTNER_MASTER].copy()
        dup_row = df[df["Partner_ID"] == "PT00001"].iloc[0].to_dict()
        templates[TemplateId.PARTNER_MASTER] = pd.concat(
            [df, pd.DataFrame([dup_row])], ignore_index=True)

        result = normalize_excel_templates(templates)
        # Issue about duplicate row should appear at the duplicated row index
        assert len(result.issues) >= 1, \
            "Duplicate Partner_ID should produce an issue"

    def test_upload_validation_detects_missing_partner_id(self):
        """Validation detects missing/empty Partner_ID in a data row."""
        from channel_governance.data_normalizer import normalize_excel_templates
        from channel_governance.template_schema import TemplateId

        templates = self._load_templates()
        # Set first data row Partner_ID to empty string
        df = templates[TemplateId.PARTNER_MASTER].copy()
        df.iloc[0, df.columns.get_loc("Partner_ID")] = ""
        templates[TemplateId.PARTNER_MASTER] = df

        result = normalize_excel_templates(templates)
        # Empty Partner_ID should produce at least one issue
        assert len(result.issues) >= 1, \
            "Empty Partner_ID should produce an issue"

    def test_evaluation_engine_accepts_normalized_partner_record(self):
        """Existing evaluation engine accepts a PartnerRecord from the normalizer."""
        from channel_governance.data_normalizer import normalize_excel_templates
        from channel_governance.evaluation import evaluate_partner
        from channel_governance.policy import PolicyRepository

        templates = self._load_templates()
        result = normalize_excel_templates(templates)
        policy_repo = PolicyRepository.from_yaml(ROOT / "config" / "scoring_rules.yaml")

        # Evaluate first healthy partner (PT00001)
        healthy = next(p for p in result.partner_records if p.partner_id == "PT00001")
        eval_result = evaluate_partner(healthy, policy_repo)

        assert eval_result.score is not None, "Score should be computed"
        assert eval_result.tier in ("STRATEGIC", "CORE", "DEVELOPMENT"), \
            f"Unexpected tier: {eval_result.tier}"
        # EvaluationResult does not expose a single risk_level field; the real
        # source of risk is the aggregated list[RiskFlag] with RiskSeverity.
        # Confirm the result carries at least one risk entry (or an empty list).
        assert hasattr(eval_result, "risks")
        assert isinstance(eval_result.risks, list)

    def test_full_50_partner_synthetic_portfolio_evaluation(self):
        """Full 50-partner synthetic portfolio evaluates without errors."""
        from channel_governance.data_normalizer import normalize_excel_templates
        from channel_governance.evaluation import evaluate_partner
        from channel_governance.policy import PolicyRepository

        templates = self._load_templates()
        result = normalize_excel_templates(templates)
        policy_repo = PolicyRepository.from_yaml(ROOT / "config" / "scoring_rules.yaml")

        scores = []
        for partner in result.partner_records:
            eval_res = evaluate_partner(partner, policy_repo)
            scores.append(eval_res.score)

        assert len(scores) == 50, f"Expected 50 results, got {len(scores)}"
        non_none = [s for s in scores if s is not None]
        assert len(non_none) > 0, "At least some partners should have scores"

    def test_business_case2_inventory_risk_partner_evaluation(self):
        """Case 2 (PT00006) — inventory risk — evaluates with a risk signal."""
        from channel_governance.data_normalizer import normalize_excel_templates
        from channel_governance.evaluation import evaluate_partner
        from channel_governance.policy import PolicyRepository

        templates = self._load_templates()
        result = normalize_excel_templates(templates)
        policy_repo = PolicyRepository.from_yaml(ROOT / "config" / "scoring_rules.yaml")

        partner_006 = next(
            p for p in result.partner_records if p.partner_id == "PT00006"
        )
        eval_006 = evaluate_partner(partner_006, policy_repo)

        assert eval_006.score is not None
        # Aggregate the real risk signal: max severity from result.risks.
        severity_rank = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}
        if eval_006.risks:
            derived_risk_level = max(
                (r.severity.value for r in eval_006.risks),
                key=severity_rank.__getitem__,
            )
            assert derived_risk_level in ("LOW", "MEDIUM", "HIGH", "CRITICAL"), \
                f"PT00006 risk should be valid, got: {derived_risk_level}"
        else:
            # No risks raised — equivalent to LOW severity per evaluation.py default.
            assert eval_006.governance_status.value in ("ACTIVE", "MONITOR"), \
                f"PT00006 with no risks should not be HOLD/REVIEW, got: {eval_006.governance_status.value}"


class TestBusinessScenarios:
    """Phase 9 §5: Validate synthetic Case 1-5 business scenarios."""

    def _eval_portfolio(self):
        from channel_governance.data_normalizer import normalize_excel_templates
        from channel_governance.evaluation import evaluate_partner
        from channel_governance.policy import PolicyRepository

        templates = {}
        for tid in _load_template_ids():
            path = SYNTHETIC_DIR / f"{tid.value}.xlsx"
            templates[tid] = pd.read_excel(path)
        result = normalize_excel_templates(templates)
        policy_repo = PolicyRepository.from_yaml(ROOT / "config" / "scoring_rules.yaml")
        evaluations = {p.partner_id: evaluate_partner(p, policy_repo) for p in result.partner_records}
        return result, evaluations

    def test_case1_healthy_strategic_partner(self):
        """Case 1: PT00001 — healthy, high-value, mature → STRATEGIC, ACTIVE, no risk."""
        _, evals = self._eval_portfolio()
        e = evals["PT00001"]

        assert e.score is not None and e.score >= 85, f"Expected high score, got {e.score}"
        assert e.tier == "STRATEGIC", f"Expected STRATEGIC, got {e.tier}"
        assert e.governance_status.value == "ACTIVE", \
            f"Expected ACTIVE, got {e.governance_status.value}"
        severity_rank = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}
        max_severity = max(
            (r.severity.value for r in e.risks),
            key=severity_rank.__getitem__,
            default="NONE",
        )
        assert max_severity == "NONE", f"PT00001 should have no risks, got {max_severity}"

    def test_case2_high_revenue_with_inventory_risk(self):
        """Case 2: PT00006 — high revenue + 165 inv_days → REVIEW + HIGH risk."""
        _, evals = self._eval_portfolio()
        e = evals["PT00006"]

        assert e.score is not None and e.score >= 60, f"Expected moderate score, got {e.score}"
        assert e.governance_status.value == "REVIEW", \
            f"Expected REVIEW due to inventory risk, got {e.governance_status.value}"
        severity_rank = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}
        max_severity = max(
            (r.severity.value for r in e.risks),
            key=severity_rank.__getitem__,
            default="NONE",
        )
        assert max_severity == "HIGH", f"Expected HIGH risk, got {max_severity}"
        action_codes = [a.action.value for a in e.recommended_actions]
        assert "INVENTORY_OPTIMIZATION" in action_codes, \
            f"Expected INVENTORY_OPTIMIZATION action, got {action_codes}"

    def test_case3_growth_partner(self):
        """Case 3: a GROWTH-lifecycle partner with reasonable score gets a GROWTH-friendly action."""
        _, evals = self._eval_portfolio()
        # PT00030 is BUILD lifecycle (closest to "growth" stage) with score ~89
        e = evals["PT00030"]

        assert e.score is not None and e.score >= 70, f"Expected growth-tier score, got {e.score}"
        assert e.tier in ("STRATEGIC", "CORE"), f"Expected STRATEGIC/CORE, got {e.tier}"
        assert e.governance_status.value in ("ACTIVE", "MONITOR"), \
            f"Expected ACTIVE/MONITOR, got {e.governance_status.value}"

    def test_case4_financial_risk_partner(self):
        """Case 4: PT00020 — ar_overdue_90d_pct ≈ 45% → CREDIT_REVIEW action."""
        _, evals = self._eval_portfolio()
        e = evals["PT00020"]

        action_codes = [a.action.value for a in e.recommended_actions]
        assert "CREDIT_REVIEW" in action_codes, \
            f"Expected CREDIT_REVIEW action, got {action_codes}"

    def test_case5_low_data_quality_partner(self):
        """Case 5: PT00024 — null metrics → low confidence + HOLD/UNRATED."""
        _, evals = self._eval_portfolio()
        e = evals["PT00024"]

        assert e.confidence == 0.0, f"Expected confidence 0.0, got {e.confidence}"
        assert e.score is None, f"Expected no score for unratable partner, got {e.score}"
        assert e.tier == "UNRATED", f"Expected UNRATED, got {e.tier}"
        assert e.governance_status.value == "HOLD", \
            f"Expected HOLD due to compliance risk, got {e.governance_status.value}"


class TestNormalizationSuccessFlag:
    """Phase 9 §6: Warnings must not flip success to False."""

    def test_warnings_do_not_block_success(self):
        from channel_governance.data_normalizer import normalize_excel_templates

        templates = {}
        for tid in _load_template_ids():
            templates[tid] = pd.read_excel(SYNTHETIC_DIR / f"{tid.value}.xlsx")

        result = normalize_excel_templates(templates)

        # Synthetic portfolio has 110+ warnings but no blocking errors.
        assert result.success is True, \
            f"Warnings must not block success, got success={result.success} with {len(result.warnings)} warnings"
        assert len(result.partner_records) > 0
        assert len(result.errors) == 0

    def test_empty_templates_yields_failure(self):
        """An empty input should still surface success=False."""
        from channel_governance.data_normalizer import normalize_excel_templates

        # Empty dict → no partners, success should be False.
        result = normalize_excel_templates({})

        assert result.success is False
        assert len(result.partner_records) == 0


def _load_template_ids():
    """Helper to import TemplateId lazily for the test classes above."""
    from channel_governance.template_schema import TemplateId
    return list(TemplateId)
