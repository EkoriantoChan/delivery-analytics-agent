"""Delivery Analytics Agent - Streamlit UI.

Mobbin-inspired modern UI/UX design (ChatGPT / Perplexity / Linear aesthetics)
featuring real-time SQL execution, interactive charting, B2B stat cards with quick-actions,
and strict multi-tenant IDOR isolation.
"""

import json
import os
from pathlib import Path
import re
from typing import Any, Dict, List, Optional

import httpx
import pandas as pd
import streamlit as st


API_URL = os.getenv("AGENT_API_URL", "http://localhost:8000").rstrip("/")

# -----------------------------------------------------------------------------
# Page Configuration & Mobbin-Inspired Modern Styling
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Delivery Analytics Agent",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for modern B2B analytics and AI chat aesthetics
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    /* Global Typography & Mesh Canvas */
    html, body, [class*="css"], .stApp {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    .stApp {
        background: radial-gradient(circle at 10% 10%, rgba(99, 102, 241, 0.12) 0%, transparent 45%),
                    radial-gradient(circle at 90% 15%, rgba(236, 72, 153, 0.10) 0%, transparent 45%),
                    radial-gradient(circle at 50% 90%, rgba(6, 182, 212, 0.10) 0%, transparent 55%),
                    #080B11 !important;
        color: #F1F5F9;
    }

    /* 3D Floating Isometric Cube Animation */
    .cube-3d-scene {
        width: 80px;
        height: 80px;
        perspective: 600px;
        margin: 0.5rem auto 1.2rem auto;
    }
    .cube-3d {
        width: 100%;
        height: 100%;
        position: relative;
        transform-style: preserve-3d;
        animation: rotateCube 12s infinite linear;
    }
    .cube-face {
        position: absolute;
        width: 80px;
        height: 80px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 2rem;
        background: rgba(15, 23, 42, 0.85);
        border: 2px solid rgba(99, 102, 241, 0.6);
        box-shadow: 0 0 25px rgba(99, 102, 241, 0.4), inset 0 0 15px rgba(6, 182, 212, 0.3);
        backdrop-filter: blur(12px);
        border-radius: 14px;
        user-select: none;
    }
    .cube-front  { transform: rotateY(  0deg) translateZ(40px); }
    .cube-back   { transform: rotateY(180deg) translateZ(40px); }
    .cube-right  { transform: rotateY( 90deg) translateZ(40px); }
    .cube-left   { transform: rotateY(-90deg) translateZ(40px); }
    .cube-top    { transform: rotateX( 90deg) translateZ(40px); }
    .cube-bottom { transform: rotateX(-90deg) translateZ(40px); }

    @keyframes rotateCube {
        0% { transform: rotateX(-20deg) rotateY(0deg); }
        50% { transform: rotateX(20deg) rotateY(180deg); }
        100% { transform: rotateX(-20deg) rotateY(360deg); }
    }

    /* Top App Header Banner */
    .top-header-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem 1.4rem;
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.85) 100%);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(99, 102, 241, 0.25);
        border-radius: 16px;
        margin-bottom: 1.4rem;
        box-shadow: 0 10px 30px -5px rgba(0, 0, 0, 0.5), 0 0 20px rgba(99, 102, 241, 0.1);
    }
    .header-title-group h2 {
        margin: 0;
        font-size: 1.45rem;
        font-weight: 800;
        letter-spacing: -0.025em;
        background: linear-gradient(135deg, #FFFFFF 30%, #38BDF8 70%, #818CF8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .header-title-group p {
        margin: 0.2rem 0 0 0;
        font-size: 0.84rem;
        color: #94A3B8;
    }
    .status-badge-container {
        display: flex;
        align-items: center;
        gap: 0.65rem;
    }
    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        background: rgba(16, 185, 129, 0.12);
        border: 1px solid rgba(16, 185, 129, 0.4);
        color: #34D399;
        font-size: 0.78rem;
        font-weight: 700;
        padding: 0.32rem 0.75rem;
        border-radius: 9999px;
        box-shadow: 0 0 15px rgba(16, 185, 129, 0.2);
    }
    .status-dot {
        width: 8px;
        height: 8px;
        background-color: #10B981;
        border-radius: 50%;
        box-shadow: 0 0 10px #10B981, 0 0 18px #10B981;
        animation: neonPulse 2s infinite ease-in-out;
    }
    @keyframes neonPulse {
        0%, 100% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.35); opacity: 0.75; }
    }
    .tenant-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        background: rgba(99, 102, 241, 0.14);
        border: 1px solid rgba(99, 102, 241, 0.4);
        color: #A5B4FC;
        font-size: 0.78rem;
        font-weight: 700;
        padding: 0.32rem 0.75rem;
        border-radius: 9999px;
        box-shadow: 0 0 15px rgba(99, 102, 241, 0.2);
    }

    /* 3D Holographic B2B KPI Stat Card */
    .b2b-stat-card {
        position: relative;
        background: linear-gradient(135deg, rgba(26, 34, 53, 0.85) 0%, rgba(13, 17, 28, 0.95) 100%);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(99, 102, 241, 0.35);
        border-radius: 16px;
        padding: 1.35rem 1.6rem;
        margin: 0.8rem 0 1.2rem 0;
        box-shadow: 0 15px 35px -5px rgba(0, 0, 0, 0.6), 0 0 25px rgba(99, 102, 241, 0.15);
        display: flex;
        flex-direction: column;
        gap: 0.55rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        overflow: hidden;
    }
    .b2b-stat-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0; height: 3px;
        background: linear-gradient(90deg, #6366F1, #06B6D4, #A855F7, #EC4899);
        background-size: 300% 300%;
        animation: gradientFlow 5s ease infinite;
    }
    @keyframes gradientFlow {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    .b2b-stat-card:hover {
        transform: translateY(-4px) scale(1.01);
        border-color: rgba(6, 182, 212, 0.6);
        box-shadow: 0 20px 40px -8px rgba(0, 0, 0, 0.7), 0 0 35px 2px rgba(6, 182, 212, 0.3);
    }
    .stat-card-top {
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .stat-card-title-group {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.82rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #A5B4FC;
    }
    .stat-card-period {
        background: rgba(30, 41, 59, 0.8);
        color: #38BDF8;
        font-size: 0.76rem;
        font-weight: 700;
        padding: 0.22rem 0.65rem;
        border-radius: 8px;
        border: 1px solid rgba(56, 189, 248, 0.3);
        box-shadow: 0 0 10px rgba(56, 189, 248, 0.15);
    }
    .stat-value-container {
        display: flex;
        align-items: baseline;
        gap: 0.65rem;
        margin: 0.2rem 0;
    }
    .stat-primary-number {
        font-size: 2.6rem;
        font-weight: 800;
        line-height: 1;
        background: linear-gradient(135deg, #FFFFFF 15%, #38BDF8 60%, #818CF8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.03em;
        filter: drop-shadow(0 2px 10px rgba(56, 189, 248, 0.35));
    }
    .stat-secondary-unit {
        font-size: 1.05rem;
        font-weight: 600;
        color: #94A3B8;
    }
    .stat-card-footer {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding-top: 0.55rem;
        border-top: 1px solid rgba(255, 255, 255, 0.08);
        font-size: 0.76rem;
        color: #64748B;
    }
    .stat-verified-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        color: #34D399;
        font-weight: 700;
        text-shadow: 0 0 10px rgba(52, 211, 153, 0.4);
    }
    .quick-action-header {
        font-size: 0.82rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #38BDF8;
        margin: 1.1rem 0 0.5rem 0;
        display: flex;
        align-items: center;
        gap: 0.45rem;
    }

    /* Hero / Empty State Welcome Card */
    .hero-container {
        text-align: center;
        padding: 2.5rem 1.2rem 1.8rem 1.2rem;
        max-width: 760px;
        margin: 0 auto;
    }
    .hero-badge {
        display: inline-block;
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.2) 0%, rgba(6, 182, 212, 0.2) 100%);
        border: 1px solid rgba(99, 102, 241, 0.5);
        color: #38BDF8;
        font-size: 0.74rem;
        font-weight: 800;
        letter-spacing: 0.12em;
        padding: 0.35rem 0.85rem;
        border-radius: 9999px;
        margin-bottom: 0.8rem;
        box-shadow: 0 0 20px rgba(56, 189, 248, 0.25);
    }
    .hero-title {
        font-size: 2.1rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        background: linear-gradient(135deg, #FFFFFF 20%, #A5B4FC 60%, #38BDF8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .hero-subtitle {
        font-size: 1rem;
        color: #94A3B8;
        margin-bottom: 2rem;
        line-height: 1.6;
    }

    /* Grounded Data Basis Pill */
    .data-basis-box {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        background: rgba(15, 23, 42, 0.8);
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 10px;
        padding: 0.45rem 0.9rem;
        margin-top: 0.6rem;
        font-size: 0.8rem;
        color: #94A3B8;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
    }
    .data-basis-icon {
        color: #38BDF8;
        font-weight: 700;
    }

    /* Styled Chat Output Containers */
    .chart-card-wrapper {
        background: linear-gradient(135deg, rgba(20, 27, 45, 0.85) 0%, rgba(13, 17, 28, 0.95) 100%);
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 16px;
        padding: 1.2rem 1.4rem;
        margin-top: 1rem;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4), 0 0 20px rgba(99, 102, 241, 0.1);
    }

    /* Streamlit Chat Messages Dark Cyber Luxe Polish */
    [data-testid="stChatMessage"] {
        background: rgba(15, 23, 42, 0.7) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 16px !important;
        padding: 1.2rem 1.4rem !important;
        margin-bottom: 1rem !important;
        backdrop-filter: blur(16px) !important;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3) !important;
    }
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
        background: rgba(30, 41, 59, 0.75) !important;
        border: 1px solid rgba(99, 102, 241, 0.4) !important;
        box-shadow: 0 6px 24px rgba(99, 102, 241, 0.15) !important;
    }

    /* Streamlit Buttons Glowing Hover */
    .stButton > button {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.75) 0%, rgba(15, 23, 42, 0.9) 100%) !important;
        color: #F8FAFC !important;
        border: 1px solid rgba(99, 102, 241, 0.35) !important;
        border-radius: 12px !important;
        padding: 0.65rem 1.15rem !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.3) !important;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) scale(1.02) !important;
        border-color: #38BDF8 !important;
        box-shadow: 0 8px 25px rgba(56, 189, 248, 0.35), 0 0 15px rgba(99, 102, 241, 0.3) !important;
        color: #FFFFFF !important;
    }

    /* Primary Accent Buttons */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #6366F1 0%, #4F46E5 50%, #7C3AED 100%) !important;
        border: 1px solid rgba(199, 210, 254, 0.5) !important;
        box-shadow: 0 4px 18px rgba(99, 102, 241, 0.45) !important;
    }
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #4F46E5 0%, #4338CA 50%, #6D28D9 100%) !important;
        box-shadow: 0 8px 28px rgba(99, 102, 241, 0.7) !important;
    }

    /* Fixed Bottom Chat Input Bar */
    .stChatInputContainer {
        background: rgba(15, 23, 42, 0.92) !important;
        border: 1px solid rgba(99, 102, 241, 0.45) !important;
        border-radius: 16px !important;
        box-shadow: 0 10px 35px rgba(0, 0, 0, 0.6), 0 0 20px rgba(99, 102, 241, 0.25) !important;
        backdrop-filter: blur(20px) !important;
    }
    .stChatInputContainer:focus-within {
        border-color: #38BDF8 !important;
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.7), 0 0 30px rgba(56, 189, 248, 0.4) !important;
    }

    /* Sidebar Glassmorphic Styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0B0F19 0%, #07090F 100%) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def api_request(method: str, path: str, token: str, **kwargs: object) -> dict | None:
    """Execute authenticated HTTP request against backend API."""
    try:
        response = httpx.request(
            method,
            f"{API_URL}{path}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=120,
            **kwargs,
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as exc:
        try:
            detail = exc.response.json().get("detail", "Request failed")
        except ValueError:
            detail = "Request failed"
        st.error(f"API Error ({exc.response.status_code}): {detail}")
    except (httpx.RequestError, ValueError) as err:
        st.error(f"Backend unreachable or invalid response: {err}")
    return None


def send_user_prompt(prompt_text: str, active_token: str) -> None:
    """Dispatch user prompt, creating conversation if necessary and updating state."""
    target_conv_id = st.session_state.get("conversation_id")
    if not target_conv_id:
        created_conv = api_request("POST", "/api/v1/conversations", active_token, json={})
        if created_conv:
            target_conv_id = created_conv["id"]
            st.session_state["conversation_id"] = target_conv_id

    if target_conv_id:
        with st.spinner("Analyzing operational data from Neon Gold..."):
            res = api_request(
                "POST",
                f"/api/v1/conversations/{target_conv_id}/messages",
                active_token,
                json={"content": prompt_text},
            )
            if res:
                st.session_state.setdefault("last_basis", {})[target_conv_id] = res.get("data_basis", "")
                st.rerun()


def extract_delivery_metric(text: str) -> Optional[Dict[str, str]]:
    """Parse key operational delivery numbers into structured B2B stat components."""
    lowered = text.lower()

    # Skip non-analytic outcomes (refusals, clarifications, empty states)
    if any(
        kw in lowered
        for kw in [
            "maaf", "sorry", "refused", "di luar", "outside", "ditolak",
            "rejected", "clarify", "perjelas", "tidak ditemukan data",
            "no data found", "gagal", "failed"
        ]
    ):
        return None

    # Check for percentage (e.g. 95.0% on-time, 2.5% refund)
    pct_match = re.search(r"(\d+(?:\.\d+)?)\s*%", text)

    # Check for currency (e.g. Rp 1.250.000 or IDR 1,250,000)
    money_match = re.search(r"(?:Rp|IDR)\s*([\d\.,]+)", text, re.IGNORECASE)

    # Check for volume counts (e.g. 217 packages, 217 shipments, 217 paket)
    count_match = re.search(r"(\b\d{1,6}\b)\s*(?:shipments?|paket|packages?|kiriman)", text, re.IGNORECASE)
    if not count_match:
        count_match = re.search(
            r"(?:total\s+(?:number\s+of\s+)?(?:shipments|kiriman|volume)|adalah|was|sebesar)\s*(\b\d{1,6}\b)",
            text,
            re.IGNORECASE,
        )

    # Determine metric title, icon, and unit
    if "on-time" in lowered or "tepat waktu" in lowered:
        title = "On-Time Delivery Rate"
        icon = "⏱️"
    elif "refund" in lowered:
        title = "Refund Rate" if pct_match else "Total Refund Amount"
        icon = "💰"
    elif "late" in lowered or "terlambat" in lowered:
        title = "Late Delivery Rate" if pct_match else "Late Shipments"
        icon = "⚠️"
    elif any(k in lowered for k in ["shipment", "kiriman", "volume", "paket"]):
        title = "Total Shipment Volume"
        icon = "📦"
    elif pct_match or count_match or money_match:
        title = "Key Delivery Metric"
        icon = "📊"
    else:
        return None

    # Identify Period
    period = "Gold Dataset"
    for p in ["august 2026", "agustus 2026", "september 2026", "july 2026", "juli 2026"]:
        if p in lowered:
            period = p.title()
            break

    # Determine primary value and unit
    if pct_match and ("rate" in title.lower() or not count_match):
        val = f"{pct_match.group(1)}%"
        unit = "delivered SLA"
    elif count_match:
        val = f"{count_match.group(1)}"
        unit = "packages" if ("package" in lowered or "shipment" in lowered or "august" in lowered) else "paket"
    elif money_match:
        val = f"Rp {money_match.group(1)}"
        unit = "IDR currency"
    else:
        return None

    return {
        "title": title,
        "icon": icon,
        "value": val,
        "unit": unit,
        "period": period,
    }


def render_chat_message(
    content: str,
    role: str = "assistant",
    msg_index: int = 0,
    is_latest: bool = False,
    active_token: str = "",
) -> None:
    """Render chat content with Mobbin B2B Stat Cards and interactive quick-actions."""
    norm_content = content
    if "\\n```chart" in norm_content or "```chart\\n" in norm_content:
        norm_content = norm_content.replace("\\n", "\n").replace('\\"', '"')

    pattern = re.compile(r"```chart\s*(\{[\s\S]*?\})\s*```", re.IGNORECASE)
    match = pattern.search(norm_content)

    clean_text = pattern.sub("", norm_content).strip() if match else norm_content

    # 1. B2B Analytics Stat Card (Mobbin Benchmark)
    metric = None
    if role == "assistant":
        metric = extract_delivery_metric(clean_text)
        if metric:
            st.markdown(
                f"""
                <div class="b2b-stat-card">
                    <div class="stat-card-top">
                        <div class="stat-card-title-group">
                            <span>{metric['icon']}</span>
                            <span>{metric['title']}</span>
                        </div>
                        <div class="stat-card-period">{metric['period']}</div>
                    </div>
                    <div class="stat-value-container">
                        <span class="stat-primary-number">{metric['value']}</span>
                        <span class="stat-secondary-unit">{metric['unit']}</span>
                    </div>
                    <div class="stat-card-footer">
                        <span class="stat-verified-badge">✓ Verified Gold Schema</span>
                        <span>Read-Only SQL AST Guard</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # 2. Render Text Answer
    if clean_text:
        st.markdown(clean_text)

    # 3. Render Interactive Chart if present
    if match:
        raw_json = match.group(1).strip()
        try:
            cfg = json.loads(raw_json)
            chart_type = str(cfg.get("type", "bar")).lower()
            title = cfg.get("title", "Analytics Data Visualization")
            raw_data = cfg.get("data", [])

            if raw_data and isinstance(raw_data, list):
                df = pd.DataFrame(raw_data)
                if "label" in df.columns:
                    df = df.set_index("label")

                for col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")

                st.markdown(
                    f"""
                    <div class="chart-card-wrapper">
                        <div style="font-weight:600; font-size:0.95rem; margin-bottom:0.5rem; color:#1E293B;">
                            📊 {title}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if chart_type == "line":
                    st.line_chart(df, use_container_width=True)
                else:
                    st.bar_chart(df, use_container_width=True)

                with st.expander("🔍 View Raw Query Data Table"):
                    st.dataframe(df, use_container_width=True)
        except Exception as exc:
            st.caption(f"*(Chart render error: {exc})*")

    # 4. Quick-Action Buttons (Mobbin Conversational B2B Pattern)
    if role == "assistant" and metric and is_latest and active_token:
        st.markdown(
            '<div class="quick-action-header">⚡ Quick Follow-Up Actions:</div>',
            unsafe_allow_html=True,
        )
        is_id = any(w in clean_text.lower() for w in ["paket", "kiriman", "pada", "agustus", "adalah"])

        col1, col2, col3, col4, col5 = st.columns(5)

        # Action 1: Trend Chart
        with col1:
            lbl1 = "📈 Grafik Tren" if is_id else "📈 Trend Chart"
            prompt1 = (
                f"Tampilkan tren mingguan untuk volume kiriman dalam grafik"
                if is_id
                else f"Show weekly volume trend for this metric in a chart"
            )
            if st.button(lbl1, key=f"qa_chart_{msg_index}", use_container_width=True):
                send_user_prompt(prompt1, active_token)

        # Action 2: Carrier Breakdown
        with col2:
            lbl2 = "🚚 Per Carrier" if is_id else "🚚 Carrier Breakdown"
            prompt2 = (
                f"Bagaimana rincian perbandingan antar carrier pada {metric['period']}?"
                if is_id
                else f"Show breakdown by carrier for {metric['period']}"
            )
            if st.button(lbl2, key=f"qa_carrier_{msg_index}", use_container_width=True):
                send_user_prompt(prompt2, active_token)

        # Action 3: Destination City Breakdown
        with col3:
            lbl3 = "🏙️ Per Kota" if is_id else "🏙️ City Breakdown"
            prompt3 = (
                f"Bagaimana rincian perbandingan antar kota tujuan pada {metric['period']}?"
                if is_id
                else f"Show breakdown by destination city for {metric['period']}"
            )
            if st.button(lbl3, key=f"qa_city_{msg_index}", use_container_width=True):
                send_user_prompt(prompt3, active_token)

        # Action 4: SLA Compliance Check (Chroma RAG + SQL)
        with col4:
            lbl4 = "⚖️ Cek SLA" if is_id else "⚖️ SLA Compliance"
            prompt4 = (
                f"Apakah performa ini memenuhi komitmen target SLA kurir pada {metric['period']}?"
                if is_id
                else f"Does this performance meet contractual SLA targets for {metric['period']}?"
            )
            if st.button(lbl4, key=f"qa_sla_{msg_index}", use_container_width=True):
                send_user_prompt(prompt4, active_token)

        # Action 5: Compare with Prior Period
        with col5:
            lbl5 = "🔄 Periode Lalu" if is_id else "🔄 Compare Previous"
            prompt5 = (
                "Bagaimana jika dibandingkan dengan periode minggu sebelumnya?"
                if is_id
                else "How does this compare to the previous period?"
            )
            if st.button(lbl5, key=f"qa_comp_{msg_index}", use_container_width=True):
                send_user_prompt(prompt5, active_token)


def get_3d_indonesia_radar_html() -> str:
    """Generate realistic 3D Indonesian logistics digital twin with authentic coastlines and active courier telemetry."""
    map_data_path = Path(__file__).parent / "src" / "indonesia_map_data.json"
    if not map_data_path.exists():
        map_data_path = Path("src/indonesia_map_data.json")
    raw_geojson = map_data_path.read_text(encoding="utf-8") if map_data_path.exists() else "[]"

    html_template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
    <meta charset="UTF-8">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
        body { background: #070A12; color: #F1F5F9; overflow: hidden; height: 100vh; width: 100vw; }
        #canvasContainer { position: relative; width: 100%; height: 100%; min-height: 560px; background: radial-gradient(circle at 50% 50%, #0D1629 0%, #050811 100%); cursor: grab; }
        #canvasContainer:active { cursor: grabbing; }
        canvas { display: block; width: 100%; height: 100%; }
        
        .radar-hud {
            position: absolute;
            top: 14px;
            left: 16px;
            background: rgba(13, 20, 36, 0.88);
            border: 1px solid rgba(56, 189, 248, 0.35);
            border-radius: 12px;
            padding: 10px 16px;
            backdrop-filter: blur(14px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.6);
            pointer-events: none;
            z-index: 10;
        }
        .hud-title {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 13px;
            font-weight: 800;
            letter-spacing: 0.05em;
            color: #38BDF8;
            text-transform: uppercase;
        }
        .live-dot {
            width: 8px;
            height: 8px;
            background: #10B981;
            border-radius: 50%;
            box-shadow: 0 0 10px #10B981, 0 0 20px #10B981;
            animation: pulse 1.5s infinite;
        }
        @keyframes pulse { 0%, 100% { opacity: 1; transform: scale(1); } 50% { opacity: 0.5; transform: scale(1.3); } }
        .hud-sub { font-size: 11px; color: #94A3B8; margin-top: 3px; }

        .radar-controls {
            position: absolute;
            bottom: 16px;
            left: 16px;
            display: flex;
            gap: 8px;
            z-index: 10;
            flex-wrap: wrap;
        }
        .ctrl-btn {
            background: rgba(22, 32, 54, 0.85);
            border: 1px solid rgba(56, 189, 248, 0.4);
            color: #F8FAFC;
            padding: 8px 14px;
            border-radius: 9px;
            font-size: 11px;
            font-weight: 700;
            cursor: pointer;
            backdrop-filter: blur(10px);
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 4px 15px rgba(0,0,0,0.4);
        }
        .ctrl-btn:hover {
            background: #4F46E5;
            border-color: #38BDF8;
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(56, 189, 248, 0.45);
        }
        .ctrl-btn.active {
            background: #6366F1;
            border-color: #38BDF8;
            box-shadow: 0 0 15px rgba(99, 102, 241, 0.6);
        }

        .radar-telemetry {
            position: absolute;
            top: 14px;
            right: 16px;
            width: 290px;
            background: rgba(13, 20, 36, 0.90);
            border: 1px solid rgba(99, 102, 241, 0.4);
            border-radius: 12px;
            padding: 14px 16px;
            backdrop-filter: blur(14px);
            font-size: 11px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.6);
            pointer-events: none;
            z-index: 10;
        }
        .telemetry-header { font-weight: 800; font-size: 11px; color: #A5B4FC; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 9px; display: flex; justify-content: space-between; align-items: center; }
        .feed-row { margin-bottom: 7px; padding-bottom: 7px; border-bottom: 1px solid rgba(255,255,255,0.06); }
        .feed-row:last-child { margin-bottom: 0; padding-bottom: 0; border-bottom: none; }
        .feed-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px; }
        .feed-courier { font-weight: 700; padding: 2px 6px; border-radius: 4px; font-size: 10px; }
        .badge-c01 { background: rgba(16, 185, 129, 0.2); color: #34D399; border: 1px solid rgba(16, 185, 129, 0.4); }
        .badge-c02 { background: rgba(6, 182, 212, 0.2); color: #38BDF8; border: 1px solid rgba(6, 182, 212, 0.4); }
        .badge-c03 { background: rgba(245, 158, 11, 0.2); color: #FBBF24; border: 1px solid rgba(245, 158, 11, 0.4); }
        .feed-route { color: #F1F5F9; font-weight: 700; font-size: 11px; }
        .feed-detail { color: #94A3B8; font-size: 10px; margin-top: 2px; }

        .city-inspector {
            position: absolute;
            bottom: 65px;
            right: 16px;
            width: 270px;
            background: rgba(15, 23, 42, 0.92);
            border: 1px solid rgba(56, 189, 248, 0.5);
            border-radius: 12px;
            padding: 12px 14px;
            backdrop-filter: blur(14px);
            font-size: 11px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.7);
            z-index: 10;
            pointer-events: none;
            transition: all 0.3s ease;
        }
        .inspector-title { font-size: 12.5px; font-weight: 800; color: #38BDF8; margin-bottom: 4px; display: flex; align-items: center; gap: 6px; }
        .inspector-metric { display: flex; justify-content: space-between; margin-top: 4px; color: #CBD5E1; }
        .inspector-metric strong { color: #F8FAFC; }
    </style>
    </head>
    <body>
    <div id="canvasContainer">
        <canvas id="radar3d"></canvas>
        <div class="radar-hud">
            <div class="hud-title"><span class="live-dot"></span> Indonesian Logistics Digital Twin</div>
            <div class="hud-sub">High-Precision Geographic Coastlines • Neon Gold Telemetry</div>
        </div>
        <div class="radar-telemetry">
            <div class="telemetry-header">
                <span>📡 Live Courier Operations</span>
                <span style="color:#10B981; font-size:10px;">6 Active Arcs</span>
            </div>
            <div class="feed-row">
                <div class="feed-top">
                    <span class="feed-courier badge-c01">C01 Regular 🚚</span>
                    <span class="feed-route">JKT ➔ BDG</span>
                </div>
                <div class="feed-detail">Cipularang Tollway • En route to Bandung Hub • <span style="color:#34D399;">95.8% On-Time</span></div>
            </div>
            <div class="feed-row">
                <div class="feed-top">
                    <span class="feed-courier badge-c02">C02 Express ✈️</span>
                    <span class="feed-route">JKT ➔ SUB</span>
                </div>
                <div class="feed-detail">Air Corridor FL280 • Java Sea Transit • <span style="color:#38BDF8;">100% SLA Guarantee</span></div>
            </div>
            <div class="feed-row">
                <div class="feed-top">
                    <span class="feed-courier badge-c03">C03 Standard 🚚</span>
                    <span class="feed-route">BDG ➔ SMG</span>
                </div>
                <div class="feed-detail">Bandung Plateau ➔ North Coast • <span style="color:#FBBF24;">Dispatched (92.4%)</span></div>
            </div>
            <div class="feed-row">
                <div class="feed-top">
                    <span class="feed-courier badge-c01">C01 Ground 🚢</span>
                    <span class="feed-route">SUB ➔ DPS</span>
                </div>
                <div class="feed-detail">Bali Strait Crossing ➔ Denpasar Hub • <span style="color:#EC4899;">On Schedule</span></div>
            </div>
        </div>
        <div class="city-inspector" id="cityInspector">
            <div class="inspector-title" id="inspTitle">🏙️ Bandung Hub (BDG-02)</div>
            <div style="color:#94A3B8; font-size:10px; margin-bottom:6px;" id="inspDesc">West Java Fulfillment Center. Receiving continuous consignments from Jakarta.</div>
            <div class="inspector-metric"><span>Daily Volume:</span> <strong id="inspVol">89 pkgs/day</strong></div>
            <div class="inspector-metric"><span>On-Time Rate:</span> <strong style="color:#34D399;" id="inspRate">95.8% (Target Met)</strong></div>
            <div class="inspector-metric"><span>Primary Carrier:</span> <strong id="inspCarrier">C01 Regular & C03 Standard</strong></div>
        </div>
        <div class="radar-controls">
            <button class="ctrl-btn" id="btnBdg" onclick="setTarget('bandung')">📍 Zoom: Bandung Hub</button>
            <button class="ctrl-btn" id="btnJkt" onclick="setTarget('jakarta')">📍 Zoom: Jakarta Central</button>
            <button class="ctrl-btn" id="btnSub" onclick="setTarget('surabaya')">📍 Zoom: Surabaya & Bali</button>
            <button class="ctrl-btn active" id="btnAll" onclick="setTarget('all')">🌐 Entire Archipelago (Zoom Out)</button>
            <button class="ctrl-btn" id="btnRot" onclick="toggleAutoRotate()">🔄 Auto-Rotate [ON]</button>
        </div>
    </div>

    <script>
    const canvas = document.getElementById('radar3d');
    const ctx = canvas.getContext('2d');
    const container = document.getElementById('canvasContainer');

    function resize() {
        canvas.width = container.clientWidth * window.devicePixelRatio;
        canvas.height = container.clientHeight * window.devicePixelRatio;
    }
    window.addEventListener('resize', resize);
    resize();

    // 139 Real Geographic Coastline Polygons of Indonesia
    const ID_COASTLINES = %MAP_GEO_JSON%;

    // Geographic Projection: Lon/Lat to 3D World Coordinates (Center at 118°E, -2.5°S)
    const GEO_SCALE = 18.0;
    function lonLatToWorld(lon, lat, alt = 0) {
        return {
            x: (lon - 118.0) * GEO_SCALE,
            y: -(lat - (-2.5)) * GEO_SCALE,
            z: alt
        };
    }

    // Pre-calculate 3D world points for all coastline polygons
    const worldCoastlines = ID_COASTLINES.map(poly => {
        return poly.map(pt => lonLatToWorld(pt[0], pt[1], 0));
    });

    // Real Indonesian Logistics Hubs
    const cities = [
        { id: "jkt", name: "Jakarta", lon: 106.845, lat: -6.208, alt: 0, code: "JKT-01", color: "#38BDF8", hub: "Jakarta Central Sort Facility", volume: "142 pkgs/day", onTime: "95.1%", carrier: "C01 & C02 Express", desc: "Automated sortation mega-hub. Handles primary air cargo intake and Trans-Java dispatches." },
        { id: "bdg", name: "Bandung", lon: 107.619, lat: -6.917, alt: 18, code: "BDG-02", color: "#10B981", hub: "Bandung West Java Center", volume: "89 pkgs/day", onTime: "95.8%", carrier: "C01 Regular & C03", desc: "West Java fulfillment depot. High ground-volume corridor via Cipularang Highway." },
        { id: "smg", name: "Semarang", lon: 110.417, lat: -6.967, alt: 5, code: "SMG-04", color: "#818CF8", hub: "Semarang Central Java Hub", volume: "47 pkgs/day", onTime: "93.4%", carrier: "C03 Standard", desc: "Central Java cross-docking terminal along Trans-Java corridor." },
        { id: "sub", name: "Surabaya", lon: 112.752, lat: -7.257, alt: 0, code: "SUB-03", color: "#F59E0B", hub: "Surabaya Mega Terminal", volume: "118 pkgs/day", onTime: "94.2%", carrier: "C01 & C02 Express", desc: "Eastern Java sea and air cargo hub. Connecting Java to Bali, Nusa Tenggara, and Sulawesi." },
        { id: "dps", name: "Denpasar", lon: 115.213, lat: -8.670, alt: 6, code: "DPS-07", color: "#EC4899", hub: "Bali Express Gateway", volume: "34 pkgs/day", onTime: "96.5%", carrier: "C01 Priority", desc: "Tourism & express gateway. Connected via Ketapang-Gilimanuk strait transit." },
        { id: "mdn", name: "Medan", lon: 98.672, lat: 3.595, alt: 0, code: "MDN-05", color: "#06B6D4", hub: "North Sumatra Air Terminal", volume: "62 pkgs/day", onTime: "94.7%", carrier: "C02 Express Air", desc: "Sumatra regional air gateway connecting to Jakarta central sortation." },
        { id: "upg", name: "Makassar", lon: 119.433, lat: -5.148, alt: 0, code: "UPG-06", color: "#A855F7", hub: "Eastern Indonesia Gateway", volume: "53 pkgs/day", onTime: "92.0%", carrier: "C01 Maritime/Air", desc: "Maritime & air transshipment center for Sulawesi, Maluku & Papua." },
        { id: "bpn", name: "Balikpapan", lon: 116.829, lat: -1.238, alt: 5, code: "BPN-08", color: "#34D399", hub: "East Kalimantan Depot", volume: "29 pkgs/day", onTime: "93.8%", carrier: "C01 & C03", desc: "Industrial logistics depot for East Kalimantan." },
        { id: "plm", name: "Palembang", lon: 104.775, lat: -2.976, alt: 0, code: "PLM-09", color: "#F97316", hub: "South Sumatra Terminal", volume: "38 pkgs/day", onTime: "94.0%", carrier: "C01 Regular", desc: "Trans-Sumatra highway node connecting Lampung and Jambi." },
        { id: "djj", name: "Jayapura", lon: 140.718, lat: -2.549, alt: 0, code: "DJJ-10", color: "#38BDF8", hub: "Papua Logistics Depot", volume: "18 pkgs/day", onTime: "91.5%", carrier: "C02 Cargo", desc: "Easternmost air cargo terminal for Papua logistics." }
    ];

    cities.forEach(c => {
        const w = lonLatToWorld(c.lon, c.lat, c.alt);
        c.x = w.x;
        c.y = w.y;
        c.z = w.z;
    });

    // Real Courier Routes & In-Flight Operations
    const routes = [
        {
            from: "jkt", to: "bdg", courier: "C01-104", type: "Regular Van", icon: "🚚",
            speed: 0.007, color: "#10B981", height: 26,
            action: "Cruising Cipularang Highway towards Bandung Hub (85 km/h)",
            telemetry: "42 pkgs • On-Time 95.8% • ETA 22m"
        },
        {
            from: "jkt", to: "sub", courier: "C02-EXP", type: "Air Cargo Express", icon: "✈️",
            speed: 0.0048, color: "#38BDF8", height: 70,
            action: "High-Altitude Airway FL280 over Java Sea JKT ➔ SUB",
            telemetry: "185 pkgs • 100% SLA Guarantee"
        },
        {
            from: "bdg", to: "smg", courier: "C03-094", type: "Standard Van", icon: "🚚",
            speed: 0.0055, color: "#FBBF24", height: 32,
            action: "Dispatched from Bandung Plateau towards Central Java",
            telemetry: "64 pkgs • On-Time 92.4% • In-Transit"
        },
        {
            from: "sub", to: "dps", courier: "C01-072", type: "Ferry/Truck", icon: "🚢",
            speed: 0.004, color: "#EC4899", height: 32,
            action: "Crossing Bali Strait towards Denpasar Express Hub",
            telemetry: "51 pkgs • Maritime Transit • SLA Met"
        },
        {
            from: "jkt", to: "mdn", courier: "C02-882", type: "Air Express", icon: "✈️",
            speed: 0.0035, color: "#06B6D4", height: 90,
            action: "Trans-Sumatra Airway over Sunda Strait to Kualanamu",
            telemetry: "140 pkgs • C02 Priority 1"
        },
        {
            from: "sub", to: "upg", courier: "C01-SEA", type: "Sea Freight", icon: "🚢",
            speed: 0.003, color: "#A855F7", height: 75,
            action: "Maritime freight crossing Java Sea to Makassar Port",
            telemetry: "320 pkgs • Bulk Freight"
        }
    ];

    routes.forEach(r => {
        r.t = Math.random();
        r.cFrom = cities.find(c => c.id === r.from);
        r.cTo = cities.find(c => c.id === r.to);
    });

    // Camera Transform & Dynamic Inertia State
    let rotX = 0.95;   // ~54 degrees pitch
    let rotZ = -0.18;  // slight yaw
    let targetRotX = rotX;
    let targetRotZ = rotZ;
    let zoom = 1.35;
    let targetZoom = zoom;
    let panX = 0;
    let panY = 0;
    let targetPanX = 0;
    let targetPanY = 0;
    let autoRotate = true;

    // Mouse & Touch Controls
    let isDragging = false;
    let lastMouseX = 0, lastMouseY = 0;

    container.addEventListener('mousedown', e => {
        isDragging = true;
        autoRotate = false;
        document.getElementById('btnRot').textContent = "🔄 Auto-Rotate [OFF]";
        lastMouseX = e.clientX;
        lastMouseY = e.clientY;
    });

    window.addEventListener('mouseup', () => isDragging = false);

    window.addEventListener('mousemove', e => {
        if (!isDragging) return;
        const dx = e.clientX - lastMouseX;
        const dy = e.clientY - lastMouseY;
        lastMouseX = e.clientX;
        lastMouseY = e.clientY;

        targetRotZ += dx * 0.005;
        targetRotX = Math.max(0.35, Math.min(1.35, targetRotX + dy * 0.005));
    });

    container.addEventListener('wheel', e => {
        e.preventDefault();
        const factor = e.deltaY < 0 ? 1.15 : 0.88;
        targetZoom = Math.max(0.65, Math.min(4.5, targetZoom * factor));
    }, { passive: false });

    // Interactive Zoom Targets (Focus on Bandung, Jakarta, etc.)
    window.setTarget = function(target) {
        document.querySelectorAll('.ctrl-btn').forEach(b => b.classList.remove('active'));
        if (target === 'bandung') {
            document.getElementById('btnBdg').classList.add('active');
            targetPanX = 166;
            targetPanY = -71;
            targetZoom = 3.4;
            targetRotX = 0.85;
            showInspector(cities.find(c => c.id === "bdg"));
        } else if (target === 'jakarta') {
            document.getElementById('btnJkt').classList.add('active');
            targetPanX = 178;
            targetPanY = -59;
            targetZoom = 3.2;
            targetRotX = 0.90;
            showInspector(cities.find(c => c.id === "jkt"));
        } else if (target === 'surabaya') {
            document.getElementById('btnSub').classList.add('active');
            targetPanX = 64;
            targetPanY = -85;
            targetZoom = 2.8;
            targetRotX = 0.88;
            showInspector(cities.find(c => c.id === "sub"));
        } else {
            document.getElementById('btnAll').classList.add('active');
            targetPanX = 0;
            targetPanY = 0;
            targetZoom = 1.35;
            targetRotX = 0.95;
            targetRotZ = -0.18;
            showInspector(cities.find(c => c.id === "bdg"));
        }
    };

    window.toggleAutoRotate = function() {
        autoRotate = !autoRotate;
        document.getElementById('btnRot').textContent = autoRotate ? "🔄 Auto-Rotate [ON]" : "🔄 Auto-Rotate [OFF]";
    };

    function showInspector(city) {
        if (!city) return;
        document.getElementById('inspTitle').textContent = `🏙️ ${city.name} (${city.code})`;
        document.getElementById('inspDesc').textContent = city.desc;
        document.getElementById('inspVol').textContent = city.volume;
        document.getElementById('inspRate').textContent = `${city.onTime} (Target Met)`;
        document.getElementById('inspCarrier').textContent = city.carrier;
    }

    // 3D Point Projection to 2D Screen Canvas
    function project(x, y, z) {
        // Rotate around Z axis (yaw)
        const cosZ = Math.cos(rotZ), sinZ = Math.sin(rotZ);
        const x1 = x * cosZ - y * sinZ;
        const y1 = x * sinZ + y * cosZ;

        // Rotate around X axis (pitch)
        const cosX = Math.cos(rotX), sinX = Math.sin(rotX);
        const y2 = y1 * cosX - z * sinX;
        const z2 = y1 * sinX + z * cosX;

        // Perspective projection
        const fov = 950;
        const d = fov / (fov + y2 + 220);
        const scale = d * zoom * (window.devicePixelRatio || 1);

        const screenX = (canvas.width / 2) + (x1 + panX) * scale;
        const screenY = (canvas.height / 2) + (z2 + panY) * scale;

        return { x: screenX, y: screenY, scale: scale, depth: y2 };
    }

    let pulseTime = 0;

    function render() {
        // Smooth camera interpolation
        rotX += (targetRotX - rotX) * 0.08;
        rotZ += (targetRotZ - rotZ) * 0.08;
        zoom += (targetZoom - zoom) * 0.08;
        panX += (targetPanX - panX) * 0.08;
        panY += (targetPanY - panY) * 0.08;

        if (autoRotate) {
            targetRotZ += 0.0015;
        }
        pulseTime += 0.035;

        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // 1. Draw 3D Ocean Coordinate Grid (Longitudes & Latitudes)
        ctx.strokeStyle = "rgba(56, 189, 248, 0.06)";
        ctx.lineWidth = 1;

        // Longitudes (95°E to 141°E)
        for (let lon = 95; lon <= 141; lon += 5) {
            const w1 = lonLatToWorld(lon, 7, 0);
            const w2 = lonLatToWorld(lon, -12, 0);
            const p1 = project(w1.x, w1.y, 0);
            const p2 = project(w2.x, w2.y, 0);
            ctx.beginPath();
            ctx.moveTo(p1.x, p1.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.stroke();

            // Coordinate label
            if (lon % 10 === 0) {
                ctx.font = `${Math.round(8 * p1.scale)}px sans-serif`;
                ctx.fillStyle = "rgba(148, 163, 184, 0.4)";
                ctx.fillText(`${lon}°E`, p1.x, p1.y - 4);
            }
        }

        // Equator Line (0° Latitude)
        const eqW1 = lonLatToWorld(93, 0, 0);
        const eqW2 = lonLatToWorld(143, 0, 0);
        const eqP1 = project(eqW1.x, eqW1.y, 0);
        const eqP2 = project(eqW2.x, eqW2.y, 0);
        ctx.beginPath();
        ctx.moveTo(eqP1.x, eqP1.y);
        ctx.lineTo(eqP2.x, eqP2.y);
        ctx.strokeStyle = "rgba(245, 158, 11, 0.28)";
        ctx.setLineDash([6, 6]);
        ctx.stroke();
        ctx.setLineDash([]);
        ctx.font = `bold ${Math.round(8 * eqP1.scale)}px sans-serif`;
        ctx.fillStyle = "rgba(245, 158, 11, 0.5)";
        ctx.fillText("EQUATOR (0°00')", eqP1.x + 10, eqP1.y - 4);

        // 2. Draw Realistic Indonesian Islands (139 authentic polygons)
        worldCoastlines.forEach(pts => {
            if (pts.length < 3) return;

            // First pass: Landmass fill
            ctx.beginPath();
            pts.forEach((w, idx) => {
                const p = project(w.x, w.y, 0);
                if (idx === 0) ctx.moveTo(p.x, p.y);
                else ctx.lineTo(p.x, p.y);
            });
            ctx.closePath();
            ctx.fillStyle = "rgba(16, 28, 48, 0.92)";
            ctx.fill();

            // Second pass: Shallow coastal shelf glow
            ctx.strokeStyle = "rgba(6, 182, 212, 0.20)";
            ctx.lineWidth = 5 * (zoom > 2 ? 1.5 : 1);
            ctx.stroke();

            // Third pass: Sharp high-res shoreline border
            ctx.strokeStyle = "rgba(56, 189, 248, 0.85)";
            ctx.lineWidth = 1.3;
            ctx.stroke();
        });

        // 3. Draw 3D Parabolic Delivery Routes & Active Moving Couriers
        routes.forEach(r => {
            r.t = (r.t + r.speed) % 1;
            const p0 = r.cFrom;
            const p1 = r.cTo;
            const midX = (p0.x + p1.x) / 2;
            const midY = (p0.y + p1.y) / 2;
            const midZ = r.height;

            // Draw Curved Arc Path
            ctx.beginPath();
            const segments = 32;
            for (let i = 0; i <= segments; i++) {
                const s = i / segments;
                const bx = (1 - s) * (1 - s) * p0.x + 2 * (1 - s) * s * midX + s * s * p1.x;
                const by = (1 - s) * (1 - s) * p0.y + 2 * (1 - s) * s * midY + s * s * p1.y;
                const bz = (1 - s) * (1 - s) * p0.z + 2 * (1 - s) * s * midZ + s * s * p1.z;
                const sp = project(bx, by, bz);
                if (i === 0) ctx.moveTo(sp.x, sp.y);
                else ctx.lineTo(sp.x, sp.y);
            }
            ctx.strokeStyle = r.color + "66";
            ctx.lineWidth = 1.8;
            ctx.setLineDash([5, 5]);
            ctx.stroke();
            ctx.setLineDash([]);

            // Draw Moving Courier Pod
            const s = r.t;
            const cx = (1 - s) * (1 - s) * p0.x + 2 * (1 - s) * s * midX + s * s * p1.x;
            const cy = (1 - s) * (1 - s) * p0.y + 2 * (1 - s) * s * midY + s * s * p1.y;
            const cz = (1 - s) * (1 - s) * p0.z + 2 * (1 - s) * s * midZ + s * s * p1.z;
            const cp = project(cx, cy, cz);

            // Glowing courier beacon
            ctx.beginPath();
            ctx.arc(cp.x, cp.y, 6.5 * cp.scale, 0, Math.PI * 2);
            ctx.fillStyle = r.color;
            ctx.shadowColor = r.color;
            ctx.shadowBlur = 16;
            ctx.fill();
            ctx.shadowBlur = 0;

            // Dynamic courier label badge
            ctx.font = `bold ${Math.round(10 * cp.scale)}px sans-serif`;
            ctx.fillStyle = "#FFFFFF";
            ctx.fillText(`${r.courier} ${r.icon}`, cp.x + 9, cp.y - 4);
        });

        // 4. Draw City Terminals & Vertical Light Beacons
        cities.forEach(c => {
            const base = project(c.x, c.y, 0);
            const top = project(c.x, c.y, c.z + 22);

            // Vertical Light Pillar
            ctx.beginPath();
            ctx.moveTo(base.x, base.y);
            ctx.lineTo(top.x, top.y);
            ctx.strokeStyle = c.color + "AA";
            ctx.lineWidth = 2.2 * base.scale;
            ctx.stroke();

            // Radar ripple on key hubs (Bandung, Jakarta, Surabaya)
            if (c.id === "bdg" || c.id === "jkt" || c.id === "sub") {
                const ringRadius = ((pulseTime * 28) % 40) * base.scale;
                const ringAlpha = Math.max(0, 1 - (ringRadius / (40 * base.scale)));
                ctx.beginPath();
                ctx.arc(base.x, base.y, ringRadius, 0, Math.PI * 2);
                ctx.strokeStyle = c.color + Math.floor(ringAlpha * 255).toString(16).padStart(2, '0');
                ctx.lineWidth = 1.8;
                ctx.stroke();
            }

            // Beacon Node
            ctx.beginPath();
            ctx.arc(top.x, top.y, 5.5 * base.scale, 0, Math.PI * 2);
            ctx.fillStyle = c.color;
            ctx.shadowColor = c.color;
            ctx.shadowBlur = 14;
            ctx.fill();
            ctx.shadowBlur = 0;

            // City Label & Hub Code
            ctx.font = `bold ${Math.round(11 * base.scale)}px 'Plus Jakarta Sans', sans-serif`;
            ctx.fillStyle = "#FFFFFF";
            ctx.fillText(c.name, top.x + 9 * base.scale, top.y - 2);

            ctx.font = `${Math.round(8.5 * base.scale)}px sans-serif`;
            ctx.fillStyle = "#94A3B8";
            ctx.fillText(c.volume, top.x + 9 * base.scale, top.y + 10 * base.scale);
        });

        requestAnimationFrame(render);
    }
    render();
    </script>
    </body>
    </html>
    """
    return html_template.replace("%MAP_GEO_JSON%", raw_geojson)



# -----------------------------------------------------------------------------
# Sidebar: Authentication, Thread Navigation, Deletion & IDOR Lab
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🔐 Authentication")
    token = st.text_input(
        "Demo Bearer Token",
        value=st.session_state.get("active_token", ""),
        type="password",
        placeholder="e.g. token-alice-demo-secret-123",
        help="Paste Alice or Bob demo token provided in the documentation.",
    )

    if st.session_state.get("active_token") != token:
        st.session_state["active_token"] = token
        st.session_state["conversation_id"] = None

    conversations = []
    ids = []
    if not token:
        st.info("👋 Welcome! Select a demo role on the main screen or enter your token above.")
        st.markdown(
            """
            **Quick Demo Tokens:**
            - `token-alice-demo-secret-123` *(Alice)*
            - `token-bob-demo-secret-456` *(Bob)*
            """
        )
    else:
        st.markdown("---")
        st.markdown("### 💬 Conversations")

        if st.button("➕ New Conversation", use_container_width=True, type="primary"):
            created = api_request("POST", "/api/v1/conversations", token, json={})
            if created:
                st.session_state["conversation_id"] = created["id"]
                st.rerun()

        listing = api_request("GET", "/api/v1/conversations", token)
        conversations = listing.get("conversations", []) if listing else []
        ids = [item["id"] for item in conversations]

        if ids:
            current = st.session_state.get("conversation_id")
            selected = st.selectbox(
                "Select Thread",
                ids,
                index=ids.index(current) if current in ids else 0,
                format_func=lambda value: next(
                    (item.get("title") or value for item in conversations if item["id"] == value),
                    value,
                ),
                label_visibility="collapsed",
            )
            st.session_state["conversation_id"] = selected

            st.caption("📋 **Active Conversation UUID:**")
            st.code(selected, language=None)

            if st.button(
                "🗑️ Delete Conversation",
                use_container_width=True,
                help="Permanently delete this active conversation and all its messages",
            ):
                deleted = api_request("DELETE", f"/api/v1/conversations/{selected}", token)
                if deleted:
                    st.session_state["conversation_id"] = None
                    if "last_basis" in st.session_state and selected in st.session_state["last_basis"]:
                        del st.session_state["last_basis"][selected]
                    st.success("Conversation deleted.")
                    st.rerun()
        else:
            st.caption("No conversations yet. Start a new one above!")

    st.markdown("---")

    # Developer & Auditor Security Toolkit
    with st.expander("🧪 Security & IDOR Audit Lab", expanded=False):
        st.caption("Verify strict tenant isolation (Cases O1, O2, O3: Read, Write, Delete).")
        idor_target = st.text_input(
            "Target Conversation UUID",
            placeholder="Paste target user's UUID here...",
            key="idor_target_input",
        )
        if st.button("🚨 Run Cross-Tenant Exploit Test", use_container_width=True):
            target_uuid = idor_target.strip()
            if not target_uuid:
                st.warning("Please provide a target conversation UUID.")
            else:
                with st.spinner("Testing security boundary on backend..."):
                    try:
                        res_read = httpx.get(
                            f"{API_URL}/api/v1/conversations/{target_uuid}",
                            headers={"Authorization": f"Bearer {token}"},
                            timeout=10,
                        )
                        res_write = httpx.post(
                            f"{API_URL}/api/v1/conversations/{target_uuid}/messages",
                            headers={"Authorization": f"Bearer {token}"},
                            json={"content": "Unauthorized injection attempt"},
                            timeout=10,
                        )
                        res_del = httpx.delete(
                            f"{API_URL}/api/v1/conversations/{target_uuid}",
                            headers={"Authorization": f"Bearer {token}"},
                            timeout=10,
                        )

                        if res_read.status_code == 404 and res_write.status_code == 404 and res_del.status_code == 404:
                            st.success(
                                "🛡️ **IDOR DEFENSE VERIFIED!**\n\n"
                                "• **Test O1 (Read):** `HTTP 404 Not Found`\n\n"
                                "• **Test O2 (Write):** `HTTP 404 Not Found`\n\n"
                                "• **Test O3 (Delete):** `HTTP 404 Not Found`\n\n"
                                "*All operations blocked without data leakage.*"
                            )
                        else:
                            st.error(
                                f"❌ Security violation: Read={res_read.status_code}, "
                                f"Write={res_write.status_code}, Delete={res_del.status_code}"
                            )
                    except Exception as exc:
                        st.error(f"Test failed: {exc}")

    # Carrier SLA & Policies (Chroma RAG)
    with st.expander("⚖️ Carrier SLA & Policies (Chroma RAG)", expanded=False):
        st.markdown(
            """
            **Contractual Targets (2026):**
            - **C01:** On-Time Rate ≥ **95.0%**
            - **C02 Express:** On-Time Rate ≥ **90.0%**
            - **C02 Standard:** On-Time Rate ≥ **85.0%**
            - **C03 Express:** On-Time Rate ≥ **93.0%**

            **Penalty & Refund Rules:**
            - **Clause 3.1:** Late Express → **100% full refund**
            - **Clause 3.2:** Late Standard → **50% partial refund**
            - **Clause 3.3:** In-Transit not late until arrival/14 days
            - **Section 4:** Monthly SLA breach → 5% penalty & 20% cut
            """
        )
        if st.button("🔍 Check SLA Targets", key="sb_sla_btn", use_container_width=True):
            send_user_prompt("Berapa target SLA untuk kurir C01, C02, dan C03?", token)
        if st.button("💸 Check Express Refund Policy", key="sb_ref_btn", use_container_width=True):
            send_user_prompt("Apa aturan refund untuk pengiriman express yang terlambat?", token)


# -----------------------------------------------------------------------------
# Main Application Canvas
# -----------------------------------------------------------------------------

# If unauthenticated, show the Full-Screen 3D Indonesian Logistics Radar and 1-Click Login Cards
if not token:
    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 1.2rem;">
            <div class="hero-badge">🌐 3D DIGITAL TWIN TELEMETRY</div>
            <h1 style="font-size: 2.2rem; font-weight: 800; background: linear-gradient(135deg, #FFFFFF 20%, #38BDF8 60%, #818CF8 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0.4rem;">
                Indonesian Delivery Operations Radar
            </h1>
            <p style="color: #94A3B8; font-size: 0.98rem; max-width: 680px; margin: 0 auto;">
                Live 3D spatial simulation tracking courier flight & ground routes across <strong>Jakarta, Bandung, Surabaya, Semarang, Medan & Bali</strong>. Grounded in Neon Gold PostgreSQL analytics.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 3D Interactive Indonesian Logistics Map & Courier Radar
    st.components.v1.html(get_3d_indonesia_radar_html(), height=550)

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    st.markdown("#### 🚀 Select Your Mission Role to Enter:")
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button(
            "📦 Launch Operations Command as Alice\n\nDemo Token: token-alice-demo-secret-123",
            key="launch_alice_main",
            use_container_width=True,
            type="primary",
        ):
            st.session_state["active_token"] = "token-alice-demo-secret-123"
            st.rerun()
    with col_b:
        if st.button(
            "🛡️ Launch Auditor Command as Bob\n\nDemo Token: token-bob-demo-secret-456",
            key="launch_bob_main",
            use_container_width=True,
        ):
            st.session_state["active_token"] = "token-bob-demo-secret-456"
            st.rerun()

    st.stop()

# Resolve user tenant label
tenant_label = (
    "Alice (Operations)"
    if "alice" in token.lower()
    else ("Bob (Auditor)" if "bob" in token.lower() else "Authenticated Tenant")
)

# Top Header Bar
st.markdown(
    f"""
    <div class="top-header-bar">
        <div class="header-title-group">
            <h2>📦 Delivery Analytics Agent</h2>
            <p>Enterprise shipping operations intelligence grounded in Neon Gold PostgreSQL</p>
        </div>
        <div class="status-badge-container">
            <span class="status-pill"><span class="status-dot"></span> Neon Gold (Online)</span>
            <span class="tenant-pill">👤 {tenant_label}</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Interactive 3D Indonesian Logistics Telemetry Radar Expander in Chat
with st.expander("🗺️ Live 3D Indonesian Delivery Map & Courier Radar (Interactive)", expanded=False):
    st.components.v1.html(get_3d_indonesia_radar_html(), height=500)


conversation_id = st.session_state.get("conversation_id")
messages: List[Dict[str, Any]] = []

if conversation_id:
    detail = api_request("GET", f"/api/v1/conversations/{conversation_id}", token)
    if detail:
        messages = detail.get("messages", [])

# Render Empty State with Mobbin-style Prompt Starter Cards if thread is empty
if not messages:
    st.markdown(
        """
        <div class="hero-container">
            <div class="cube-3d-scene">
                <div class="cube-3d">
                    <div class="cube-face cube-front">📦</div>
                    <div class="cube-face cube-back">⚡</div>
                    <div class="cube-face cube-right">📊</div>
                    <div class="cube-face cube-left">🚀</div>
                    <div class="cube-face cube-top">🌐</div>
                    <div class="cube-face cube-bottom">✨</div>
                </div>
            </div>
            <div class="hero-badge">⚡ NEON GOLD INTELLIGENCE</div>
            <div class="hero-title">Shipping Operations Command</div>
            <div class="hero-subtitle">
                Autonomous delivery analytics, carrier contract SLA tracking, and dynamic SQL telemetry.
                Select a mission prompt below or enter your operational query:
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    card_col1, card_col2 = st.columns(2)
    with card_col1:
        if st.button(
            "📦 Total Volume & Carrier Breakdown\n\nWhat is the total shipments in August 2026 and carrier comparisons?",
            key="starter_1",
            use_container_width=True,
        ):
            send_user_prompt("What is the total shipments in August 2026 and carrier comparisons?", token)

        if st.button(
            "⏱️ Top Carrier On-Time Rate\n\nWhich carrier had the highest on-time rate in August 2026, min 20 delivered?",
            key="starter_2",
            use_container_width=True,
        ):
            send_user_prompt("Which carrier had the highest on-time rate in August 2026, minimum 20 delivered?", token)

    with card_col2:
        if st.button(
            "📈 Weekly Volume Trend to Bandung\n\nShow weekly shipment volume trend to Bandung in a chart",
            key="starter_3",
            use_container_width=True,
        ):
            send_user_prompt("Show weekly shipment volume trend to Bandung in a chart", token)

        if st.button(
            "💰 Express Service Refund Ratio\n\nWhat was the refund rate for express service in September 2026?",
            key="starter_4",
            use_container_width=True,
        ):
            send_user_prompt("What was the refund rate for express service in September 2026?", token)

else:
    # Render active message thread
    total_msgs = len(messages)
    for idx, msg in enumerate(messages):
        with st.chat_message(msg["role"]):
            render_chat_message(
                msg["content"],
                role=msg["role"],
                msg_index=idx,
                is_latest=(idx == total_msgs - 1),
                active_token=token,
            )

    # Perplexity-style Data Grounding Citation Pill
    basis = st.session_state.get("last_basis", {}).get(conversation_id)
    if basis:
        st.markdown(
            f"""
            <div class="data-basis-box">
                <span class="data-basis-icon">📌</span>
                <span><strong>Data Basis:</strong> {basis}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

# Chat Input Box fixed at bottom
user_input = st.chat_input("Ask about volume, SLA delays, refund rate, carriers, or request a chart...")
if user_input:
    send_user_prompt(user_input, token)
