# CP1 — PII Scrubbing (Thành viên B, Security Engineer)

Tóm tắt phần việc để dán vào `submission/REPORT.md` mục 2, 3 và 7.

## Vấn đề phát hiện

Repo starter đã có `scrub_text()` và các call site đều gọi `summarize_text()`, nên
`validate_logs.py` báo **0 leak ngay từ baseline**. Con số đó che mất một lỗ hổng thật:

> Việc che PII phụ thuộc vào lập trình viên **nhớ gọi hàm scrub thủ công** ở từng
> chỗ ghi log. Không có lớp kiểm soát nào ở tầng pipeline.

Processor `scrub_event` — vốn là lớp kiểm soát đó — **chưa được đăng ký** vào
`structlog.configure()` (còn nằm trong TODO), và bản thân nó cũng chỉ quét
`payload` nông + `event`, trong khi `validate_logs.py` quét `json.dumps(toàn bộ record)`.

Ba đường rò lọt qua bản gốc nhưng vẫn bị validator bắt:

| # | Đường rò | Ví dụ |
|---|---|---|
| 1 | dict lồng nhau | `payload={"profile": {"email": ...}}` |
| 2 | list | `payload={"attachments": [...]}` |
| 3 | field top-level | bất kỳ khoá nào bind qua `bind_contextvars` |

Bằng chứng: `cp1-05-gap-before-after.txt` — cùng một record, bản gốc để lọt
`['cccd', 'credit_card', 'email', 'phone_vn']`, bản đã vá còn **0 leak**.

## Thay đổi đã thực hiện

**`app/logging_config.py`**

1. Viết lại `scrub_event` thành đệ quy qua `_scrub_value()`, quét toàn bộ
   `event_dict` ở mọi độ sâu (str / dict / list / tuple). Giá trị không phải chuỗi
   (`latency_ms`, `cost_usd`) giữ nguyên kiểu để dashboard vẫn tính toán được.
2. Đăng ký `scrub_event` vào pipeline, đặt **sau `format_exc_info` và ngay trước
   `JsonlFileProcessor`**. Vị trí này quan trọng: traceback chỉ được render thành
   chuỗi ở bước `format_exc_info`, nên nếu scrub chạy sớm hơn (như vị trí TODO gợi ý)
   thì exception chứa dữ liệu người dùng vẫn bị ghi ra file nguyên văn.

**`app/pii.py`** — mở rộng `PII_PATTERNS` từ 4 lên 9, sắp xếp theo nguyên tắc
**pattern dài/đặc hiệu chạy trước**:

| Pattern | Lý do |
|---|---|
| `secret_token` | Key Langfuse/Anthropic (`sk-lf-`, `pk-ant-`) lọt log là sự cố bảo mật |
| `ip_address` | PII theo GDPR; phải đứng **trước** `phone_vn`, nếu không `010.123.456.789` bị `phone_vn` nuốt mất `010.123.456` và bỏ sót `.789` |
| `cmnd` (9 số), `passport_vn` | Giấy tờ tuỳ thân |
| `address_vn` | Địa chỉ theo từ khoá tiếng Việt (đường, quận, phường...) |

## Kết quả kiểm chứng

| Hạng mục | Kết quả |
|---|---|
| `validate_logs.py` — PII | `Potential PII leaks detected: 0` → `[PASSED] PII scrubbing` |
| Test PII | 13/13 pass (`cp1-06-pytest-pii.txt`) |
| Toàn bộ test suite | 33/33 pass |
| Quét secret/PII trên 56 file Git track | Sạch; `.env`, `data/logs.jsonl`, `.venv/` đều không bị track |

Lưu ý: `Estimated Score: 100/100` là điểm của **cả nhóm**. Phần thuộc vai trò này
là 30 điểm ứng với dòng `[PASSED] PII scrubbing`; ba dòng còn lại thuộc Role 1.

## Danh sách evidence

| File | Nội dung |
|---|---|
| `cp1-01-validate-logs-before.txt` | Baseline trước khi sửa |
| `cp1-02-logs-sample-before.jsonl` | Log gốc 21 record |
| `cp1-03-validate-logs-after.txt` | Sau khi vá — 0 leak |
| `cp1-04-redacted-log-lines.json` | 3 record thật đã redact (email, phone, credit card) |
| `cp1-05-gap-before-after.txt` | **Chứng minh lỗ hổng**: 4 loại leak → 0 |
| `cp1-06-pytest-pii.txt` | 13 test PII pass |
| `cp1-07-secret-scan.txt` | Quét secret/PII trên file Git track |

## Câu hỏi vấn đáp có thể gặp

**Vì sao baseline đã 0 leak mà vẫn phải sửa?** Vì 0 leak đó đến từ kỷ luật lập
trình viên ở call site, không phải từ kiểm soát hệ thống. Chỉ cần một dòng log mới
quên `summarize_text()` là lộ ngay — đúng kịch bản trong
`test_logging_pipeline_redacts_unsanitised_record`.

**Vì sao đặt scrub sau `format_exc_info`?** Vì traceback chỉ tồn tại dưới dạng
chuỗi sau bước đó; scrub trước sẽ bỏ sót toàn bộ nội dung exception.

**Redact vs hash vs drop?** Redact giữ được cấu trúc câu để debug mà không giữ giá
trị gốc. `user_id` thì dùng hash (`hash_user_id`) vì cần join các request cùng một
người; PII trong nội dung tin nhắn thì redact vì không cần join.

**Rủi ro false positive?** `cmnd` (9 chữ số) và `address_vn` là hai pattern rộng
nhất. Đã chốt bằng `test_scrub_keeps_clean_text_untouched` để bảo đảm log nghiệp vụ
bình thường không bị che.
