# Alert rules và Incident Runbook

Mỗi alert dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ. Nguồn metric chuẩn là `data/logs.jsonl`; ngưỡng đồng bộ với `config/slo.yaml`.

## High Error Rate

- Tên: `high_error_rate`
- Severity: `critical`
- SLI/SLO: `error_rate_pct <= 2%` trong cửa sổ 28 ngày.
- Điều kiện: `error_rate_pct > 2` liên tục 5 phút.
- Ảnh hưởng: request lỗi hoặc người dùng không nhận được câu trả lời.
- Owner: `sre-alerts`.

### Kiểm tra

1. Xác nhận error rate và traffic cùng cửa sổ 5 phút; không kết luận từ một request đơn lẻ.
2. Lọc event `request_failed`, nhóm theo `error_type` và lấy `correlation_id` đại diện.
3. Mở trace theo `correlation_id` để xác định lỗi ở API, retrieval, tool hay LLM; kiểm tra incident `tool_fail` có đang bật không.

### Mitigation và đóng sự cố

- Khi diễn tập, chạy `python scripts/inject_incident.py --scenario tool_fail --disable`.
- Với sự cố thật, cô lập dependency lỗi; tạm tắt tool không thiết yếu hoặc chuyển sang fallback đã được phê duyệt.
- Escalate cho service owner nếu error rate không giảm sau 10 phút hoặc lỗi lan sang nhiều feature.
- Đóng incident khi `error_rate_pct <= 2%` liên tục 10 phút và request kiểm tra thành công.

## Latency Breach

- Tên: `latency_p95_slo_breach`
- Severity: `warning`.
- SLI/SLO: `latency_p95_ms <= 3000 ms` trong cửa sổ 28 ngày.
- Điều kiện: `latency_p95_ms > 3000` liên tục 10 phút.
- Ảnh hưởng: ít nhất 5% request có trải nghiệm chậm, có nguy cơ timeout.
- Owner: `sre-alerts`.

### Kiểm tra

1. So sánh P50/P95/P99 và traffic để xác định chậm toàn hệ thống hay chỉ tail latency.
2. Chọn request chậm, mở trace và tìm span chiếm phần lớn tổng duration.
3. Đối chiếu log cùng `correlation_id`, feature và model; kiểm tra incident `rag_slow` có đang bật không.

### Mitigation và đóng sự cố

- Khi diễn tập, chạy `python scripts/inject_incident.py --scenario rag_slow --disable`.
- Với sự cố thật, giảm concurrency/load, áp timeout và dùng retrieval hoặc model fallback đã được kiểm thử.
- Escalate cho service owner nếu P95 vượt 5000 ms hoặc không phục hồi sau 15 phút.
- Đóng incident khi P95 không quá 3000 ms liên tục 15 phút và trace mới không còn span bất thường.

## Daily Cost Budget Breach

- Tên: `daily_cost_budget_breach`.
- Severity: `warning`.
- SLI/SLO: `daily_cost_usd <= 2.5 USD` cho mỗi ngày UTC.
- Điều kiện: `daily_cost_usd > 2.5` trong 5 phút sau khi tổng hợp log theo ngày.
- Ảnh hưởng: không gây lỗi tức thời nhưng có thể làm hệ thống hết ngân sách hoặc bị giới hạn dịch vụ.
- Owner: `sre-alerts`.

### Kiểm tra

1. Xác nhận tổng cost và traffic trong ngày; phân biệt tăng do lưu lượng với tăng cost/request.
2. Nhóm `cost_usd`, `tokens_in`, `tokens_out` theo model và feature để tìm nguồn tăng.
3. Mở trace có cost cao và kiểm tra prompt/token, retry hoặc vòng lặp bất thường; kiểm tra incident `cost_spike` có đang bật không.

### Mitigation và đóng sự cố

- Khi diễn tập, chạy `python scripts/inject_incident.py --scenario cost_spike --disable`.
- Với sự cố thật, áp quota/rate limit; chuyển workload phù hợp sang model rẻ hơn và giới hạn output token theo policy.
- Escalate cho product owner khi dự báo vượt 120% ngân sách ngày hoặc chưa tìm được nguồn tăng sau 15 phút.
- Đóng incident khi đã loại bỏ nguồn tăng, cost/request trở về baseline và ghi nhận biện pháp ngăn tái diễn.

## Quy trình chung

Mọi incident phải ghi thời điểm phát hiện, alert, người xử lý, các `correlation_id`/trace ID liên quan, root cause, mitigation và preventive action. Không đưa secret hoặc PII vào ticket hay evidence.
