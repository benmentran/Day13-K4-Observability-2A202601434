from __future__ import annotations

from collections import Counter
from statistics import mean

REQUEST_LATENCIES: list[int] = []
REQUEST_COSTS: list[float] = []
REQUEST_TOKENS_IN: list[int] = []
REQUEST_TOKENS_OUT: list[int] = []
ERRORS: Counter[str] = Counter()
TRAFFIC: int = 0
QUALITY_SCORES: list[float] = []
TOTAL_REQUESTS: int = 0  # CP1: Track total requests for error_rate calculation
TOTAL_ERRORS: int = 0    # CP2: Track total errors for error_rate calculation


def record_request(latency_ms: int, cost_usd: float, tokens_in: int, tokens_out: int, quality_score: float) -> None:
    global TRAFFIC, TOTAL_REQUESTS
    TRAFFIC += 1
    TOTAL_REQUESTS += 1
    REQUEST_LATENCIES.append(latency_ms)
    REQUEST_COSTS.append(cost_usd)
    REQUEST_TOKENS_IN.append(tokens_in)
    REQUEST_TOKENS_OUT.append(tokens_out)
    QUALITY_SCORES.append(quality_score)



def reset() -> None:
    global TRAFFIC, TOTAL_REQUESTS, TOTAL_ERRORS
    REQUEST_LATENCIES.clear()
    REQUEST_COSTS.clear()
    REQUEST_TOKENS_IN.clear()
    REQUEST_TOKENS_OUT.clear()
    ERRORS.clear()
    QUALITY_SCORES.clear()
    TRAFFIC = 0
    TOTAL_REQUESTS = 0
    TOTAL_ERRORS = 0


def record_error(error_type: str) -> None:
    global ERRORS, TOTAL_ERRORS
    ERRORS[error_type] += 1
    TOTAL_ERRORS += 1



def percentile(values: list[int], p: int) -> float:
    if not values:
        return 0.0
    items = sorted(values)
    idx = max(0, min(len(items) - 1, round((p / 100) * len(items) + 0.5) - 1))
    return float(items[idx])



def snapshot() -> dict:
    error_rate_pct = (TOTAL_ERRORS / TOTAL_REQUESTS * 100) if TOTAL_REQUESTS > 0 else 0.0
    return {
        "traffic": TRAFFIC,
        "latency_p50": percentile(REQUEST_LATENCIES, 50),
        "latency_p95": percentile(REQUEST_LATENCIES, 95),
        "latency_p99": percentile(REQUEST_LATENCIES, 99),
        "avg_cost_usd": round(mean(REQUEST_COSTS), 4) if REQUEST_COSTS else 0.0,
        "total_cost_usd": round(sum(REQUEST_COSTS), 4),
        "tokens_in_total": sum(REQUEST_TOKENS_IN),
        "tokens_out_total": sum(REQUEST_TOKENS_OUT),
        "error_rate_pct": round(error_rate_pct, 2),
        "error_breakdown": dict(ERRORS),
        "quality_avg": round(mean(QUALITY_SCORES), 4) if QUALITY_SCORES else 0.0,
    }
