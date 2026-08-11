# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm:
- Repository URL:
- Commit SHA cuối:
- Thành viên và vai trò:

## 2. Kết quả kỹ thuật

- Điểm `validate_logs.py`:
- Tổng số traces:
- Số PII leak còn lại:
- Link/đường dẫn dashboard:

## 3. Logging và tracing

- Evidence correlation ID:
- Evidence PII redaction:
- Evidence trace waterfall:
- Giải thích một span đáng chú ý:

## 4. Prompt versioning

- Prompt name:
- Version/label baseline:
- Version/label candidate:
- Trace ID của mỗi version:
- Bằng chứng đổi label hoặc rollback:

## 5. Dashboard, SLO và alerts

- Kết quả `validate_dashboard.py`:
- Evidence dashboard:
- SLO đã chọn và lý do: 4 SLI trên cửa sổ 28 ngày gồm P95 latency <= 3000 ms, error rate <= 2%, daily cost <= 2.5 USD và quality trung bình >= 0.75. Các ngưỡng khớp dashboard contract và bao phủ trải nghiệm, độ tin cậy, ngân sách và chất lượng AI; chi tiết tại `config/slo.yaml`.
- Alert rules và runbook: 3 symptom-based alerts cho error rate, P95 latency và daily cost tại `config/alert_rules.yaml`; quy trình triage, mitigation, escalation và tiêu chí đóng sự cố tại `docs/alerts.md`. Kết quả kiểm tra: `submission/evidence/cp2-slo-alerts-validation.txt`.

## 6. Điều tra challenge

- **Challenge ID:** day13-k4-observability-v1
- **Incident:** rag_slow (RAG retrieval thêm 2.5s delay)
- **Triệu chứng từ metrics:**
  - `latency_p95: 3850ms` - vượt ngưỡng 2000ms trong challenge config
  - `latency_p50: 3444ms` - tăng ~3.5x so với baseline ~1000ms
  - `error_rate_pct: 0.0` - không có lỗi
  - Tất cả 5 requests đều có `feature: monitoring`
- **Trace ID liên quan:**
  - Correlation IDs: `req-7a0cc79e`, `req-f7cfd394`, `req-dd8f9311`, `req-a970fd65`, `req-b63da124`
  - Tất cả traces đều được ghi nhận với `model: claude-sonnet-4-5` và feature `monitoring`
  - Langfuse trace: span `run` bị kéo dài do RAG retrieve operation
- **Log line/correlation ID liên quan:**
  - `{"event": "incident_enabled", "payload": {"name": "rag_slow"}, "correlation_id": "req-8beccf90"}` (bật incident)
  - `{"event": "response_sent", "latency_ms": 3850, "correlation_id": "req-a970fd65", "session_id": "k4-challenge-s01"}`
- **Root cause:**
  - Khi incident `rag_slow` được bật, `mock_rag.py` thực hiện `time.sleep(2.5)` trước khi retrieve documents
  - Điều này làm tăng latency từ ~1s (baseline) lên ~3.5s, vượt ngưỡng SLO
  - RAG là bottleneck chính - LLM generation chỉ mất ~0.9-1.0s
- **Fix action:**
  - Tắt incident ngay lập tức: `python scripts/inject_incident.py --scenario rag_slow --disable`
  - Verify latency trở lại baseline sau khi disable
- **Preventive measure:**
  - Thêm sub-component trace cho RAG `retrieve()` operation để phân biệt retrieval vs generation latency
  - Cấu hình alert riêng cho RAG latency với ngưỡng 500ms
  - Implement circuit breaker cho vector store để graceful degradation
  - Giám sát chi tiết hơn: tách metrics cho `rag_retrieve_latency_ms` và `llm_generate_latency_ms`

## 7. Đóng góp cá nhân

Với mỗi thành viên, ghi rõ nhiệm vụ và link commit/PR tương ứng.

| Thành viên | Phần việc | Commit/PR | Điều đã học |
|---|---|---|---|
| | | | |
