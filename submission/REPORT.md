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

- Challenge ID:
- Triệu chứng từ metrics:
- Trace ID liên quan:
- Log line/correlation ID liên quan:
- Root cause:
- Fix action:
- Preventive measure:

## 7. Đóng góp cá nhân

Với mỗi thành viên, ghi rõ nhiệm vụ và link commit/PR tương ứng.

| Thành viên | Phần việc | Commit/PR | Điều đã học |
|---|---|---|---|
| | | | |
