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
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(REPO_ROOT / ".env")

LOG_PATH = Path(os.getenv("LOG_PATH", "data/logs.jsonl"))
if not LOG_PATH.is_absolute():
    LOG_PATH = REPO_ROOT / LOG_PATH
CHALLENGE_JSON = REPO_ROOT / "config" / "challenge.json"

st.set_page_config(
    page_title="Day 13 AI Observability",
    layout="wide",
    page_icon="📊"
)

# Dark theme palette
COLORS = {
    "primary": "#3B82F6",
    "secondary": "#8B5CF6",
    "success": "#10B981",
    "danger": "#EF4444",
    "warning": "#F59E0B",
    "info": "#06B6D4",
    "purple": "#A78BFA",
    "pink": "#F472B6",
    "cyan": "#22D3EE",
    "gray": "#9CA3AF",
    
    # Dark theme
    "bg_dark": "#0F172A",
    "bg_card": "#1E293B",
    "bg_elevated": "#334155",
    "border": "#334155",
    "text_primary": "#F1F5F9",
    "text_secondary": "#94A3B8",
    "text_muted": "#64748B",
}

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
    return COLORS["success"] if op == "gte" else COLORS["danger"]


def _slo_label(pid: str) -> str:
    s = SLO[pid]
    sym = "≥" if s["op"] == "gte" else "≤"
    return f"SLO {sym} {s['value']} {s['unit']}"


def _threshold_fig(fig: go.Figure, pid: str) -> go.Figure:
    s = SLO[pid]
    fig.add_hline(
        y=s["value"],
        line_dash="dot",
        line_width=2,
        line_color=COLORS["warning"],
        annotation_text=_slo_label(pid),
        annotation_position="top left",
        annotation_font_color=COLORS["warning"],
        annotation_font_size=11,
        annotation_bgcolor="rgba(15,23,42,0.8)",
    )
    return fig


def _fig_base(height: int = 280, showlegend: bool | None = None) -> dict:
    layout = dict(
        height=height,
        margin=dict(l=50, r=30, t=40, b=40),
        paper_bgcolor=COLORS["bg_card"],
        plot_bgcolor=COLORS["bg_card"],
        font=dict(size=12, color=COLORS["text_primary"]),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(0,0,0,0)",
            font=dict(color=COLORS["text_secondary"]),
        ),
    )
    if showlegend is not None:
        layout["showlegend"] = showlegend
        if not showlegend:
            layout.pop("legend", None)
    return layout


def _ts_floor(ts: pd.Series) -> pd.Series:
    return ts.dt.floor("1min")


def _slo_ok(pid: str, val: float) -> bool:
    s = SLO[pid]
    if s["op"] == "lte":
        return val <= s["value"]
    return val >= s["value"]


