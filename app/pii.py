from __future__ import annotations

import hashlib
import re

# Thứ tự có ý nghĩa: pattern dài/đặc hiệu chạy trước để không bị pattern ngắn
# "ăn" mất một phần chuỗi rồi để lại phần đuôi nguyên văn.
# Ví dụ: IP 010.123.456.789 phải khớp `ip_address` trước, nếu không `phone_vn`
# sẽ nuốt "010.123.456" và bỏ sót ".789".
PII_PATTERNS: dict[str, str] = {
    "email": r"[\w\.-]+@[\w\.-]+\.\w+",
    "secret_token": r"\b(?:sk|pk)-(?:lf|ant)-[A-Za-z0-9_\-]{8,}",
    "credit_card": r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b",
    "cccd": r"\b\d{12}\b",
    "ip_address": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
    "phone_vn": r"(?<!\d)(?:\+84|0)(?:[ .-]?\d){9}(?!\d)",
    "cmnd": r"\b\d{9}\b",
    "passport_vn": r"\b[A-Z]{1,2}\d{7}\b",
    "address_vn": (
        r"(?i)(?:số\s*\d+[\w/]*[,\s]+)?"
        r"\b(?:đường|phố|ngõ|ngách|hẻm|quận|phường|thị trấn|huyện|tỉnh|tp\.?)\s+"
        r"[^\n,;.]{2,40}"
    ),
}


def scrub_text(text: str) -> str:
    safe = text
    for name, pattern in PII_PATTERNS.items():
        safe = re.sub(pattern, f"[REDACTED_{name.upper()}]", safe)
    return safe


def summarize_text(text: str, max_len: int = 80) -> str:
    safe = scrub_text(text).strip().replace("\n", " ")
    return safe[:max_len] + ("..." if len(safe) > max_len else "")


def hash_user_id(user_id: str) -> str:
    return hashlib.sha256(user_id.encode("utf-8")).hexdigest()[:12]
