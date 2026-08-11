import pytest

from app import metrics


@pytest.fixture(autouse=True)
def _reset_metrics() -> None:
    metrics.reset()
    yield
    metrics.reset()