def _card(col: Any, label: str, value: str, unit: str, ok: bool, icon: str = "") -> None:
    bg_color = "rgba(16,185,129,0.15)" if ok else "rgba(239,68,68,0.15)"
    border_color = COLORS["success"] if ok else COLORS["danger"]
    text_color = COLORS["success"] if ok else COLORS["danger"]
    tag = "✓ SLO OK" if ok else "✗ SLO FAIL"
    
    col.markdown(
        f"""
        <div style="
            padding:18px 22px;
            border-radius:14px;
            background:{bg_color};
            border: 1px solid {border_color}40;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            margin: 4px 0;
            transition: transform 0.2s;
        ">
            <div style="font-size:0.75rem;color:{COLORS['text_secondary']};text-transform:uppercase;font-weight:600;letter-spacing:0.05em;">
                {icon} {label}
            </div>
            <div style="font-size:1.9rem;font-weight:700;color:{COLORS['text_primary']};margin:6px 0;line-height:1.1;">
                {value} <span style="font-size:0.85rem;color:{COLORS['text_muted']};font-weight:500">{unit}</span>
            </div>
            <div style="color:{text_color};font-size:0.75rem;font-weight:600;">{tag}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# Custom CSS - Dark theme
st.markdown(f"""
<style>
    /* Main app background */
    .stApp {{
        background-color: {COLORS['bg_dark']};
    }}
    
    /* Headers */
    h1, h2, h3 {{
        color: {COLORS['text_primary']} !important;
        font-weight: 700 !important;
    }}
    
    /* Sidebar */
    [data-testid="stSidebar"] {{
        background-color: {COLORS['bg_card']};
        border-right: 1px solid {COLORS['border']};
    }}
    
    [data-testid="stSidebar"] * {{
        color: {COLORS['text_primary']} !important;
    }}
    
    /* Metric numbers */
    [data-testid="stMetricValue"] {{
        font-size: 1.5rem !important;
        font-weight: 700 !important;
        color: {COLORS['text_primary']} !important;
    }}
    
    [data-testid="stMetricLabel"] {{
        color: {COLORS['text_secondary']} !important;
    }}
    
    /* Tabs */
    .stTabs button {{
        font-weight: 600;
        color: {COLORS['text_secondary']};
    }}
    
    .stTabs button[aria-selected="true"] {{
        color: {COLORS['primary']} !important;
        border-bottom-color: {COLORS['primary']} !important;
    }}
    
    /* Info/Success/Warning boxes via markdown */
    .stAlert {{
        background-color: {COLORS['bg_card']} !important;
        color: {COLORS['text_primary']} !important;
        border: 1px solid {COLORS['border']};
    }}
    
    /* Caption */
    p, .stCaption {{
        color: {COLORS['text_secondary']} !important;
    }}
    
    /* Code blocks */
    code, pre {{
        background-color: {COLORS['bg_elevated']} !important;
        color: {COLORS['text_primary']} !important;
        border-radius: 8px !important;
        border: 1px solid {COLORS['border']};
    }}
    
    /* Expander */
    details {{
        background-color: {COLORS['bg_card']};
        border-radius: 12px;
        border: 1px solid {COLORS['border']};
    }}
    
    details summary {{
        color: {COLORS['text_primary']} !important;
    }}
    
    /* Divider */
    hr {{
        border: none;
        border-top: 1px solid {COLORS['border']};
        margin: 16px 0;
    }}
    
    /* Dataframe */
    [data-testid="stDataFrame"] {{
        background-color: {COLORS['bg_card']};
        border-radius: 12px;
        padding: 8px;
    }}
    
    /* Selectbox, checkbox */
    .stSelectbox label, .stCheckbox label {{
        color: {COLORS['text_primary']} !important;
    }}
    
    /* Buttons */
    .stButton button {{
        background-color: {COLORS['primary']};
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
    }}
    
    .stButton button:hover {{
        background-color: #2563EB;
    }}
    
    /* Markdown links */
    a {{
        color: {COLORS['primary']} !important;
    }}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🎛️ Điều khiển")
    st.markdown("---")
    
    _DURATION_OPTIONS = {
        "15 phút": 15,
        "30 phút": 30,
        "60 phút (mặc định)": 60,
        "120 phút": 120,
        "Tất cả": None,
    }
    sel = st.selectbox("⏰ Khoảng thời gian", list(_DURATION_OPTIONS.keys()), index=2)
    window_min = _DURATION_OPTIONS[sel]
    auto_refresh = st.checkbox("🔄 Tự động làm mới (30s)", value=False)
    
    st.markdown("---")
    st.markdown("### 📏 Ngưỡng SLO")
    for pid in SLO:
        s = SLO[pid]
        icon = "✅" if s["op"] == "gte" else "⚠️"
        st.markdown(f"- **{pid}**: {icon} `{s['value']} {s['unit']}`")
    
    if CHALLENGE_JSON.exists():
        try:
            challenge = json.loads(CHALLENGE_JSON.read_text(encoding="utf-8"))
            st.markdown("---")
            st.markdown("### 🏁 Challenge Info")
            st.markdown(f"**ID:** `{challenge.get('challenge_id','')}`")
            st.markdown(f"**Incident:** `{challenge.get('incident','')}`")
            st.markdown(f"**Threshold:** `{challenge.get('latency_threshold_ms','')} ms`")
        except Exception:
            pass
    
    st.markdown("---")
    st.markdown("### 📚 Liên kết nhanh")
    st.markdown("""
    - [🌐 Langfuse Cloud](https://cloud.langfuse.com)
    - [📖 API Docs](/docs)
    - [📁 Logs](data/logs.jsonl)
    """)


# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------
st.title("📊 Day 13 AI Observability Dashboard")
st.markdown("---")

# Status bar
col_status1, col_status2, col_status3 = st.columns(3)

with col_status1:
    if LOG_PATH.exists():
        log_lines = len(LOG_PATH.read_text(encoding="utf-8").strip().splitlines())
        log_size = LOG_PATH.stat().st_size / 1024
        st.markdown(f"""
        <div style="padding:10px 16px;border-radius:10px;background:rgba(16,185,129,0.1);border:1px solid rgba(16,185,129,0.3);">
            <span style="color:{COLORS['text_secondary']};font-size:0.85rem;">📁 Logs</span><br>
            <span style="color:{COLORS['text_primary']};font-weight:600;">{log_lines} dòng ({log_size:.1f} KB)</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="padding:10px 16px;border-radius:10px;background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.3);">
            <span style="color:{COLORS['danger']};font-weight:600;">⚠️ Chưa có file logs</span>
        </div>
        """, unsafe_allow_html=True)

with col_status2:
    st.markdown(f"""
    <div style="padding:10px 16px;border-radius:10px;background:{COLORS['bg_card']};border:1px solid {COLORS['border']};">
        <span style="color:{COLORS['text_secondary']};font-size:0.85rem;">📍 Nguồn</span><br>
        <span style="color:{COLORS['text_primary']};font-weight:600;">data/logs.jsonl</span>
    </div>
    """, unsafe_allow_html=True)

with col_status3:
    refresh_text = "🔄 Auto (30s)" if auto_refresh else "⏸️ Manual"
    st.markdown(f"""
    <div style="padding:10px 16px;border-radius:10px;background:{COLORS['bg_card']};border:1px solid {COLORS['border']};">
        <span style="color:{COLORS['text_secondary']};font-size:0.85rem;">🔄 Refresh</span><br>
        <span style="color:{COLORS['text_primary']};font-weight:600;">{refresh_text}</span>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")


# ---------------------------------------------------------------------------
# Tab: Dashboard
# ---------------------------------------------------------------------------
@st.fragment(run_every=30 if auto_refresh else None)
def _render_panels() -> None:
    df = _load_logs()
    
    if df.empty:
        st.markdown(f"""
        <div style="
            padding: 40px;
            border-radius: 16px;
            background: {COLORS['bg_card']};
            border-left: 4px solid {COLORS['warning']};
            text-align: center;
            margin: 20px 0;
        ">
            <h2 style="color: {COLORS['warning']}; margin-bottom: 16px;">⚠️ Chưa có dữ liệu</h2>
            <p style="color: {COLORS['text_secondary']}; font-size: 1.1rem; margin-bottom: 16px;">
                Chạy API và load test để sinh dữ liệu observability
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        col_cmd1, col_cmd2 = st.columns(2)
        with col_cmd1:
            st.markdown(f"""
            <div style="background:{COLORS['bg_card']};padding:16px;border-radius:12px;border:1px solid {COLORS['border']};">
                <h4 style="color:{COLORS['primary']};margin-top:0;">🚀 Khởi động</h4>
            </div>
            """, unsafe_allow_html=True)
            st.code("""# Terminal 1: Chạy API
uvicorn app.main:app --reload --env-file .env

# Terminal 2: Load test
python scripts/load_test.py --concurrency 5""")
        
        with col_cmd2:
            st.markdown(f"""
            <div style="background:{COLORS['bg_card']};padding:16px;border-radius:12px;border:1px solid {COLORS['border']};">
                <h4 style="color:{COLORS['secondary']};margin-top:0;">🧪 Quick Actions</h4>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("🧪 Test API Health", use_container_width=True, type="primary"):
                import requests
                try:
                    r = requests.get("http://127.0.0.1:8000/health", timeout=5)
                    st.json(r.json())
                except Exception as e:
                    st.error(f"Lỗi kết nối API: {e}")
            
            if st.button("📜 Hướng dẫn Load Test", use_container_width=True):
                st.info("Mở terminal mới và chạy: `python scripts/load_test.py --concurrency 5`")
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
    st.markdown("### 📈 Tổng quan Metrics")
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    _card(c1, "Latency P95", f"{p95:.0f}", "ms", _slo_ok("latency", p95), "⏱️")
    _card(c2, "Traffic", f"{avg_rpm:.1f}", "rpm", _slo_ok("traffic", avg_rpm), "📨")
    _card(c3, "Error Rate", f"{error_rate:.2f}", "%", _slo_ok("errors", error_rate), "❌")
    _card(c4, "Cost Total", f"{cost_total:.3f}", "USD", _slo_ok("cost", cost_total), "💰")
    _card(c5, "Tokens Total", f"{(ti_total + to_total):,}", "tok", _slo_ok("tokens", ti_total + to_total), "📝")
    _card(c6, "Quality Avg", f"{q_mean:.2f}", "", _slo_ok("quality", q_mean), "⭐")

    st.markdown("---")

    # --- Row 1: Latency, Traffic, Errors ---
    st.markdown("### 📉 Performance & Traffic")
    rc1, rc2, rc3 = st.columns(3)

    # 1) Latency
    with rc1:
        st.markdown("**⏱️ Latency (P50/P95/P99)**")
        if total_sent > 0:
            gb = sent.groupby(_ts_floor(sent["ts"]))["latency_ms"]
            idx = sorted(gb.mean().index)
            fig = go.Figure()
            for q, name, color in [
                (0.5, "P50", COLORS["gray"]),
                (0.95, "P95", COLORS["info"]),
                (0.99, "P99", COLORS["danger"]),
            ]:
                vals = [float(gb.get_group(t).quantile(q)) for t in idx] if idx else []
                fig.add_trace(go.Scatter(
                    x=idx, y=vals, name=name, 
                    mode="lines+markers", 
                    line=dict(width=3, color=color),
                    marker=dict(size=8, symbol="circle")
                ))
            fig = _threshold_fig(fig, "latency")
            fig.update_layout(
                **_fig_base(), 
                yaxis_title="ms", 
                hovermode="x unified",
                xaxis=dict(showgrid=True, gridcolor=COLORS["border"], zeroline=False),
                yaxis=dict(showgrid=True, gridcolor=COLORS["border"], zeroline=False),
            )
        else:
            fig = go.Figure()
            fig.add_annotation(text="No data", showarrow=False, font=dict(size=16, color=COLORS["text_secondary"]))
            fig.update_layout(**_fig_base(height=280))
        st.plotly_chart(fig, use_container_width=True, key="chart_latency")

    # 2) Traffic
    with rc2:
        st.markdown("**📨 Request Traffic**")
        if total_recv > 0:
            gb_r = received.groupby(_ts_floor(received["ts"])).size()
            idx_r = sorted(gb_r.index)
            vals_r = [int(gb_r[t]) for t in idx_r]
            fig = go.Figure(go.Bar(
                x=idx_r, y=vals_r, 
                marker_color=COLORS["primary"],
                marker_line_width=0,
            ))
            fig = _threshold_fig(fig, "traffic")
            fig.update_layout(
                **_fig_base(), 
                yaxis_title="requests/min",
                xaxis=dict(showgrid=True, gridcolor=COLORS["border"], zeroline=False),
                yaxis=dict(showgrid=True, gridcolor=COLORS["border"], zeroline=False),
                hovermode="x unified",
            )
        else:
            fig = go.Figure()
            fig.add_annotation(text="No data", showarrow=False, font=dict(size=16, color=COLORS["text_secondary"]))
            fig.update_layout(**_fig_base(height=280))
        st.plotly_chart(fig, use_container_width=True, key="chart_traffic")

    # 3) Errors
    with rc3:
        st.markdown("**❌ Error Rate**")
        if total_recv > 0:
            gb_r = received.groupby(_ts_floor(received["ts"])).size()
            gb_f = failed.groupby(_ts_floor(failed["ts"])).size() if total_fail > 0 else pd.Series(dtype=int)
            idx_e = sorted(set(gb_r.index) | set(gb_f.index))
            r_vals = [int(gb_r.get(t, 0)) for t in idx_e]
            f_vals = [int(gb_f.get(t, 0)) for t in idx_e]
            rate_vals = [(f / r * 100) if r > 0 else 0.0 for f, r in zip(f_vals, r_vals)]
            
            fig = go.Figure(go.Scatter(
                x=idx_e, y=rate_vals, name="Error Rate",
                mode="lines+markers", 
                line=dict(width=3, color=COLORS["danger"]),
                marker=dict(size=8, color=COLORS["danger"], symbol="circle"),
                fill='tozeroy', 
                fillcolor='rgba(239,68,68,0.15)'
            ))
            fig = _threshold_fig(fig, "errors")
            fig.update_layout(
                **_fig_base(height=280, showlegend=False), 
                yaxis_title="%",
                xaxis=dict(showgrid=True, gridcolor=COLORS["border"], zeroline=False),
                yaxis=dict(showgrid=True, gridcolor=COLORS["border"], zeroline=False),
                hovermode="x unified",
            )
            st.plotly_chart(fig, use_container_width=True, key="chart_error_rate")
            
            if total_fail > 0:
                bd = failed.groupby("error_type", dropna=False).size().sort_values(ascending=True)
                fig2 = go.Figure(go.Bar(
                    x=bd.values, y=bd.index, 
                    orientation="h", 
                    marker_color=COLORS["danger"],
                ))
                fig2.update_layout(
                    height=120, 
                    margin=dict(l=8, r=8, t=4, b=8), 
                    paper_bgcolor=COLORS["bg_card"], 
                    plot_bgcolor=COLORS["bg_card"],
                    font=dict(size=11, color=COLORS["text_primary"]),
                    xaxis=dict(showgrid=True, gridcolor=COLORS["border"], zeroline=False),
                    yaxis=dict(zeroline=False),
                    showlegend=False,
                )
                st.plotly_chart(fig2, use_container_width=True, key="chart_errors_breakdown")
        else:
            fig = go.Figure()
            fig.add_annotation(text="No data", showarrow=False, font=dict(size=16, color=COLORS["text_secondary"]))
            fig.update_layout(**_fig_base(height=280))
        st.plotly_chart(fig, use_container_width=True, key="chart_errors")

    # --- Row 2: Cost, Tokens, Quality ---
    st.markdown("### 💵 Cost & Quality")
    rc4, rc5, rc6 = st.columns(3)

    # 4) Cost
    with rc4:
        st.markdown("**💰 Cost Over Time**")
        if total_sent > 0:
            gb_c = sent.groupby(_ts_floor(sent["ts"]))["cost_usd"].sum()
            idx_c = sorted(gb_c.index)
            vals_c = [float(gb_c[t]) for t in idx_c]
            fig = go.Figure(go.Bar(
                x=idx_c, y=vals_c, 
                marker_color=COLORS["success"],
            ))
            fig.update_layout(
                **_fig_base(height=280), 
                yaxis_title="USD",
                xaxis=dict(showgrid=True, gridcolor=COLORS["border"], zeroline=False),
                yaxis=dict(showgrid=True, gridcolor=COLORS["border"], zeroline=False),
                hovermode="x unified",
            )
        else:
            fig = go.Figure()
            fig.add_annotation(text="No data", showarrow=False, font=dict(size=16, color=COLORS["text_secondary"]))
            fig.update_layout(**_fig_base(height=280))
        st.plotly_chart(fig, use_container_width=True, key="chart_cost")

    # 5) Tokens
    with rc5:
        st.markdown("**📝 Token Usage**")
        if total_sent > 0:
            gb_in = sent.groupby(_ts_floor(sent["ts"]))["tokens_in"].sum()
            gb_out = sent.groupby(_ts_floor(sent["ts"]))["tokens_out"].sum()
            idx_t = sorted(set(gb_in.index) | set(gb_out.index))
            in_v = [int(gb_in.get(t, 0)) for t in idx_t]
            out_v = [int(gb_out.get(t, 0)) for t in idx_t]
            fig = go.Figure()
            fig.add_trace(go.Bar(x=idx_t, y=in_v, name="Input", marker_color=COLORS["info"]))
            fig.add_trace(go.Bar(x=idx_t, y=out_v, name="Output", marker_color=COLORS["purple"]))
            fig.update_layout(
                barmode="stack", 
                **_fig_base(height=280), 
                yaxis_title="tokens",
                xaxis=dict(showgrid=True, gridcolor=COLORS["border"], zeroline=False),
                yaxis=dict(showgrid=True, gridcolor=COLORS["border"], zeroline=False),
                hovermode="x unified",
            )
        else:
            fig = go.Figure()
            fig.add_annotation(text="No data", showarrow=False, font=dict(size=16, color=COLORS["text_secondary"]))
            fig.update_layout(**_fig_base(height=280))
        st.plotly_chart(fig, use_container_width=True, key="chart_tokens")

    # 6) Quality
    with rc6:
        st.markdown("**⭐ Quality Score**")
        if total_sent > 0:
            gb_q = sent.groupby(_ts_floor(sent["ts"]))["quality_score"].mean()
            idx_q = sorted(gb_q.index)
            vals_q = [float(gb_q[t]) for t in idx_q]
            fig = go.Figure(go.Scatter(
                x=idx_q, y=vals_q, 
                mode="lines+markers", 
                line=dict(width=3, color=COLORS["purple"]),
                marker=dict(size=8, color=COLORS["purple"], symbol="circle"),
                fill='tozeroy', 
                fillcolor='rgba(139,92,246,0.15)'
            ))
            fig = _threshold_fig(fig, "quality")
            fig.update_layout(
                **_fig_base(height=280), 
                yaxis_title="score", 
                yaxis_range=[0, 1.05],
                xaxis=dict(showgrid=True, gridcolor=COLORS["border"], zeroline=False),
                yaxis=dict(showgrid=True, gridcolor=COLORS["border"], zeroline=False),
                hovermode="x unified",
            )
        else:
            fig = go.Figure()
            fig.add_annotation(text="No data", showarrow=False, font=dict(size=16, color=COLORS["text_secondary"]))
            fig.update_layout(**_fig_base(height=280))
        st.plotly_chart(fig, use_container_width=True, key="chart_quality")
    
    # --- Summary stats ---
    st.markdown("---")
    st.markdown("### 📊 Thống kê chi tiết")
    
    with st.expander("🔍 Xem chi tiết", expanded=False):
        col_sum1, col_sum2, col_sum3, col_sum4 = st.columns(4)
        with col_sum1:
            st.metric("Tổng Requests", total_recv)
        with col_sum2:
            pct = f"{total_sent/total_recv*100:.1f}%" if total_recv else "0%"
            st.metric("Thành công", total_sent, delta=pct)
        with col_sum3:
            st.metric("Thất bại", total_fail, delta=f"-{total_fail}" if total_fail else None, delta_color="inverse")
        with col_sum4:
            st.metric("Active Time", f"{minutes_active:.1f} phút")
        
        st.markdown("#### Latency Details")
        col_lat1, col_lat2, col_lat3 = st.columns(3)
        with col_lat1:
            st.metric("P50 Latency", f"{p50:.0f} ms")
        with col_lat2:
            st.metric("P95 Latency", f"{p95:.0f} ms")
        with col_lat3:
            st.metric("P99 Latency", f"{p99:.0f} ms")


_render_panels()


# ---------------------------------------------------------------------------
# Tab: Langfuse Traces
# ---------------------------------------------------------------------------
def _render_langfuse(logs_df: pd.DataFrame) -> None:
    st.markdown("### 🔍 Langfuse Traces")
    
    host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com").rstrip("/")
    pk = os.getenv("LANGFUSE_PUBLIC_KEY", "")
    sk = os.getenv("LANGFUSE_SECRET_KEY", "")

    if not pk or not sk:
        st.warning("⚠️ Chưa cấu hình Langfuse. Thêm vào `.env`:")
        st.code("""LANGFUSE_PUBLIC_KEY=pk-...
LANGFUSE_SECRET_KEY=sk-...
LANGFUSE_HOST=https://cloud.langfuse.com""")
        
        if not logs_df.empty:
            st.markdown("---")
            st.markdown("### 📜 Recent Logs (thay thế tạm)")
            recent = logs_df.tail(20)[["ts", "event", "session_id", "latency_ms", "tokens_in", "tokens_out"]]
            st.dataframe(recent, use_container_width=True, hide_index=True)
        return

    try:
        from langfuse import Langfuse
        client = Langfuse()
        res = client.api.trace.list(limit=50)
        data = res.to_dict().get("data", []) if hasattr(res, "to_dict") else []
    except Exception as exc:
        st.error(f"Không kết nối được Langfuse: {exc}")
        st.info("Kiểm tra LANGFUSE_HOST, PUBLIC_KEY, SECRET_KEY trong .env")
        return

    if not data:
        st.info("Chưa có trace nào. Chạy API + load_test trước.")
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
        trace_rows.append({
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
        })

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
            corr_ids.append(str(matches.iloc[-1].get("correlation_id", "")) if not matches.empty else "")
        tdf["log_correlation_id"] = corr_ids

    # Summary metrics
    st.markdown("#### 📊 Trace Summary")
    col_lf1, col_lf2, col_lf3, col_lf4 = st.columns(4)
    with col_lf1:
        st.metric("Tổng Traces", len(tdf))
    with col_lf2:
        avg_lat = tdf["latency_ms"].mean() if "latency_ms" in tdf else 0
        st.metric("Avg Latency", f"{avg_lat:.0f}ms")
    with col_lf3:
        total_cost = tdf["total_cost_usd"].sum() if "total_cost_usd" in tdf else 0
        st.metric("Total Cost", f"${total_cost:.4f}")
    with col_lf4:
        total_tokens = (tdf["tokens_in"].sum() + tdf["tokens_out"].sum()) if "tokens_in" in tdf else 0
        st.metric("Total Tokens", f"{total_tokens:,}")
    
    st.markdown("---")
    
    st.markdown("#### 📋 Traces List")
    st.dataframe(
        tdf,
        column_config={
            "url": st.column_config.LinkColumn("Mở", display_text="🔗 Mở trace"),
            "trace_id": st.column_config.TextColumn("Trace ID"),
            "timestamp": st.column_config.TextColumn("Thời gian"),
            "latency_ms": st.column_config.NumberColumn("Latency (ms)", format="%.0f"),
            "total_cost_usd": st.column_config.NumberColumn("Cost", format="$%.4f"),
            "tokens_in": st.column_config.NumberColumn("Input"),
            "tokens_out": st.column_config.NumberColumn("Output"),
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
    st.caption("💡 **Tip**: Dùng `session_id` và `timestamp` để kết nối trace với log trong `data/logs.jsonl`")


# Tabs
tab_main, tab_trace = st.tabs(["📊 Dashboard", "🔍 Langfuse Traces"])

with tab_main:
    pass

with tab_trace:
    _render_langfuse(_load_logs())
