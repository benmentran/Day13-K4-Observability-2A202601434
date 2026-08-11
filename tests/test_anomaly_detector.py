from __future__ import annotations

import json
from pathlib import Path

from scripts.detect_anomaly import analyze, detect_pii_leak


def _write_logs(path: Path, records: list[dict]) -> None:
    path.write_text(
        "\n".join(json.dumps(r) for r in records) + "\n",
        encoding="utf-8",
    )


def test_detect_pii_leak() -> None:
    assert detect_pii_leak({"message": "email student@vinuni.edu.vn"}) is not None
    assert detect_pii_leak({"message": "plain text only"}) is None


def test_analyze_reports_anomalies(tmp_path: Path) -> None:
    log_path = tmp_path / "logs.jsonl"
    _write_logs(
        log_path,
        [
            {"ts": "t", "event": "app_started", "service": "day13"},
            {
                "ts": "t",
                "event": "request_received",
                "correlation_id": "req-1",
                "payload": {"message_preview": "phone 0987654321"},
            },
            {
                "ts": "t",
                "event": "response_sent",
                "correlation_id": "req-2",
                "latency_ms": 5000,
                "cost_usd": 0.02,
                "tokens_in": 100,
                "tokens_out": 900,
            },
            {
                "ts": "t",
                "event": "response_sent",
                "correlation_id": "req-3",
                "latency_ms": 100,
                "cost_usd": 0.0003,
                "tokens_in": 100,
                "tokens_out": 90,
            },
        ],
    )

    anomalies = analyze(log_path, latency_threshold=2000, cost_threshold=0.01, tokens_ratio=8.0)
    types = [entry["anomaly_type"] for entry in anomalies]
    assert "pii_leak" in types
    assert "latency_slo_breach" in types
    assert "cost_anomaly" in types
    assert "token_ratio_anomaly" in types
    assert "missing_correlation_id" not in types
    assert all(entry["correlation_id"] in ("req-1", "req-2", "req-3") for entry in anomalies)


def test_analyze_clean_logs_no_anomalies(tmp_path: Path) -> None:
    log_path = tmp_path / "logs.jsonl"
    _write_logs(
        log_path,
        [
            {"ts": "t", "event": "app_started"},
            {
                "ts": "t",
                "event": "response_sent",
                "correlation_id": "req-1",
                "latency_ms": 100,
                "cost_usd": 0.0003,
                "tokens_in": 100,
                "tokens_out": 90,
            },
        ],
    )
    assert analyze(log_path, latency_threshold=2000, cost_threshold=0.01, tokens_ratio=8.0) == []
