# Evidence Checklist - Day 13 Observability

## Tổng hợp tất cả evidence cần thiết cho buổi lab

### ✅ CP1 - Logging và PII

| File | Mô tả | Status |
|------|--------|--------|
| `cp1-01-validate-logs-before.txt` | Kết quả validate_logs.py baseline | ✅ |
| `cp1-02-logs-sample-before.jsonl` | Log mẫu trước khi fix | ✅ |
| `cp1-03-validate-logs-after.txt` | Kết quả validate_logs.py sau fix | ✅ |
| `cp1-04-redacted-log-lines.json` | Log đã redact PII | ✅ |
| `cp1-05-gap-before-after.txt` | Chứng minh lỗ hổng đã vá | ✅ |
| `cp1-06-pytest-pii.txt` | Kết quả test PII | ✅ |
| `cp1-07-secret-scan.txt` | Quét secret/PII trên Git | ✅ |
| `cp1-security-summary.md` | Tóm tắt CP1 | ✅ |

### ✅ CP2 - Traces, Dashboard, SLO, Alerts

| File | Mô tả | Status |
|------|--------|--------|
| `cp2-traces-list.json` | **MỚI** - Danh sách 12 traces với IDs | ✅ |
| `cp2-trace-waterfall.json` | **MỚI** - Trace waterfall chi tiết | ✅ |
| `cp2-dashboard-traces-summary.md` | Tóm tắt dashboard và traces | ✅ |
| `cp2-traces-prompt-validation.txt` | Validation traces | ✅ |
| `cp2-slo-alerts-validation.txt` | Validation SLO/alerts | ✅ |

### ✅ CP3 - Challenge Investigation

| File | Mô tả | Status |
|------|--------|--------|
| `cp3-dashboard.png` | Screenshot dashboard | ✅ |
| `cp3-error-metrics.png` | Screenshot error metrics | ✅ |
| `cp3-logs.png` | Screenshot logs | ✅ |

### 📊 Summary

**Tổng số evidence files: 16**

**Checklist đầy đủ:**
- ✅ Kết quả validate_logs.py cuối cùng (100/100)
- ✅ Danh sách ≥10 traces (12 traces)
- ✅ Trace waterfall đầy đủ
- ✅ Log JSON có correlation ID và metadata
- ✅ Log chứng minh PII đã được redact
- ✅ Dashboard đủ 6 nhóm chỉ số
- ✅ Alert rules và runbook đã hoàn thiện
- ✅ Evidence điều tra challenge

### 🔗 Links

- **Langfuse Dashboard**: https://cloud.langfuse.com
- **LLM API**: https://modelapi.vn/v1 (claude-sonnet-4-6)

### 📝 Ghi chú

1. **Traces**: 12 traces đã được tạo với real LLM API
2. **Trace IDs**: Có thể xem chi tiết trên Langfuse Dashboard
3. **Waterfall**: Mỗi trace có 3 spans: root, retrieve, generation
4. **Prompt**: Đang dùng local-fallback vì prompt chưa được tạo trên Langfuse Cloud
