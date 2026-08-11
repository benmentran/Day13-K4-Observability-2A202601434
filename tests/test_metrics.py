from app.metrics import record_request, record_error, snapshot, percentile, TOTAL_REQUESTS, TOTAL_ERRORS


def test_percentile_basic() -> None:
    assert percentile([100, 200, 300, 400], 50) >= 100


def test_error_rate_basic() -> None:
    record_request(latency_ms=100, cost_usd=0.001, tokens_in=50, tokens_out=20, quality_score=0.8)
    record_request(latency_ms=150, cost_usd=0.002, tokens_in=60, tokens_out=25, quality_score=0.7)
    record_error("timeout")
    snap = snapshot()
    assert "error_rate_pct" in snap
    assert snap["error_rate_pct"] == 50.0
