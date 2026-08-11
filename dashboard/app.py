"""Dashboard Day 13 AI Observability.

Chay:  streamlit run dashboard/app.py
Can:   python -m pip install -r dashboard/requirements.txt

Nguon chuan 6 panel: data/logs.jsonl (xem config/dashboard.yaml).
Langfuse dung o tab Deep-dive de mo trace va kiem tra prompt version.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yaml
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(REPO_ROOT / ".env")

LOG_PATH = Path(os.getenv("LOG_PATH", "data/logs.jsonl"))
if not LOG_PATH.is_absolute():
    LOG_PATH = REPO_ROOT / LOG_PATH
DASHBOARD_YAML = REPO_ROOT / "config" / "dashboard.yaml"
CHALLENGE_JSON = REPO_ROOT / "config" / "challenge.json"

st.set_page_config(page_title="Day 13 AI Observability", layout="wide")

SLO: dict[str, dict[str, Any]] = {
    "latency": {"value": 3000, "op": "lte", "unit": "ms"},
    "traffic": {"value": 1, "op": "gte", "unit": "rpm"},
    "errors": {"value": 2, "op": "lte", "unit": "%"},
    "cost": {"value": 2.5, "op": "lte", "unit": "USD"},
    "tokens": {"value": 50000, "op": "lte", "unit": "tokens"},
    "quality": {"value": 0.75, "op": "gte", "unit": "score"},
}


def _load_logs() -> pd.DataFrame:
    if not LOG_PATH.exists():
        return pd.DataFrame()
    rows: list[dict] = []
    text = LOG_PATH.read_text(encoding="utf-8")
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        try:
            rows.append(json.loads(s))
        except json.JSONDecodeError:
            continue
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["ts"] = pd.to_datetime(df["ts"], utc=True, errors="coerce")
    return df.dropna(subset=["ts"]).sort_values("ts").reset_index(drop=True)


def _filter_window(df: pd.DataFrame, minutes: int | None) -> pd.DataFrame:
    if df.empty or minutes is None:
        return df
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    return df[df["ts"] >= cutoff]


def _hline_color(op: str) -> str:
    return "#1b5e20" if op == "gte" else "#c62828"


def _slo_label(pid: str) -> str:
    s = SLO[pid]
    sym = "≥" if s["op"] == "gte" else "≤"
    return f"SLO {sym} {s['value']} {s['unit']}"


def _threshold_fig(fig: go.Figure, pid: str) -> go.Figure:
    s = SLO[pid]
    fig.add_hline(
        y=s["value"],
        line_dash="dash",
        line_color=_hline_color(s["op"]),
        annotation_text=_slo_label(pid),
        annotation_position="top left",
        annotation_font_color=_hline_color(s["op"]),
    )
    return fig


def _fig_base(height: int = 260) -> dict:
    return dict(
        height=height,
        margin=dict(l=8, r=8, t=32, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(size=11),
    )


def _ts_floor(ts: pd.Series) -> pd.Series:
    return ts.dt.floor("1min")


def _slo_ok(pid: str, val: float) -> bool:
    s = SLO[pid]
    if s["op"] == "lte":
        return val <= s["value"]
    return val >= s["value"]


def _card(col: Any, label: str, value: str, unit: str, ok: bool) -> None:
    color = "#2e7d32" if ok else "#c62828"
    tag = "SLO OK" if ok else "SLO FAIL"
    col.markdown(
        f"""<div style="padding:8px 12px;border-radius:8px;border:1px solid #e0e0e0;background:#fafafa">
