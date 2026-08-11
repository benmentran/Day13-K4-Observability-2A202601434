from __future__ import annotations

import threading
import time
from typing import Any

CONFIG: dict[str, Any] = {
    "max_output_tokens": 0,
    "cache_enabled": False,
    "cache_ttl_seconds": 60,
}

_LOCK = threading.Lock()


def get_config() -> dict[str, Any]:
    return dict(CONFIG)


def update_config(patch: dict[str, Any]) -> dict[str, Any]:
    allowed = {"max_output_tokens", "cache_enabled", "cache_ttl_seconds"}
    unknown = set(patch) - allowed
    if unknown:
        raise KeyError(f"Unknown config keys: {', '.join(sorted(unknown))}")

    with _LOCK:
        changed: dict[str, tuple[Any, Any]] = {}
        for key, value in patch.items():
            if key == "max_output_tokens":
                if not isinstance(value, int) or value < 0:
                    raise ValueError("max_output_tokens phải là số nguyên >= 0")
            elif key == "cache_ttl_seconds":
                if not isinstance(value, (int, float)) or value <= 0:
                    raise ValueError("cache_ttl_seconds phải là số dương")
            elif key == "cache_enabled" and not isinstance(value, bool):
                raise ValueError("cache_enabled phải là boolean")
            before = CONFIG[key]
            if before != value:
                CONFIG[key] = value
                changed[key] = (before, value)
    return dict(CONFIG), changed


_CACHE: dict[tuple[str, str], tuple[float, Any]] = {}
_CACHE_LOCK = threading.Lock()


def _is_fresh(expires_at: float, now: float) -> bool:
    return expires_at > now


def cache_get(feature: str, message: str) -> Any | None:
    key = (feature, message)
    now = time.monotonic()
    with _CACHE_LOCK:
        item = _CACHE.get(key)
        if item is None:
            return None
        expires_at, value = item
        if not _is_fresh(expires_at, now):
            _CACHE.pop(key, None)
            return None
        return value


def cache_put(feature: str, message: str, value: Any) -> None:
    ttl = float(CONFIG["cache_ttl_seconds"])
    key = (feature, message)
    with _CACHE_LOCK:
        _CACHE[key] = (time.monotonic() + ttl, value)


def cache_clear() -> None:
    with _CACHE_LOCK:
        _CACHE.clear()


def cache_size() -> int:
    with _CACHE_LOCK:
        return len(_CACHE)
