from __future__ import annotations

import json
from pathlib import Path

from app import audit


def test_audit_writes_append_only_jsonl(monkeypatch, tmp_path: Path) -> None:
    log_path = tmp_path / "audit.jsonl"
    monkeypatch.setattr(audit, "AUDIT_LOG_PATH", log_path)

    audit.audit("app_started", detail={"config": {"max_output_tokens": 0}})
    entry = audit.audit("config_changed", target="max_output_tokens", before=0, after=150)

    lines = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    assert len(lines) == 2
    assert lines[0]["action"] == "app_started"
    assert lines[1]["action"] == "config_changed"
    assert lines[1]["target"] == "max_output_tokens"
    assert lines[1]["before"] == 0
    assert lines[1]["after"] == 150
    assert entry["audit_id"]
    assert lines[0]["event"] == "audit"


def test_audit_handles_non_jsonable_detail(monkeypatch, tmp_path: Path) -> None:
    log_path = tmp_path / "audit.jsonl"
    monkeypatch.setattr(audit, "AUDIT_LOG_PATH", log_path)

    audit.audit("config_changed", target="cache_enabled", before=True, after=False)
    line = json.loads(log_path.read_text(encoding="utf-8").splitlines()[0])
    assert line["after"] is False
