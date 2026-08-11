from __future__ import annotations

import os
from typing import Any

try:
    from langfuse import Langfuse, observe

    LANGFUSE_SDK_AVAILABLE = True
except ImportError:  # pragma: no cover - chỉ dùng khi chưa cài requirements
    LANGFUSE_SDK_AVAILABLE = False
    Langfuse = None
    observe = None


_client = None


def get_langfuse_client() -> Langfuse:
    global _client
    if _client is None:
        _client = Langfuse()
    return _client


def tracing_enabled() -> bool:
    return LANGFUSE_SDK_AVAILABLE and bool(
        os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY")
    )
