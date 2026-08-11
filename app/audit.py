from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path
from typing import Any
from uuid import uuid4

AUDIT_LOG_PATH = Path(os.getenv("AUDIT_LOG_PATH", "data/audit.jsonl"))
_LOCK = threading.Lock()


def audit(action: str, target: str | None = None, before: Any = None, after: Any = None, detail: dict[str, Any] | None = None) -> dict[str, Any]:
    entry = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "event": "audit",
        "action": action,
        "target": target,
        "before": _jsonable(before),
        "after": _jsonable(after),
        "detail": detail or {},
        "audit_id": uuid4().hex[:12],
    }
    with _LOCK:
        AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with AUDIT_LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    try:
        json.dumps(value)
        return value
    except (TypeError, ValueError):
        return str(value)