<div style="font-size:0.85rem;color:#666">{label}</div>
<div style="font-size:1.5rem;font-weight:700;margin:2px 0">{value} <span style="font-size:0.8rem;color:#999">{unit}</span></div>
<div style="color:{color};font-size:0.75rem;font-weight:600">{tag}</div>
</div>""",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
st.sidebar.title("Dieu khien")
_DURATION_OPTIONS = {
    "15 phut": 15,
    "30 phut": 30,
    "60 phut (mac dinh)": 60,
    "120 phut": 120,
    "Tat ca": None,
}
sel = st.sidebar.selectbox("Time range", list(_DURATION_OPTIONS.keys()), index=2)
window_min = _DURATION_OPTIONS[sel]
auto_refresh = st.sidebar.checkbox("Tu lam moi moi 30 giay", value=False)

st.sidebar.markdown("---")
st.sidebar.subheader("SLO / Threshold")
for pid in SLO:
    st.sidebar.caption(f"**{pid}**: {_slo_label(pid)}")

if CHALLENGE_JSON.exists():
    try:
        challenge = json.loads(CHALLENGE_JSON.read_text(encoding="utf-8"))
        st.sidebar.markdown("---")
        st.sidebar.caption(f"Challenge: `{challenge.get('challenge_id','')}`")
        st.sidebar.caption(f"Incident: `{challenge.get('incident','')}`")
        st.sidebar.caption(
            f"Threshold: `{challenge.get('latency_threshold_ms','')} ms`"
        )
    except Exception:
        pass

# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------
st.title("Day 13 AI Observability")
st.caption(
    f"Nguon: `{LOG_PATH}` | Contract: `config/dashboard.yaml` | Refresh: "
    f"{'30s' if auto_refresh else 'manual'}"
)


# ---------------------------------------------------------------------------
# Tab: 6 Panel (logs.jsonl)
# ---------------------------------------------------------------------------
@st.fragment(run_every=30 if auto_refresh else None)
def _render_panels() -> None:
    df = _load_logs()
    if df.empty:
        st.info(
            "Chua co log. Chay API va load test de sinh du lieu:\n\n"
            "```\nuvicorn app.main:app --reload --env-file .env\n"
            "python scripts/load_test.py --concurrency 5\n```"
        )
        return

    wdf = _filter_window(df, window_min)
    received = wdf[wdf["event"] == "request_received"]
    sent = wdf[wdf["event"] == "response_sent"]
    failed = wdf[wdf["event"] == "request_failed"]

    total_recv = len(received)
    total_sent = len(sent)
    total_fail = len(failed)

    if total_sent > 0:
        p50 = float(sent["latency_ms"].quantile(0.5))
        p95 = float(sent["latency_ms"].quantile(0.95))
        p99 = float(sent["latency_ms"].quantile(0.99))
    else:
        p50 = p95 = p99 = 0.0

    error_rate = (total_fail / total_recv * 100) if total_recv else 0.0
    cost_total = float(sent["cost_usd"].sum()) if "cost_usd" in sent else 0.0
    ti_total = int(sent["tokens_in"].sum()) if "tokens_in" in sent else 0
    to_total = int(sent["tokens_out"].sum()) if "tokens_out" in sent else 0
    q_mean = float(sent["quality_score"].mean()) if "quality_score" in sent else 0.0
    minutes_active = (
        (wdf["ts"].max() - wdf["ts"].min()).total_seconds() / 60
        if len(wdf) > 1
        else 0
    )
    avg_rpm = total_recv / max(minutes_active, 1) if minutes_active > 0 else total_recv

    # --- Metric cards row ---
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    _card(c1, "Latency P95", f"{p95:.0f}", "ms", _slo_ok("latency", p95))
    _card(c2, "Traffic", f"{avg_rpm:.1f}", "rpm", _slo_ok("traffic", avg_rpm))
    _card(c3, "Error rate", f"{error_rate:.2f}", "%", _slo_ok("errors", error_rate))
    _card(c4, "Cost total", f"${cost_total:.3f}", "USD", _slo_ok("cost", cost_total))
    _card(c5, "Tokens total", f"{ti_total + to_total:,}", "tok", _slo_ok("tokens", ti_total + to_total))
    _card(c6, "Quality avg", f"{q_mean:.2f}", "score", _slo_ok("quality", q_mean))

    st.markdown("---")

    # --- Row 1: Latency, Traffic, Errors ---
    rc1, rc2, rc3 = st.columns(3)

    # 1) Latency
    with rc1:
        st.markdown("**Latency percentiles**")
        if total_sent > 0:
            gb = sent.groupby(_ts_floor(sent["ts"]))["latency_ms"]
            idx = sorted(gb.mean().index)
            fig = go.Figure()
            for q, name, color in [
                (0.5, "P50", "#90a4ae"),
                (0.95, "P95", "#1565c0"),
                (0.99, "P99", "#e65100"),
            ]:
                vals = [float(gb.get_group(t).quantile(q)) for t in idx] if idx else []
                fig.add_trace(go.Scatter(x=idx, y=vals, name=name, mode="lines+markers", line=dict(width=2, color=color)))
            fig = _threshold_fig(fig, "latency")
            fig.update_layout(**_fig_base(), yaxis_title="ms", legend=dict(orientation="h", y=1.12))
        else:
            fig = go.Figure()
            fig.add_annotation(text="No data", showarrow=False)
            fig.update_layout(**_fig_base())
        st.plotly_chart(fig, use_container_width=True)

    # 2) Traffic
    with rc2:
        st.markdown("**Request traffic**")
        if total_recv > 0:
            gb_r = received.groupby(_ts_floor(received["ts"])).size()
            idx_r = sorted(gb_r.index)
            vals_r = [int(gb_r[t]) for t in idx_r]
            fig = go.Figure(go.Bar(x=idx_r, y=vals_r, marker_color="#1976d2"))
            fig = _threshold_fig(fig, "traffic")
            fig.update_layout(**_fig_base(), yaxis_title="req/min")
        else:
            fig = go.Figure()
            fig.add_annotation(text="No data", showarrow=False)
            fig.update_layout(**_fig_base())
        st.plotly_chart(fig, use_container_width=True)

    # 3) Errors
    with rc3:
        st.markdown("**Error rate & breakdown**")
        if total_recv > 0:
            gb_r = received.groupby(_ts_floor(received["ts"])).size()
            gb_f = failed.groupby(_ts_floor(failed["ts"])).size() if total_fail > 0 else pd.Series(dtype=int)
            idx_e = sorted(set(gb_r.index) | set(gb_f.index))
            r_vals = [int(gb_r.get(t, 0)) for t in idx_e]
            f_vals = [int(gb_f.get(t, 0)) for t in idx_e]
            rate_vals = [
                (f / r * 100) if r > 0 else 0.0 for f, r in zip(f_vals, r_vals)
            ]
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=idx_e, y=rate_vals, name="error rate", mode="lines+markers", line=dict(color="#c62828")))
            fig = _threshold_fig(fig, "errors")
            fig.update_layout(**_fig_base(), yaxis_title="%", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
            if total_fail > 0:
                bd = failed.groupby("error_type", dropna=False).size().sort_values(ascending=True)
                fig2 = go.Figure(go.Bar(x=bd.values, y=bd.index, orientation="h", marker_color="#e57373"))
                fig2.update_layout(**{"height": 140, "margin": dict(l=8, r=8, t=4, b=8), "paper_bgcolor": "rgba(0,0,0,0)", "plot_bgcolor": "rgba(0,0,0,0)", "font": dict(size=11)})
                st.plotly_chart(fig2, use_container_width=True)
        else:
            fig = go.Figure()
            fig.add_annotation(text="No data", showarrow=False)
            fig.update_layout(**_fig_base())
            st.plotly_chart(fig, use_container_width=True)

    # --- Row 2: Cost, Tokens, Quality ---
    rc4, rc5, rc6 = st.columns(3)

    # 4) Cost
    with rc4:
        st.markdown("**Cost over time**")
        if total_sent > 0:
            gb_c = sent.groupby(_ts_floor(sent["ts"]))["cost_usd"].sum()
            idx_c = sorted(gb_c.index)
            vals_c = [float(gb_c[t]) for t in idx_c]
            fig = go.Figure(go.Bar(x=idx_c, y=vals_c, marker_color="#388e3c"))
            fig.update_layout(**_fig_base(), yaxis_title="USD")
        else:
            fig = go.Figure()
            fig.add_annotation(text="No data", showarrow=False)
            fig.update_layout(**_fig_base())
        st.plotly_chart(fig, use_container_width=True)

    # 5) Tokens
    with rc5:
        st.markdown("**Input and output tokens**")
        if total_sent > 0:
            gb_in = sent.groupby(_ts_floor(sent["ts"]))["tokens_in"].sum()
            gb_out = sent.groupby(_ts_floor(sent["ts"]))["tokens_out"].sum()
            idx_t = sorted(set(gb_in.index) | set(gb_out.index))
            in_v = [int(gb_in.get(t, 0)) for t in idx_t]
            out_v = [int(gb_out.get(t, 0)) for t in idx_t]
            fig = go.Figure()
            fig.add_trace(go.Bar(x=idx_t, y=in_v, name="input", marker_color="#42a5f5"))
            fig.add_trace(go.Bar(x=idx_t, y=out_v, name="output", marker_color="#ab47bc"))
            fig.update_layout(barmode="stack", **_fig_base(), yaxis_title="tokens", legend=dict(orientation="h", y=1.12))
        else:
            fig = go.Figure()
            fig.add_annotation(text="No data", showarrow=False)
            fig.update_layout(**_fig_base())
        st.plotly_chart(fig, use_container_width=True)

    # 6) Quality
    with rc6:
        st.markdown("**Quality proxy**")
        if total_sent > 0:
            gb_q = sent.groupby(_ts_floor(sent["ts"]))["quality_score"].mean()
            idx_q = sorted(gb_q.index)
            vals_q = [float(gb_q[t]) for t in idx_q]
            fig = go.Figure(go.Scatter(x=idx_q, y=vals_q, mode="lines+markers", line=dict(color="#7b1fa2")))
            fig = _threshold_fig(fig, "quality")
            fig.update_layout(**_fig_base(), yaxis_title="score", yaxis_range=[0, 1.05])
        else:
            fig = go.Figure()
            fig.add_annotation(text="No data", showarrow=False)
            fig.update_layout(**_fig_base())
        st.plotly_chart(fig, use_container_width=True)


_render_panels()

# ---------------------------------------------------------------------------
# Tab: Langfuse deep-dive
# ---------------------------------------------------------------------------
def _render_langfuse(logs_df: pd.DataFrame) -> None:
    host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com").rstrip("/")
    pk = os.getenv("LANGFUSE_PUBLIC_KEY", "")
    sk = os.getenv("LANGFUSE_SECRET_KEY", "")

    if not pk or not sk:
        st.info("Chua co LANGFUSE_PUBLIC_KEY/SECRET_KEY trong .env.")
        st.code("LANGFUSE_PUBLIC_KEY=pk-...\nLANGFUSE_SECRET_KEY=sk-...")
        return

    try:
        from langfuse import Langfuse

        client = Langfuse()
        res = client.api.trace.list(limit=50)
        data = res.to_dict().get("data", []) if hasattr(res, "to_dict") else []
    except Exception as exc:
        st.warning(f"Khong ket noi duoc Langfuse ({type(exc).__name__}). Kiem tra key va host.")
        return

    if not data:
        st.info("Chua co trace nao. Chay API + load_test truoc.")
        return

    project_id = None
    try:
        proj = client.api.projects.list().to_dict().get("data", [])
        if proj:
            project_id = proj[0].get("id")
    except Exception:
        pass

    trace_rows = []
    for t in data:
        meta = t.get("metadata") or {}
        usage = t.get("usage") or {}
        tid = t.get("id", "")
        ts_raw = t.get("timestamp", "")
        session_id = t.get("sessionId") or ""
        trace_rows.append(
            {
                "trace_id": tid,
                "timestamp": ts_raw,
                "name": t.get("name", ""),
                "latency_ms": t.get("latency"),
                "total_cost_usd": t.get("totalCost"),
                "tokens_in": usage.get("input"),
                "tokens_out": usage.get("output"),
                "session_id": session_id,
                "prompt_name": meta.get("prompt_name", ""),
                "prompt_label": meta.get("prompt_label", ""),
                "prompt_version": meta.get("prompt_version", ""),
                "prompt_source": meta.get("prompt_source", ""),
                "url": f"{host}/project/{project_id}/traces/{tid}" if project_id else "",
            }
        )

    tdf = pd.DataFrame(trace_rows)

    if not logs_df.empty and "session_id" in logs_df.columns:
        corr_ids = []
        for _, tr in tdf.iterrows():
            sid = tr["session_id"]
            ts_str = tr["timestamp"]
            if not sid or not ts_str:
                corr_ids.append("")
                continue
            try:
                tr_ts = pd.to_datetime(ts_str, utc=True)
            except Exception:
                corr_ids.append("")
                continue
            mask = (logs_df["session_id"] == sid) & (
                (logs_df["ts"] - tr_ts).dt.total_seconds().abs() <= 120
            )
            matches = logs_df[mask]
            if not matches.empty:
                best = matches.iloc[-1]
                corr_ids.append(str(best.get("correlation_id", "")))
            else:
                corr_ids.append("")
        tdf["log_correlation_id"] = corr_ids

    st.dataframe(
        tdf,
        column_config={
            "url": st.column_config.LinkColumn("Langfuse", display_text="mo"),
            "trace_id": st.column_config.TextColumn("Trace ID"),
            "timestamp": st.column_config.TextColumn("Thoi gian"),
            "latency_ms": st.column_config.NumberColumn("Latency (ms)"),
            "total_cost_usd": st.column_config.NumberColumn("Cost (USD)", format="%.4f"),
            "tokens_in": st.column_config.NumberColumn("Tok in"),
            "tokens_out": st.column_config.NumberColumn("Tok out"),
            "session_id": st.column_config.TextColumn("Session"),
            "prompt_name": st.column_config.TextColumn("Prompt"),
            "prompt_label": st.column_config.TextColumn("Label"),
            "prompt_version": st.column_config.TextColumn("Version"),
            "prompt_source": st.column_config.TextColumn("Source"),
            "log_correlation_id": st.column_config.TextColumn("Log Corr ID"),
            "name": st.column_config.TextColumn("Name"),
        },
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("---")
    st.caption("Trace -> Log: dung session_id va timestamp de ket noi sang data/logs.jsonl.")


tab_main, tab_trace = st.tabs(["6 panel (logs.jsonl)", "Langfuse deep-dive"])

with tab_main:
    pass  # already rendered by _render_panels above

with tab_trace:
    _render_langfuse(_load_logs())
