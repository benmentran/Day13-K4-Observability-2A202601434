# Dashboard Specification

Contract có thể kiểm tra bằng máy nằm tại `config/dashboard.yaml`. Hướng dẫn dựng và kiểm tra runtime nằm tại [DASHBOARD_SETUP.md](DASHBOARD_SETUP.md).

Dashboard chính cần đủ 6 nhóm thông tin:

1. **Latency P50/P95/P99** - Thời gian phản hồi theo percentile
2. **Traffic** - Request count hoặc QPS
3. **Error rate** - Tỷ lệ lỗi và breakdown theo loại lỗi (CP1/CP2: error_rate_pct metric)
4. **Cost** - Chi phí theo thời gian
5. **Tokens** - Tổng token input/output
6. **Quality proxy** - Điểm chất lượng phản hồi

## Metrics Implementation (CP1/CP2)

### Error Rate Calculation
```
error_rate_pct = (TOTAL_ERRORS / TOTAL_REQUESTS) * 100
```

Metrics được track trong `app/metrics.py`:
- `TOTAL_REQUESTS`: Tổng số request (tăng khi gọi `record_request()`)
- `TOTAL_ERRORS`: Tổng số lỗi (tăng khi gọi `record_error()`)
- `error_rate_pct`: Tính toán trong `snapshot()` và trả về dưới dạng phần trăm

Tiêu chuẩn trình bày:

- Khoảng thời gian mặc định: 1 giờ.
- Tự refresh mỗi 15–30 giây nếu công cụ hỗ trợ.
- Có threshold hoặc SLO line.
- Ghi rõ đơn vị.
- Chỉ giữ 6–8 panel quan trọng ở lớp chính.
- Screenshot phải nhìn được tên panel và khoảng thời gian.

Kiểm tra contract trước khi chụp evidence:

```bash
python scripts/validate_dashboard.py
```
