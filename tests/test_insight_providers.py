from channel_governance.evaluation import evaluate_partner
from channel_governance.insight import generate_deterministic_insight
from channel_governance.insight_providers import (
    OpenAIInsightProvider,
    build_management_context,
    generate_management_insight,
)
from channel_governance.models import PartnerRecord
import json
from types import SimpleNamespace


def partner() -> PartnerRecord:
    return PartnerRecord(
        partner_id="P-AI", partner_name="Synthetic AI Partner", business_line="SURVEYING",
        country_code="PL", lifecycle_stage="GROWTH", market_tier="GROWTH_VALUE",
        partner_type="DISTRIBUTOR", annual_revenue=500_000, target_achievement_pct=90,
        yoy_growth_pct=12, new_product_contribution_pct=15, active_dealers=10,
        geographic_coverage_pct=65, inventory_days=80, sell_out_performance_pct=92,
        forecast_accuracy_pct=80, payment_on_time_pct=90, ar_overdue_90d_pct=5,
        certified_engineers=3, training_completion_pct=80, demo_capability=True,
        data_reporting_quality_pct=90, pricing_violations=0,
        unauthorized_sales_incidents=0, sanctions_match=False, material_contract_breach=False,
    )


class UnavailableProvider:
    available = False

    def generate(self, context):
        raise AssertionError("unavailable provider must not be called")


class FailingProvider:
    available = True

    def generate(self, context):
        raise TimeoutError("synthetic timeout")


class CapturingProvider:
    available = True

    def __init__(self, response):
        self.response = response
        self.context = None

    def generate(self, context):
        self.context = context
        return self.response


def setup(record, policies):
    result = evaluate_partner(record, policies)
    policy = policies.resolve(record)
    fallback = generate_deterministic_insight(record, result, policy)
    return result, policy, fallback


def test_ai_unavailable_returns_deterministic_fallback(policies) -> None:
    record = partner()
    result, policy, fallback = setup(record, policies)
    assert generate_management_insight(record, result, policy, UnavailableProvider()) == fallback


def test_provider_error_returns_deterministic_fallback(policies) -> None:
    record = partner()
    result, policy, fallback = setup(record, policies)
    assert generate_management_insight(record, result, policy, FailingProvider()) == fallback


def test_provider_cannot_mutate_evaluation_object(policies) -> None:
    record = partner()
    result, policy, fallback = setup(record, policies)
    original = result.model_dump()
    provider = CapturingProvider(fallback)
    enhanced = generate_management_insight(record, result, policy, provider)
    assert result.model_dump() == original
    assert enhanced.source == "AI_ENHANCED"
    assert not hasattr(provider.context, "pillar_scores")


def test_raw_dataset_is_not_passed_to_provider(policies) -> None:
    record = partner()
    result, policy, fallback = setup(record, policies)
    context = build_management_context(record, result, fallback)
    keys = set(context.model_dump())
    assert "raw_dataset" not in keys and "dataframe" not in keys and "csv" not in keys
    assert "annual_revenue" not in keys
    assert keys == set(type(context).model_fields)


def test_openai_adapter_mock_can_only_replace_narrative(policies) -> None:
    record = partner()
    result, policy, fallback = setup(record, policies)

    class Responses:
        def __init__(self):
            self.request = None

        def create(self, **kwargs):
            self.request = kwargs
            return SimpleNamespace(output_text=json.dumps({
                "executive_summary": "Fact-bound summary.",
                "management_attention": "Review supplied evidence.",
                "recommended_next_step": "Use the existing action.",
                "data_limitations": ["Uncertainty remains."],
            }))

    responses = Responses()
    provider = OpenAIInsightProvider(
        api_key="synthetic-test-key",
        model="synthetic-test-model",
        client=SimpleNamespace(responses=responses),
    )
    enhanced = generate_management_insight(record, result, policy, provider)
    assert enhanced.executive_summary == "Fact-bound summary."
    assert enhanced.severity == fallback.severity
    assert enhanced.key_drivers == fallback.key_drivers
    assert "annual_revenue" not in responses.request["input"]
    schema = responses.request["text"]["format"]["schema"]
    assert set(schema["required"]) == set(schema["properties"])
