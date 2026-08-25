from pathlib import Path

import pytest

from channel_governance.policy import PolicyLifecycleManager, PolicyRepository


ROOT = Path(__file__).parents[1]


@pytest.fixture(scope="session")
def policies() -> PolicyRepository:
    return PolicyRepository.from_yaml(ROOT / "config" / "scoring_rules.yaml")


@pytest.fixture
def policy_manager() -> PolicyLifecycleManager:
    return PolicyLifecycleManager.from_yaml(ROOT / "config" / "scoring_rules.yaml")
