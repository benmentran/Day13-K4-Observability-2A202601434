from __future__ import annotations

import json
from pathlib import Path

import structlog

from app import logging_config
from app.logging_config import configure_logging, scrub_event

EMAIL = "student@vinuni.edu.vn"
PHONE = "090 123 4567"
CARD = "4111 1111 1111 1111"


def _scrubbed(event_dict: dict) -> str:
    return json.dumps(scrub_event(None, "info", event_dict), ensure_ascii=False)


def test_scrub_event_redacts_nested_dict_in_payload() -> None:
    """Đường rò 1: dict lồng nhau bị bản gốc bỏ qua."""
    out = _scrubbed(
        {"event": "request_received", "payload": {"user": {"email": EMAIL}}}
    )

    assert EMAIL not in out
    assert "REDACTED_EMAIL" in out


def test_scrub_event_redacts_values_inside_lists() -> None:
    """Đường rò 2: list bị bản gốc bỏ qua."""
    out = _scrubbed({"event": "batch_done", "payload": {"contacts": [EMAIL, PHONE]}})

    assert EMAIL not in out
    assert PHONE not in out


def test_scrub_event_redacts_top_level_fields() -> None:
    """Đường rò 3: field bind qua contextvars nằm ngoài payload."""
    out = _scrubbed({"event": "request_received", "note": f"callback {PHONE}"})

    assert PHONE not in out
    assert "REDACTED_PHONE_VN" in out


def test_scrub_event_keeps_non_string_values_usable() -> None:
    """Số liệu dashboard phải giữ nguyên kiểu, không bị chuyển thành chuỗi."""
    out = scrub_event(
        None,
        "info",
        {"event": "response_sent", "latency_ms": 1684, "cost_usd": 0.0021},
    )

    assert out["latency_ms"] == 1684
    assert out["cost_usd"] == 0.0021


def test_logging_pipeline_redacts_unsanitised_record(monkeypatch, tmp_path: Path) -> None:
    """Test end-to-end: log PII thô mà KHÔNG gọi summarize_text ở call site.

    Đây là kịch bản thật khi một thành viên thêm log mới và quên scrub thủ công.
    """
    log_path = tmp_path / "logs.jsonl"
    monkeypatch.setattr(logging_config, "LOG_PATH", log_path)

    structlog.reset_defaults()
    configure_logging()
    structlog.get_logger().info(
        "unsafe_debug_log",
        service="api",
        payload={"raw_message": f"Liên hệ {EMAIL} hoặc {PHONE}, thẻ {CARD}"},
    )

    written = log_path.read_text(encoding="utf-8")
    for secret in (EMAIL, PHONE, CARD):
        assert secret not in written, f"PII lọt xuống file: {secret}"
    assert json.loads(written.splitlines()[0])["event"] == "unsafe_debug_log"
