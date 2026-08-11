from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.cli import configure_utf8_stdio
from app.pii import scrub_text

DEFAULT_LOG_PATH = "data/logs.jsonl"
DEFAULT_ANOMALY_PATH = "data/anomalies.jsonl"
DEFAULT_COST_THRESHOLD_USD = 0.01
DEFAULT_TOKENS_RATIO = 8.0


def load_challenge_threshold(repo_root: Path) -> int | None:
    challenge_path = repo_root / "config" / "challenge.json"
    if not challenge_path.exists():
        return None
    try:
        payload = json.loads(challenge_path.read_text(encoding="utf-8"))
        return int(payload.get("latency_threshold_ms") or 0) or None
    except (ValueError, OSError):
        return None


def detect_pii_leak(record: dict[str, Any]) -> list[str] | None:
    raw = json.dumps(record, ensure_ascii=False)
    scrubbed = scrub_text(raw)
    if scrubbed == raw:
        return None
    markers = re.findall(r"\[REDACTED_[A-Z_]+\]", scrubbed)
    return markers or ["[REDACTED]"]


def analyze(log_path: Path, latency_threshold: int | None, cost_threshold: float, tokens_ratio: float) -> list[dict[str, Any]]:
    anomalies: list[dict[str, Any]] = []
    ts_now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    if not log_path.exists():
        raise FileNotFoundError(f"Không tìm thấy {log_path}. Hãy chạy load test trước.")

    for line in log_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            anomalies.append(
                {
                    "ts": ts_now,
                    "anomaly_type": "malformed_log",
                    "correlation_id": None,
                    "event": None,
                    "detail": {"preview": line[:120]},
                }
            )
            continue

        event = record.get("event")
        correlation_id = record.get("correlation_id")

        if event not in ("app_started", "app_shutdown") and not correlation_id:
            anomalies.append(
                {
                    "ts": ts_now,
                    "anomaly_type": "missing_correlation_id",
                    "correlation_id": None,
                    "event": event,
                    "detail": {"line_preview": json.dumps(record, ensure_ascii=False)[:120]},
                }
            )

        leak_snippet = detect_pii_leak(record)
        if leak_snippet is not None:
            anomalies.append(
                {
                    "ts": ts_now,
                    "anomaly_type": "pii_leak",
                    "correlation_id": correlation_id,
                    "event": event,
                    "detail": {"markers": leak_snippet},
                }
            )

        if event == "response_sent":
            latency = record.get("latency_ms")
            if isinstance(latency, int) and latency_threshold is not None and latency > latency_threshold:
                anomalies.append(
                    {
                        "ts": ts_now,
                        "anomaly_type": "latency_slo_breach",
                        "correlation_id": correlation_id,
                        "event": event,
                        "detail": {"latency_ms": latency, "threshold_ms": latency_threshold},
                    }
                )

            cost = record.get("cost_usd")
            tokens_in = record.get("tokens_in") or 0
            tokens_out = record.get("tokens_out") or 0
            if isinstance(cost, (int, float)) and cost > cost_threshold:
                anomalies.append(
                    {
                        "ts": ts_now,
                        "anomaly_type": "cost_anomaly",
                        "correlation_id": correlation_id,
                        "event": event,
                        "detail": {"cost_usd": cost, "threshold_usd": cost_threshold},
                    }
                )
            if tokens_in > 0 and tokens_out / tokens_in > tokens_ratio:
                anomalies.append(
                    {
                        "ts": ts_now,
                        "anomaly_type": "token_ratio_anomaly",
                        "correlation_id": correlation_id,
                        "event": event,
                        "detail": {"tokens_in": tokens_in, "tokens_out": tokens_out, "ratio_threshold": tokens_ratio},
                    }
                )

    return anomalies


def main() -> int:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(description="Phát hiện anomaly từ data/logs.jsonl")
    parser.add_argument("--log-path", default=DEFAULT_LOG_PATH)
    parser.add_argument("--anomaly-path", default=DEFAULT_ANOMALY_PATH)
    parser.add_argument("--threshold", type=int, default=None, help="Ngưỡng latency SLO (ms)")
    parser.add_argument("--cost-threshold", type=float, default=DEFAULT_COST_THRESHOLD_USD)
    parser.add_argument("--tokens-ratio", type=float, default=DEFAULT_TOKENS_RATIO)
    args = parser.parse_args()

    threshold = args.threshold
    if threshold is None:
        threshold = load_challenge_threshold(REPO_ROOT)

    try:
        anomalies = analyze(
            Path(args.log_path),
            latency_threshold=threshold,
            cost_threshold=args.cost_threshold,
            tokens_ratio=args.tokens_ratio,
        )
    except FileNotFoundError as exc:
        print(f"LỖI: {exc}")
        return 2

    anomaly_path = Path(args.anomaly_path)
    if anomalies:
        anomaly_path.parent.mkdir(parents=True, exist_ok=True)
        with anomaly_path.open("a", encoding="utf-8") as f:
            for entry in anomalies:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(f"PHÂN TÍCH: {args.log_path} ({threshold}ms latency threshold, {args.cost_threshold}USD cost)")
    if not anomalies:
        print("HỢP LỆ: không phát hiện anomaly.")
        return 0

    print(f"PHÁT HIỆN {len(anomalies)} anomaly (đã ghi vào {args.anomaly_path}):")
    for entry in anomalies:
        print(
            f"  - [{entry['anomaly_type']}] correlation_id={entry['correlation_id']} "
            f"event={entry['event']} {json.dumps(entry['detail'], ensure_ascii=False)}"
        )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
