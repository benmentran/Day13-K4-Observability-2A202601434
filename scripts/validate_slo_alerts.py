from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.cli import configure_utf8_stdio

REQUIRED_SLIS = {
    "latency_p95_ms",
    "error_rate_pct",
    "daily_cost_usd",
    "quality_score_avg",
}
REQUIRED_ALERT_FIELDS = {
    "name",
    "severity",
    "condition",
    "duration",
    "type",
    "owner",
    "slo",
    "runbook",
    "metric",
}


class SloAlertConfigError(ValueError):
    pass


def load_yaml(path: Path) -> dict:
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise SloAlertConfigError(f"Không đọc được {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise SloAlertConfigError(f"{path} phải chứa YAML object")
    return payload


def validate(repo_root: Path = REPO_ROOT) -> tuple[int, int]:
    slo = load_yaml(repo_root / "config" / "slo.yaml")
    rules = load_yaml(repo_root / "config" / "alert_rules.yaml")
    runbook_path = repo_root / "docs" / "alerts.md"
    runbook = runbook_path.read_text(encoding="utf-8")

    slis = slo.get("slis")
    if slo.get("window") != "28d" or not isinstance(slis, dict):
        raise SloAlertConfigError("SLO phải có window 28d và object slis")
    if set(slis) != REQUIRED_SLIS:
        raise SloAlertConfigError("SLO phải gồm latency, error rate, daily cost và quality")
    for name, definition in slis.items():
        required = {"description", "query", "objective", "operator", "unit", "target", "target_unit"}
        if not isinstance(definition, dict) or required - set(definition):
            raise SloAlertConfigError(f"SLI {name} thiếu trường bắt buộc")
        if definition["operator"] not in {"lte", "gte"}:
            raise SloAlertConfigError(f"SLI {name} có operator không hợp lệ")

    alerts = rules.get("alerts")
    if not isinstance(alerts, list) or len(alerts) != 3:
        raise SloAlertConfigError("Phải có đúng 3 alert rules")
    for alert in alerts:
        if not isinstance(alert, dict) or REQUIRED_ALERT_FIELDS - set(alert):
            raise SloAlertConfigError("Alert rule thiếu trường bắt buộc")
        if alert["severity"] not in {"warning", "critical"}:
            raise SloAlertConfigError(f"Alert {alert['name']} có severity không hợp lệ")
        if alert["type"] != "symptom-based" or alert["slo"] not in slis:
            raise SloAlertConfigError(f"Alert {alert['name']} chưa liên kết SLO hợp lệ")
        if not re.fullmatch(r"\d+[mh]", str(alert["duration"])):
            raise SloAlertConfigError(f"Alert {alert['name']} có duration không hợp lệ")
        link = str(alert["runbook"])
        prefix = "docs/alerts.md#"
        if not link.startswith(prefix) or f"## {link.removeprefix(prefix).replace('-', ' ').title()}" not in runbook:
            raise SloAlertConfigError(f"Alert {alert['name']} trỏ tới runbook không tồn tại")

    combined = yaml.safe_dump({"slo": slo, "rules": rules}, allow_unicode=True) + runbook
    if "TODO" in combined or "Replace with" in combined:
        raise SloAlertConfigError("CP2 vẫn còn placeholder")
    return len(slis), len(alerts)


def main() -> int:
    configure_utf8_stdio()
    try:
        slo_count, alert_count = validate()
    except (OSError, SloAlertConfigError) as exc:
        print(f"KHÔNG HỢP LỆ: {exc}")
        return 1
    print(f"HỢP LỆ: {slo_count} SLI/SLO, {alert_count} alert rules và 3 runbook.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
