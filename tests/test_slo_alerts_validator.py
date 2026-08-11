from pathlib import Path

from scripts.validate_slo_alerts import validate


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_repository_slo_alerts_and_runbooks_are_valid() -> None:
    assert validate(REPO_ROOT) == (4, 3)
