from app.pii import scrub_text


def test_scrub_email() -> None:
    out = scrub_text("Email me at student@vinuni.edu.vn")
    assert "student@" not in out
    assert "REDACTED_EMAIL" in out


def test_scrub_common_vietnamese_phone_formats() -> None:
    phone_numbers = (
        "0901234567",
        "090 123 4567",
        "090.123.4567",
        "090-123-4567",
        "+84 90 123 4567",
    )

    for phone_number in phone_numbers:
        out = scrub_text(f"Contact: {phone_number}")
        assert phone_number not in out
        assert "REDACTED_PHONE_VN" in out


def test_scrub_passport_and_national_id() -> None:
    out = scrub_text("Passport B1234567, CMND 123456789, CCCD 001202012345")

    assert "B1234567" not in out
    assert "123456789" not in out
    assert "001202012345" not in out


def test_scrub_credit_card_is_not_broken_by_shorter_patterns() -> None:
    """Số thẻ phải bị che trọn vẹn, không để sót nhóm chữ số cuối."""
    out = scrub_text("Card 4111 1111 1111 1111 please")

    assert "1111" not in out
    assert "REDACTED_CREDIT_CARD" in out


def test_scrub_ip_address_is_not_split_by_phone_pattern() -> None:
    out = scrub_text("Client IP 010.123.456.789 connected")

    assert "010.123.456" not in out
    assert "789" not in out


def test_scrub_api_secret_tokens() -> None:
    """Key Langfuse/Anthropic lọt vào log là sự cố bảo mật, không chỉ là PII."""
    out = scrub_text("Using sk-lf-1234567890abcdef and pk-lf-abcdef1234567890")

    assert "sk-lf-1234567890abcdef" not in out
    assert "pk-lf-abcdef1234567890" not in out
    assert "REDACTED_SECRET_TOKEN" in out


def test_scrub_vietnamese_address_keywords() -> None:
    out = scrub_text("Giao tới số 25 đường Nguyễn Trãi, quận Thanh Xuân")

    assert "Nguyễn Trãi" not in out
    assert "Thanh Xuân" not in out


def test_scrub_keeps_clean_text_untouched() -> None:
    """Chống false positive: log nghiệp vụ bình thường không được bị che."""
    clean = "Summarize the monitoring policy for production logging"

    assert scrub_text(clean) == clean
