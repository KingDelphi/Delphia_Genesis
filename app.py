"""
╔══════════════════════════════════════════════════════════════════╗
║           DELPHIA GENESIS v0.7 — THE SOVEREIGN ASCENSION         ║
║       Where Imagination Becomes Sovereign on the Genesis Layer    ║
║                     Rey Delphi · Kardashev VI                    ║
╚══════════════════════════════════════════════════════════════════╝

CHANGELOG v0.7:
  - Vault 100% dinámico: imágenes reales, PDFs, emojis
  - Upload robusto con reflejo inmediato en Vault
  - TITLE funciona con cualquier creación real
  - SPLIT actualiza campo is_fractional en CSV
  - Parental / Sponsor Mode (mock) en sidebar
  - Quest Engine inteligente: auto-detecta estado al login
  - IMAGIX Wallet en tiempo real
  - Showcase mejorado con animaciones CSS
  - Genesis Terminal enriquecido
  - Mejoras responsive
  - Código modular y comentado
"""

import streamlit as st
import pandas as pd
import os
import hashlib
import io
import math
import base64
from datetime import datetime, date
from pathlib import Path

# ─── ReportLab — PDF certificates ────────────────────────────
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.colors import HexColor

# ─── Pillow — thumbnail generation ───────────────────────────
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


# ══════════════════════════════════════════════════════════════
# ① CONSTANTS & DESIGN TOKENS
# ══════════════════════════════════════════════════════════════
C = {
    "space":    "#05121f",
    "celestial":"#0A2540",
    "card":     "#0e2240",
    "card2":    "#112B4D",
    "gold":     "#F2C94C",
    "gold_dim": "#c8a000",
    "teal":     "#00E5C0",
    "purple":   "#9D4EDD",
    "purple2":  "#6b2fa0",
    "white":    "#FFFFFF",
    "muted":    "#8899aa",
    "danger":   "#FF6B6B",
    "success":  "#2ECC71",
}

DATA_FILE      = "genesis_creations.csv"
QUESTS_FILE    = "genesis_quests.csv"
WALLET_FILE    = "genesis_wallets.csv"
CREATIONS_DIR  = "creations"
THUMB_SIZE     = (320, 220)

RANK_TIERS = [
    (0,        "✦ SPARK I",    "spark"),
    (10_000,   "✦ SPARK II",   "spark"),
    (25_000,   "✦ SPARK III",  "spark"),
    (50_000,   "🔥 FLAME I",   "flame"),
    (100_000,  "🔥 FLAME II",  "flame"),
    (175_000,  "🔥 FLAME III", "flame"),
    (275_000,  "⭐ STAR I",    "star"),
    (400_000,  "⭐ STAR II",   "star"),
    (600_000,  "⭐ STAR III",  "star"),
    (900_000,  "👑 LEGEND",    "legend"),
]

QUESTS = [
    {
        "id": "q_first_creation",
        "title": "First Genesis",
        "desc": "Register your very first creation on the Genesis Layer.",
        "reward": 5_000,
        "icon": "🌱",
        "check": lambda df, user, _: len(df[df.sovereign == user]) >= 1,
    },
    {
        "id": "q_three_creations",
        "title": "Trilogy of Wonders",
        "desc": "Bring three creations into the Genesis Layer.",
        "reward": 12_000,
        "icon": "🎨",
        "check": lambda df, user, _: len(df[df.sovereign == user]) >= 3,
    },
    {
        "id": "q_ten_creations",
        "title": "Sovereign Gallery",
        "desc": "Amass a collection of ten creations.",
        "reward": 30_000,
        "icon": "🖼️",
        "check": lambda df, user, _: len(df[df.sovereign == user]) >= 10,
    },
    {
        "id": "q_daily_upload",
        "title": "Daily Genesis",
        "desc": "Upload a creation today.",
        "reward": 2_500,
        "icon": "☀️",
        "check": lambda df, user, _: _today_upload(df, user),
    },
    {
        "id": "q_cert_download",
        "title": "Sacred Title Claimed",
        "desc": "Download a Genesis Certificate for any creation.",
        "reward": 3_000,
        "icon": "📜",
        "check": lambda df, user, ss: ss.get("cert_ever_downloaded", False),
    },
    {
        "id": "q_split_asset",
        "title": "Fractional Sovereign",
        "desc": "Activate fractional ownership on any creation.",
        "reward": 7_500,
        "icon": "🔀",
        "check": lambda df, user, _: _has_split(df, user),
    },
    {
        "id": "q_high_value",
        "title": "Million Imaginer",
        "desc": "Register a creation valued at 1,000,000 IMAGIX or more.",
        "reward": 25_000,
        "icon": "💎",
        "check": lambda df, user, _: _has_high_value(df, user, 1_000_000),
    },
    {
        "id": "q_image_upload",
        "title": "Visual Sovereign",
        "desc": "Upload a creation with an image file.",
        "reward": 4_000,
        "icon": "🖼️",
        "check": lambda df, user, _: _has_image_upload(df, user),
    },
]

# ── Quest helper lambdas (defined as module-level functions) ──
def _today_upload(df, user):
    udf = df[df.sovereign == user]
    if udf.empty:
        return False
    today = date.today().isoformat()
    return any(str(r.get("created_at", "")).startswith(today)
               for r in udf.to_dict("records"))

def _has_split(df, user):
    udf = df[df.sovereign == user]
    if udf.empty:
        return False
    return bool(udf["is_fractional"].astype(str).str.lower().isin(["true","1"]).any())

def _has_high_value(df, user, threshold):
    udf = df[df.sovereign == user]
    if udf.empty:
        return False
    return bool((pd.to_numeric(udf["value"], errors="coerce") >= threshold).any())

def _has_image_upload(df, user):
    udf = df[df.sovereign == user]
    if udf.empty:
        return False
    return any(
        str(r.get("file_path","")).lower().endswith((".jpg",".jpeg",".png"))
        for r in udf.to_dict("records")
    )

DEMO_SHOWCASE = [
    ("Star Dragon Awakening",       48_200,  "🐉"),
    ("Kingdom of Eternal Clouds",  125_000,  "☁️"),
    ("The Brave Robot Friend",      32_800,  "🤖"),
    ("Legendary Enchanted Sword",   67_500,  "⚔️"),
    ("Floating Family Castle",      89_000,  "🏰"),
    ("Crystal Phoenix Rising",      54_300,  "🦅"),
]


# ══════════════════════════════════════════════════════════════
# ② PAGE CONFIG — must be the very first Streamlit call
# ══════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="DELPHIA GENESIS | IMAGINARIUM",
    page_icon="🌟",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ══════════════════════════════════════════════════════════════
# ③ VISUAL THEME — Genesis CSS System v0.7
# ══════════════════════════════════════════════════════════════
def inject_theme():
    st.markdown(f"""
    <style>
    /* ── Google Fonts ── */
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700;900&family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=DM+Mono:wght@300;400;500&display=swap');

    /* ── CSS Variables ── */
    :root {{
        --space:    {C['space']};
        --celest:   {C['celestial']};
        --card:     {C['card']};
        --card2:    {C['card2']};
        --gold:     {C['gold']};
        --gold-dim: {C['gold_dim']};
        --teal:     {C['teal']};
        --purple:   {C['purple']};
        --purple2:  {C['purple2']};
        --muted:    {C['muted']};
        --white:    {C['white']};
    }}

    /* ── Base ── */
    html, body, [data-testid="stAppViewContainer"] {{
        background-color: var(--space);
        color: var(--gold);
    }}
    .stApp {{
        background:
            radial-gradient(ellipse 80% 60% at 15% 10%, rgba(13,45,74,0.9) 0%, transparent 70%),
            radial-gradient(ellipse 60% 50% at 85% 85%, rgba(10,31,53,0.8) 0%, transparent 70%),
            radial-gradient(ellipse 40% 40% at 50% 50%, rgba(157,78,221,0.04) 0%, transparent 60%),
            linear-gradient(180deg, #060f1a 0%, var(--space) 100%);
    }}

    /* ── Typography ── */
    h1, h2, h3 {{ font-family: 'Cinzel', serif !important; color: var(--gold) !important; letter-spacing: 1px; }}
    p, li, span, div {{ font-family: 'DM Mono', monospace; }}
    label {{ font-family: 'DM Mono', monospace !important; color: var(--teal) !important; font-size: 11px !important; }}

    /* ── Buttons — Base ── */
    .stButton > button {{
        background: linear-gradient(135deg, var(--purple), var(--purple2));
        color: var(--gold);
        border: 1px solid rgba(242,201,76,0.5);
        border-radius: 8px;
        font-family: 'Cinzel', serif;
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 1.5px;
        padding: 8px 14px;
        transition: all 0.22s ease;
        width: 100%;
    }}
    .stButton > button:hover {{
        background: linear-gradient(135deg, var(--gold), var(--gold-dim));
        color: var(--space);
        border-color: var(--gold);
        box-shadow: 0 0 18px rgba(242,201,76,0.45), 0 4px 16px rgba(0,0,0,0.4);
        transform: translateY(-2px);
    }}
    .stButton > button:active {{ transform: translateY(0px); }}
    /* Primary buttons */
    .stButton > button[kind="primary"],
    [data-testid="stFormSubmitButton"] > button {{
        background: linear-gradient(135deg, var(--gold), var(--gold-dim)) !important;
        color: var(--space) !important;
        font-size: 12px;
        padding: 11px 28px;
        border: none !important;
        box-shadow: 0 4px 20px rgba(242,201,76,0.3);
    }}
    [data-testid="stFormSubmitButton"] > button:hover {{
        background: linear-gradient(135deg, #ffe080, var(--gold)) !important;
        color: var(--space) !important;
        box-shadow: 0 0 24px rgba(242,201,76,0.6);
    }}

    /* ── Download button ── */
    .stDownloadButton > button {{
        background: linear-gradient(135deg, {C['teal']}22, {C['teal']}44) !important;
        color: var(--teal) !important;
        border: 1px solid var(--teal) !important;
        font-family: 'Cinzel', serif;
        font-size: 10px;
        letter-spacing: 1px;
        width: 100%;
        transition: all 0.2s;
    }}
    .stDownloadButton > button:hover {{
        background: var(--teal) !important;
        color: var(--space) !important;
        box-shadow: 0 0 16px rgba(0,229,192,0.4);
    }}

    /* ── Inputs & Selects ── */
    .stTextInput input,
    .stNumberInput input {{
        background-color: {C['card']} !important;
        color: var(--teal) !important;
        border: 1px solid rgba(157,78,221,0.6) !important;
        border-radius: 8px !important;
        font-family: 'DM Mono', monospace !important;
        font-size: 13px !important;
        caret-color: var(--gold);
    }}
    .stTextInput input:focus, .stNumberInput input:focus {{
        border-color: var(--gold) !important;
        box-shadow: 0 0 0 2px rgba(242,201,76,0.15) !important;
    }}
    .stSelectbox [data-baseweb="select"] > div {{
        background-color: {C['card']} !important;
        border: 1px solid rgba(157,78,221,0.6) !important;
        color: var(--teal) !important;
        font-family: 'DM Mono', monospace !important;
    }}

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {{
        background: transparent;
        border-bottom: 1px solid rgba(157,78,221,0.4);
        gap: 2px;
        padding-bottom: 0;
    }}
    .stTabs [data-baseweb="tab"] {{
        font-family: 'Cinzel', serif;
        font-size: 11px;
        letter-spacing: 1px;
        color: var(--muted);
        padding: 9px 18px;
        border-radius: 8px 8px 0 0;
        border: 1px solid transparent;
        border-bottom: none;
        transition: all 0.2s;
    }}
    .stTabs [data-baseweb="tab"]:hover {{
        color: var(--gold);
        background: rgba(242,201,76,0.05);
    }}
    .stTabs [aria-selected="true"] {{
        background: var(--card2) !important;
        color: var(--gold) !important;
        border-color: rgba(0,229,192,0.5) !important;
        border-bottom: 1px solid var(--card2) !important;
    }}

    /* ── Metrics ── */
    [data-testid="metric-container"] {{
        background: linear-gradient(135deg, {C['card']}, {C['card2']});
        border: 1px solid rgba(157,78,221,0.5);
        border-radius: 12px;
        padding: 12px 18px;
        transition: border-color 0.2s;
    }}
    [data-testid="metric-container"]:hover {{
        border-color: var(--gold);
    }}
    [data-testid="metric-container"] label {{
        color: var(--teal) !important;
        font-family: 'Cinzel', serif !important;
        font-size: 9px !important;
        letter-spacing: 2px !important;
        text-transform: uppercase;
    }}
    [data-testid="stMetricValue"] {{
        color: var(--gold) !important;
        font-family: 'Cinzel', serif !important;
        font-weight: 700 !important;
    }}
    [data-testid="stMetricDelta"] {{ font-size: 11px !important; }}

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, #080f1e 0%, #0a1628 60%, {C['space']} 100%);
        border-right: 1px solid rgba(157,78,221,0.4);
    }}
    [data-testid="stSidebar"] section {{ padding-top: 0; }}

    /* ── Progress bars ── */
    .stProgress > div > div > div > div {{
        background: linear-gradient(90deg, var(--purple), var(--teal) 60%, var(--gold));
        border-radius: 4px;
    }}
    .stProgress > div > div {{
        background: rgba(255,255,255,0.06);
        border-radius: 4px;
    }}

    /* ── Alerts ── */
    .stSuccess > div {{
        background: rgba(46,204,113,0.1) !important;
        border: 1px solid rgba(46,204,113,0.4) !important;
        color: #2ECC71 !important;
        font-family: 'DM Mono', monospace !important;
        border-radius: 10px !important;
    }}
    .stInfo > div {{
        background: rgba(0,229,192,0.08) !important;
        border: 1px solid rgba(0,229,192,0.35) !important;
        color: var(--teal) !important;
        font-family: 'DM Mono', monospace !important;
        border-radius: 10px !important;
    }}
    .stWarning > div {{
        background: rgba(242,201,76,0.08) !important;
        border: 1px solid rgba(242,201,76,0.35) !important;
        color: var(--gold) !important;
        border-radius: 10px !important;
    }}
    .stError > div {{
        background: rgba(255,107,107,0.1) !important;
        border: 1px solid rgba(255,107,107,0.4) !important;
        color: {C['danger']} !important;
        border-radius: 10px !important;
    }}

    /* ── File uploader ── */
    [data-testid="stFileUploader"] > div {{
        background: {C['card']} !important;
        border: 2px dashed rgba(157,78,221,0.5) !important;
        border-radius: 14px !important;
        transition: border-color 0.2s;
    }}
    [data-testid="stFileUploader"] > div:hover {{
        border-color: var(--gold) !important;
    }}

    /* ── Spinner ── */
    .stSpinner > div {{ border-top-color: var(--gold) !important; }}

    /* ── Divider ── */
    hr {{ border-color: rgba(157,78,221,0.25) !important; margin: 12px 0; }}

    /* ── Scrollbar ── */
    ::-webkit-scrollbar {{ width: 5px; height: 5px; }}
    ::-webkit-scrollbar-track {{ background: transparent; }}
    ::-webkit-scrollbar-thumb {{ background: rgba(157,78,221,0.5); border-radius: 3px; }}
    ::-webkit-scrollbar-thumb:hover {{ background: var(--purple); }}

    /* ═══════════════════════════════════════════════════════
       CUSTOM COMPONENTS
    ═══════════════════════════════════════════════════════ */

    /* ── Genesis Card ── */
    .g-card {{
        background: linear-gradient(145deg, {C['card']}, {C['card2']});
        border: 1px solid rgba(0,229,192,0.3);
        border-radius: 14px;
        overflow: hidden;
        transition: all 0.28s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        margin-bottom: 8px;
        cursor: default;
    }}
    .g-card:hover {{
        border-color: var(--gold);
        box-shadow:
            0 0 0 1px rgba(242,201,76,0.15),
            0 8px 32px rgba(0,0,0,0.5),
            0 0 40px rgba(242,201,76,0.12);
        transform: translateY(-5px) scale(1.01);
    }}
    .g-card-img {{
        height: 130px;
        background: linear-gradient(135deg, {C['celestial']}, #142f55);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 60px;
        border-bottom: 1px solid rgba(0,229,192,0.15);
        position: relative;
        overflow: hidden;
    }}
    .g-card-img::after {{
        content: '';
        position: absolute;
        inset: 0;
        background: radial-gradient(ellipse at 50% 80%, rgba(157,78,221,0.1) 0%, transparent 70%);
    }}
    .g-card-body {{ padding: 10px 13px 13px; }}
    .g-card-title {{
        font-family: 'Playfair Display', serif;
        color: #dde8ff;
        font-size: 12.5px;
        font-weight: 700;
        line-height: 1.35;
        min-height: 32px;
        margin-bottom: 5px;
    }}
    .g-card-value {{
        font-family: 'Cinzel', serif;
        color: var(--gold);
        font-size: 14px;
        font-weight: 700;
    }}
    .g-card-id {{
        font-family: 'DM Mono', monospace;
        color: var(--teal);
        font-size: 8.5px;
        opacity: 0.65;
        margin-top: 3px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}
    .g-card-badge {{
        position: absolute;
        top: 8px;
        right: 8px;
        background: rgba(5,18,31,0.88);
        border: 1px solid var(--gold);
        border-radius: 20px;
        padding: 2px 9px;
        font-family: 'Cinzel', serif;
        font-size: 7.5px;
        color: var(--gold);
        letter-spacing: 1px;
        backdrop-filter: blur(4px);
    }}
    .g-card-fractional {{
        position: absolute;
        bottom: 8px;
        right: 8px;
        background: rgba(0,229,192,0.15);
        border: 1px solid var(--teal);
        border-radius: 20px;
        padding: 2px 8px;
        font-family: 'Cinzel', serif;
        font-size: 7px;
        color: var(--teal);
        letter-spacing: 1px;
    }}

    /* ── Hero Banner ── */
    .g-hero {{
        background: linear-gradient(135deg, #0b1d35 0%, #15284a 50%, #0a1827 100%);
        border: 1px solid rgba(157,78,221,0.5);
        border-radius: 18px;
        padding: 32px 40px;
        text-align: center;
        position: relative;
        overflow: hidden;
        margin-bottom: 8px;
    }}
    .g-hero::before {{
        content: '';
        position: absolute;
        top: -60%;
        left: 50%;
        transform: translateX(-50%);
        width: 120%;
        height: 120%;
        background: radial-gradient(ellipse, rgba(157,78,221,0.1) 0%, transparent 65%);
        pointer-events: none;
    }}
    .g-hero-title {{
        font-family: 'Cinzel', serif;
        font-size: clamp(20px, 3vw, 30px);
        font-weight: 900;
        color: var(--gold);
        letter-spacing: 5px;
        margin: 0;
        text-shadow: 0 0 30px rgba(242,201,76,0.3);
    }}
    .g-hero-sub {{
        font-family: 'DM Mono', monospace;
        color: var(--teal);
        font-size: 11px;
        letter-spacing: 3px;
        margin-top: 8px;
        opacity: 0.9;
    }}

    /* ── Quest cards ── */
    .q-card {{
        background: linear-gradient(135deg, {C['card']}, {C['card2']});
        border: 1px solid rgba(157,78,221,0.45);
        border-radius: 12px;
        padding: 14px 18px;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        gap: 14px;
        transition: all 0.2s;
        position: relative;
    }}
    .q-card:hover {{ border-color: rgba(242,201,76,0.4); transform: translateX(3px); }}
    .q-card.done {{
        border-color: rgba(0,229,192,0.4);
        background: linear-gradient(135deg, rgba(0,229,192,0.04), rgba(0,229,192,0.02));
    }}
    .q-card.done::after {{
        content: '✓';
        position: absolute;
        right: 16px;
        top: 50%;
        transform: translateY(-50%);
        color: var(--teal);
        font-size: 18px;
        font-weight: 700;
    }}
    .q-icon {{ font-size: 26px; min-width: 34px; text-align: center; }}
    .q-info {{ flex: 1; }}
    .q-title {{
        font-family: 'Cinzel', serif;
        color: var(--gold);
        font-size: 12px;
        font-weight: 700;
        margin-bottom: 2px;
    }}
    .q-desc {{ font-family: 'DM Mono', monospace; color: var(--muted); font-size: 10.5px; line-height: 1.4; }}
    .q-reward {{
        font-family: 'Cinzel', serif;
        color: var(--teal);
        font-size: 12px;
        font-weight: 700;
        white-space: nowrap;
        margin-right: 28px;
    }}

    /* ── Rank badge ── */
    .rank-pill {{
        background: linear-gradient(135deg, {C['card']}, #1c3560);
        border: 2px solid var(--gold);
        border-radius: 50px;
        padding: 7px 22px;
        display: inline-block;
        font-family: 'Cinzel', serif;
        color: var(--gold);
        font-size: 13px;
        font-weight: 700;
        letter-spacing: 2px;
        box-shadow: 0 0 20px rgba(242,201,76,0.18), inset 0 0 10px rgba(242,201,76,0.05);
    }}

    /* ── Parental mode banner ── */
    .parent-mode {{
        background: linear-gradient(135deg, rgba(242,201,76,0.08), rgba(242,201,76,0.04));
        border: 1px solid rgba(242,201,76,0.5);
        border-radius: 10px;
        padding: 12px 16px;
        margin: 8px 0;
    }}
    .parent-mode-title {{
        font-family: 'Cinzel', serif;
        color: var(--gold);
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 1.5px;
    }}

    /* ── Wallet card ── */
    .wallet-card {{
        background: linear-gradient(145deg, #0a1e38, #0d2540);
        border: 2px solid rgba(242,201,76,0.5);
        border-radius: 16px;
        padding: 20px 24px;
        text-align: center;
        position: relative;
        overflow: hidden;
        margin-bottom: 16px;
    }}
    .wallet-card::before {{
        content: '';
        position: absolute;
        top: -40%;
        left: 50%;
        transform: translateX(-50%);
        width: 80%;
        height: 80%;
        background: radial-gradient(ellipse, rgba(242,201,76,0.06) 0%, transparent 70%);
    }}
    .wallet-amount {{
        font-family: 'Cinzel', serif;
        color: var(--gold);
        font-size: clamp(22px, 4vw, 36px);
        font-weight: 900;
        letter-spacing: 2px;
        text-shadow: 0 0 20px rgba(242,201,76,0.4);
    }}
    .wallet-label {{
        font-family: 'DM Mono', monospace;
        color: var(--teal);
        font-size: 10px;
        letter-spacing: 3px;
        margin-top: 4px;
        opacity: 0.85;
    }}

    /* ── Demo showcase shimmer ── */
    @keyframes shimmer {{
        0%   {{ background-position: -200% center; }}
        100% {{ background-position: 200% center; }}
    }}
    .showcase-glow {{
        background: linear-gradient(90deg,
            transparent 0%,
            rgba(242,201,76,0.06) 30%,
            rgba(0,229,192,0.06) 50%,
            rgba(242,201,76,0.06) 70%,
            transparent 100%);
        background-size: 200% auto;
        animation: shimmer 4s linear infinite;
        border-radius: 14px;
    }}

    /* ── Sidebar Terminal ── */
    .terminal-block {{
        background: rgba(0,0,0,0.25);
        border: 1px solid rgba(0,229,192,0.15);
        border-radius: 10px;
        padding: 12px 14px;
        margin: 6px 0;
        font-family: 'DM Mono', monospace;
    }}
    .terminal-key {{
        font-size: 8.5px;
        color: {C['teal']};
        letter-spacing: 1.5px;
        text-transform: uppercase;
        opacity: 0.8;
    }}
    .terminal-val {{
        font-family: 'Cinzel', serif;
        color: {C['gold']};
        font-size: 12.5px;
        font-weight: 700;
        margin-top: 1px;
    }}

    /* ── Markdown overrides ── */
    .stMarkdown {{ color: var(--muted); }}
    .stMarkdown strong {{ color: var(--gold) !important; }}
    .stMarkdown code {{
        background: rgba(0,229,192,0.1) !important;
        color: var(--teal) !important;
        border: 1px solid rgba(0,229,192,0.2) !important;
        border-radius: 4px;
        font-family: 'DM Mono', monospace;
        font-size: 11px;
    }}

    /* ── Caption ── */
    .stCaption {{ color: var(--muted) !important; font-size: 10.5px !important; }}

    /* ── Mobile responsive ── */
    @media (max-width: 768px) {{
        .g-hero {{ padding: 20px 16px; }}
        .g-hero-title {{ font-size: 18px; letter-spacing: 2px; }}
        .g-card-img {{ height: 100px; font-size: 44px; }}
        .q-card {{ flex-wrap: wrap; }}
        .q-reward {{ margin-right: 0; }}
    }}
    </style>
    """, unsafe_allow_html=True)

inject_theme()


# ══════════════════════════════════════════════════════════════
# ④ DATA LAYER
# ══════════════════════════════════════════════════════════════

CSV_COLS = [
    "id", "name", "sovereign", "value", "emoji",
    "file_path", "created_at", "is_fractional",
    "cert_downloaded", "fraction_count",
]

def ensure_dirs(user: str):
    """Create required directories."""
    Path(CREATIONS_DIR).mkdir(exist_ok=True)
    Path(f"{CREATIONS_DIR}/{user}").mkdir(parents=True, exist_ok=True)


def load_creations() -> pd.DataFrame:
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE)
            for col in CSV_COLS:
                if col not in df.columns:
                    df[col] = ""
            return df
        except Exception:
            pass
    return pd.DataFrame(columns=CSV_COLS)


def save_creations(df: pd.DataFrame):
    try:
        df.to_csv(DATA_FILE, index=False)
    except Exception as e:
        st.warning(f"Auto-save warning: {e}")


def load_wallet(user: str) -> int:
    """Load IMAGIX balance from wallet CSV."""
    if os.path.exists(WALLET_FILE):
        try:
            df = pd.read_csv(WALLET_FILE)
            row = df[df["sovereign"] == user]
            if not row.empty:
                return int(row.iloc[0]["imagix"])
        except Exception:
            pass
    return 0


def save_wallet(user: str, imagix: int):
    row = {"sovereign": user, "imagix": imagix}
    if os.path.exists(WALLET_FILE):
        try:
            df = pd.read_csv(WALLET_FILE)
            if user in df["sovereign"].values:
                df.loc[df["sovereign"] == user, "imagix"] = imagix
            else:
                df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
            df.to_csv(WALLET_FILE, index=False)
            return
        except Exception:
            pass
    pd.DataFrame([row]).to_csv(WALLET_FILE, index=False)


def load_completed_quests(user: str) -> set:
    if os.path.exists(QUESTS_FILE):
        try:
            df = pd.read_csv(QUESTS_FILE)
            row = df[df["sovereign"] == user]
            if not row.empty:
                raw = str(row.iloc[0]["completed_ids"])
                return set(x for x in raw.split(",") if x.strip())
        except Exception:
            pass
    return set()


def save_completed_quests(user: str, completed: set):
    row = {"sovereign": user, "completed_ids": ",".join(completed)}
    if os.path.exists(QUESTS_FILE):
        try:
            df = pd.read_csv(QUESTS_FILE)
            if user in df["sovereign"].values:
                df.loc[df["sovereign"] == user, "completed_ids"] = row["completed_ids"]
            else:
                df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
            df.to_csv(QUESTS_FILE, index=False)
            return
        except Exception:
            pass
    pd.DataFrame([row]).to_csv(QUESTS_FILE, index=False)


def generate_asset_id(name: str, sovereign: str) -> str:
    raw = f"{name}::{sovereign}::{datetime.now().isoformat()}"
    return "GEN-" + hashlib.sha256(raw.encode()).hexdigest()[:8].upper()


def img_to_b64(path: str) -> str | None:
    """Return base64 data-URI for an image file, or None on failure."""
    try:
        with open(path, "rb") as f:
            data = base64.b64encode(f.read()).decode()
        ext = Path(path).suffix.lower().lstrip(".")
        mime = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png"}.get(ext, "jpeg")
        return f"data:image/{mime};base64,{data}"
    except Exception:
        return None


# ══════════════════════════════════════════════════════════════
# ⑤ RANK ENGINE
# ══════════════════════════════════════════════════════════════

def get_rank(imagix: int) -> dict:
    rank_name, curr_t = RANK_TIERS[0][1], 0
    next_t = RANK_TIERS[1][0]
    for i, (t, name, _) in enumerate(RANK_TIERS):
        if imagix >= t:
            rank_name, curr_t = name, t
            next_t = RANK_TIERS[i + 1][0] if i + 1 < len(RANK_TIERS) else t
    span = next_t - curr_t
    progress = min((imagix - curr_t) / span, 1.0) if span > 0 else 1.0
    return {
        "name": rank_name,
        "progress": progress,
        "curr": curr_t,
        "next": next_t,
        "maxed": next_t == curr_t,
    }


# ══════════════════════════════════════════════════════════════
# ⑥ QUEST ENGINE
# ══════════════════════════════════════════════════════════════

def run_quest_checks(df: pd.DataFrame, user: str) -> int:
    """
    Evaluate all quests against current state.
    Awards any newly completed quests.
    Returns total IMAGIX delta from newly completed quests.
    """
    completed = st.session_state["quest_completed"]
    ss_extra   = {
        "cert_ever_downloaded": st.session_state.get("cert_ever_downloaded", False),
    }
    earned = 0
    newly  = []

    for q in QUESTS:
        if q["id"] in completed:
            continue
        try:
            if q["check"](df, user, ss_extra):
                completed.add(q["id"])
                earned += q["reward"]
                newly.append(q)
        except Exception:
            pass

    if newly:
        st.session_state["quest_completed"] = completed
        st.session_state["imagix"] += earned
        save_completed_quests(user, completed)
        save_wallet(user, st.session_state["imagix"])
        for q in newly:
            st.toast(
                f"⚡ QUEST COMPLETE: {q['title']}  +{q['reward']:,} IMAGIX",
                icon="🏆"
            )
    return earned


# ══════════════════════════════════════════════════════════════
# ⑦ PDF CERTIFICATE — ReportLab
# ══════════════════════════════════════════════════════════════

def make_certificate(name: str, asset_id: str, sovereign: str, value: int) -> bytes:
    """
    Generates a celestial Genesis Certificate PDF.
    Returns raw bytes — no temp files, safe on Streamlit Cloud.
    """
    buf = io.BytesIO()
    W, H = A4   # 595 × 842 pt

    c = rl_canvas.Canvas(buf, pagesize=A4)
    c.setTitle(f"Genesis Certificate · {name}")

    # ── Deep space background ──────────────────────────────
    c.setFillColor(HexColor("#04101e"))
    c.rect(0, 0, W, H, fill=1, stroke=0)

    # Star field (tiny dots)
    import random
    rng = random.Random(42)
    c.setFillColor(HexColor("#ffffff"))
    for _ in range(90):
        sx, sy = rng.uniform(30, W-30), rng.uniform(80, H-80)
        sr = rng.uniform(0.3, 1.1)
        c.setFillColorRGB(1, 1, 1, alpha=rng.uniform(0.1, 0.45))
        c.circle(sx, sy, sr, fill=1, stroke=0)

    # Central glow
    for r, a in [(200, 0.025), (140, 0.045), (90, 0.07), (50, 0.06), (25, 0.05)]:
        c.setFillColorRGB(0.35, 0.28, 0.82, alpha=a)
        c.circle(W/2, H/2, r, fill=1, stroke=0)

    # ── Double border ──────────────────────────────────────
    c.setStrokeColor(HexColor(C["gold"]))
    c.setLineWidth(2.8)
    c.roundRect(15, 15, W-30, H-30, 16, fill=0, stroke=1)

    c.setStrokeColor(HexColor(C["purple"]))
    c.setLineWidth(0.9)
    c.roundRect(23, 23, W-46, H-46, 12, fill=0, stroke=1)

    # Gold inner line
    c.setStrokeColor(HexColor(C["gold"]))
    c.setLineWidth(0.35)
    c.setDash(4, 3)
    c.roundRect(28, 28, W-56, H-56, 10, fill=0, stroke=1)
    c.setDash()

    # ── Corner ornaments ────────────────────────────────────
    for ox, oy in [(24, 24), (W-24, 24), (24, H-24), (W-24, H-24)]:
        c.setStrokeColor(HexColor(C["gold"]))
        c.setLineWidth(1.4)
        c.circle(ox, oy, 7, fill=0, stroke=1)
        c.setFillColor(HexColor(C["gold"]))
        c.circle(ox, oy, 3, fill=1, stroke=0)

    # ── Header band ─────────────────────────────────────────
    c.setFillColorRGB(0.04, 0.10, 0.19, alpha=0.95)
    c.roundRect(32, H-108, W-64, 76, 8, fill=1, stroke=0)
    c.setStrokeColor(HexColor(C["gold"]))
    c.setLineWidth(0.6)
    c.roundRect(32, H-108, W-64, 76, 8, fill=0, stroke=1)

    c.setFillColor(HexColor(C["gold"]))
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(W/2, H-64, "DELPHIA GENESIS")

    c.setFillColor(HexColor(C["teal"]))
    c.setFont("Helvetica", 9.5)
    c.drawCentredString(W/2, H-86, "✦  CERTIFICATE OF IMAGINATION  ·  GENESIS LAYER  ✦")

    # ── Central star ────────────────────────────────────────
    star_cy = H - 192

    # Outer glow rings
    for r, a in [(55, 0.07), (42, 0.10), (32, 0.08)]:
        c.setFillColorRGB(0.95, 0.79, 0.30, alpha=a)
        c.circle(W/2, star_cy, r, fill=1, stroke=0)

    # 5-point star
    def draw_star(cx, cy, ro, ri, pts=5):
        path = c.beginPath()
        for i in range(pts * 2):
            angle = math.pi / pts * i - math.pi / 2
            r = ro if i % 2 == 0 else ri
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            path.moveTo(x, y) if i == 0 else path.lineTo(x, y)
        path.close()
        c.drawPath(path, fill=1, stroke=1)

    c.setFillColor(HexColor(C["gold"]))
    c.setStrokeColor(HexColor(C["purple"]))
    c.setLineWidth(1.2)
    draw_star(W/2, star_cy, 34, 14)

    # Teal ring around star
    c.setStrokeColor(HexColor(C["teal"]))
    c.setLineWidth(0.6)
    c.setFillColorRGB(0, 0, 0, alpha=0)
    c.circle(W/2, star_cy, 50, fill=0, stroke=1)

    # ── Decorative rule ─────────────────────────────────────
    ry = H - 238
    c.setStrokeColor(HexColor(C["purple"]))
    c.setLineWidth(0.7)
    c.line(48, ry, W-48, ry)
    c.setStrokeColor(HexColor(C["gold"]))
    c.setLineWidth(0.35)
    c.line(58, ry-5, W-58, ry-5)

    # ── Fields ──────────────────────────────────────────────
    def draw_field(label: str, val: str, y: float):
        c.setFillColor(HexColor(C["teal"]))
        c.setFont("Helvetica", 7.5)
        c.drawCentredString(W/2, y + 17, label.upper())
        # Underline
        c.setStrokeColor(HexColor(C["purple"]))
        c.setLineWidth(0.35)
        c.line(72, y + 13, W-72, y + 13)
        # Value
        c.setFillColor(HexColor(C["white"]))
        c.setFont("Helvetica-Bold", 13)
        display = val[:50] + "…" if len(val) > 50 else val
        c.drawCentredString(W/2, y, display)

    fields_data = [
        ("Creation",        str(name)[:55]),
        ("Genesis ID",      str(asset_id)),
        ("Young Sovereign", str(sovereign)[:45]),
        ("Imagined Value",  f"{int(value):,} IMAGIX"),
        ("Date Sealed",     datetime.now().strftime("%B %Y").upper()),
        ("Status",          "SACRED & IMMUTABLE"),
    ]

    fy = H - 278
    gap = 52
    for i, (lbl, v) in enumerate(fields_data):
        draw_field(lbl, v, fy - i * gap)

    # ── Bottom rule ─────────────────────────────────────────
    bot_y = fy - len(fields_data) * gap + 8
    c.setStrokeColor(HexColor(C["gold"]))
    c.setLineWidth(0.7)
    c.line(48, bot_y, W-48, bot_y)
    c.setStrokeColor(HexColor(C["purple"]))
    c.setLineWidth(0.35)
    c.line(58, bot_y-5, W-58, bot_y-5)

    # ── Signature ───────────────────────────────────────────
    sig_y = bot_y - 52
    c.setFillColor(HexColor(C["purple"]))
    c.setFont("Helvetica", 8)
    c.drawCentredString(W/2, sig_y + 18, "— Signed by the Keeper of the Genesis Layer —")
    c.setFillColor(HexColor(C["gold"]))
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(W/2, sig_y, "REY DELPHI  ·  REINO DE DELPHIA  ·  KARDASHEV VI")

    # ── Footer ──────────────────────────────────────────────
    c.setFillColor(HexColor(C["teal"]))
    c.setFont("Helvetica", 7)
    c.drawCentredString(W/2, 30, "Delphia Genesis v0.7  ·  Where Imagination Becomes Sovereign  ·  delphia.genesis")

    c.save()
    return buf.getvalue()


# ══════════════════════════════════════════════════════════════
# ⑧ SESSION STATE INITIALISATION
# ══════════════════════════════════════════════════════════════

_SS_DEFAULTS = {
    "authenticated":       False,
    "user":                "",
    "imagix":              0,
    "quest_completed":     set(),
    "creations_df":        None,
    "split_open":          {},          # asset_id → bool
    "cert_triggered":      {},          # asset_id → bool
    "cert_ever_downloaded":False,
    "parent_mode":         False,
    "parent_confirmed":    False,
}

for _k, _v in _SS_DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# ══════════════════════════════════════════════════════════════
# ⑨ LOGIN GATE
# ══════════════════════════════════════════════════════════════

if not st.session_state["authenticated"]:
    # Centered login
    st.markdown("""
    <div class="g-hero" style="margin-top:50px; padding:52px 40px;">
        <div class="g-hero-title">⬟ DELPHIA GENESIS ⬟</div>
        <div class="g-hero-sub">THE IMAGINARIUM · GENESIS LAYER v0.7</div>
    </div>
    """, unsafe_allow_html=True)

    _, mid, _ = st.columns([1, 1.8, 1])
    with mid:
        st.markdown(f"""
        <div style="text-align:center; margin-bottom:24px;">
            <div style="font-family:'DM Mono',monospace; color:{C['muted']}; font-size:12px; line-height:1.8;">
                Enter your Kingdom Name to access<br>your Sovereign Vault on the Genesis Layer.
            </div>
        </div>
        """, unsafe_allow_html=True)

        kingdom = st.text_input(
            "Kingdom Name",
            placeholder="e.g. Astra Nova",
            key="login_kingdom",
            label_visibility="collapsed",
        )
        st.caption("Your unique sovereign identity within the Delphia Multiverse.")
        st.write("")

        if st.button("✦ ENTER THE IMAGINARIUM", type="primary", use_container_width=True):
            if kingdom.strip():
                u = kingdom.strip()
                st.session_state["authenticated"]   = True
                st.session_state["user"]            = u
                st.session_state["quest_completed"] = load_completed_quests(u)
                st.session_state["imagix"]          = load_wallet(u)
                ensure_dirs(u)
                st.rerun()
            else:
                st.warning("Your kingdom must bear a name, Young Sovereign.")
    st.stop()


# ══════════════════════════════════════════════════════════════
# ⑩ MAIN APP — Authenticated
# ══════════════════════════════════════════════════════════════

user: str = st.session_state["user"]
ensure_dirs(user)

# Load creations once per session
if st.session_state["creations_df"] is None:
    st.session_state["creations_df"] = load_creations()

df_all: pd.DataFrame = st.session_state["creations_df"]
user_df = df_all[df_all["sovereign"] == user].copy()

# Run quest auto-detection every render
run_quest_checks(df_all, user)

# Re-read user_df after quest check (imagix may have changed)
total_imagix = st.session_state["imagix"]
rank = get_rank(total_imagix)
n_quests_done = len(st.session_state["quest_completed"])


# ── A. HEADER ────────────────────────────────────────────────
h1, h2, h3, h4, h5 = st.columns([4, 1, 1, 1, 1])

h1.markdown(f"""
<div style="padding-top:8px;">
    <span style="font-family:'Cinzel',serif; font-size:17px; color:{C['gold']}; font-weight:700;">
        🌟 {user}
    </span>
    &nbsp;<span style="color:{C['muted']}; font-size:13px;">·</span>&nbsp;
    <span class="rank-pill" style="font-size:11px; padding:4px 14px;">
        {rank['name']}
    </span>
</div>
""", unsafe_allow_html=True)

h2.metric("IMAGIX", f"{total_imagix:,} 𝕀",
          delta=f"+{st.session_state.get('_last_delta',0):,}" if st.session_state.get('_last_delta',0) else None)
h3.metric("CREATIONS", len(user_df))
h4.metric("QUESTS", f"{n_quests_done}/{len(QUESTS)}")

if h5.button("✦ LOGOUT"):
    for k in list(_SS_DEFAULTS.keys()):
        if k in st.session_state:
            del st.session_state[k]
    st.rerun()

# Rank progress bar
pb_col, _ = st.columns([3, 1])
with pb_col:
    if not rank["maxed"]:
        st.progress(
            rank["progress"],
            text=f"Progress to next rank · {total_imagix:,} / {rank['next']:,} IMAGIX"
        )
    else:
        st.progress(1.0, text="👑 LEGEND — Supreme Sovereign of the Genesis Layer")

st.divider()


# ══════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════

tab_vault, tab_wallet, tab_quests, tab_market, tab_upload = st.tabs([
    "🌌 MY VAULT",
    "💎 WALLET",
    "⚔️ QUESTS",
    "🌠 MARKETPLACE",
    "🌱 UPLOAD",
])


# ────────────────────────────────────────────────────────────
# TAB 1 — VAULT
# ────────────────────────────────────────────────────────────
with tab_vault:
    col_title, col_filter = st.columns([3, 1])
    col_title.markdown("### 🌌 SOVEREIGN CREATIONS VAULT")
    
    # Filter control
    with col_filter:
        sort_opt = st.selectbox(
            "Sort by",
            ["Newest first", "Highest value", "Alphabetical"],
            label_visibility="collapsed",
        )

    if user_df.empty:
        # ── Enhanced showcase ──────────────────────────────
        st.info("🌠 Your vault awaits its first creation. Upload below to begin your Genesis journey!")
        st.markdown(f"""
        <div style="font-family:'Cinzel',serif; color:{C['gold']};
             font-size:14px; margin:20px 0 12px; letter-spacing:1px;">
            ✦ GENESIS SHOWCASE — Creations from the Multiverse
        </div>
        """, unsafe_allow_html=True)
        demo_cols = st.columns(6)
        for i, (dname, dval, demoji) in enumerate(DEMO_SHOWCASE):
            with demo_cols[i % 6]:
                st.markdown(f"""
                <div class="g-card showcase-glow">
                    <div class="g-card-img">{demoji}</div>
                    <div class="g-card-body">
                        <div class="g-card-badge">SHOWCASE</div>
                        <div class="g-card-title">{dname}</div>
                        <div class="g-card-value">{dval:,} 𝕀</div>
                        <div class="g-card-id">DEMO · GENESIS MULTIVERSE</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    else:
        # ── Sort ──────────────────────────────────────────
        sort_df = user_df.copy()
        if sort_opt == "Newest first":
            sort_df = sort_df.sort_values("created_at", ascending=False)
        elif sort_opt == "Highest value":
            sort_df["_v"] = pd.to_numeric(sort_df["value"], errors="coerce").fillna(0)
            sort_df = sort_df.sort_values("_v", ascending=False)
        else:
            sort_df = sort_df.sort_values("name")

        st.caption(f"{len(sort_df)} creation(s) on the Genesis Layer")

        records = sort_df.to_dict("records")
        COLS_PER_ROW = 4

        for row_start in range(0, len(records), COLS_PER_ROW):
            chunk = records[row_start : row_start + COLS_PER_ROW]
            cols = st.columns(COLS_PER_ROW)

            for ci, rec in enumerate(chunk):
                with cols[ci]:
                    aid    = str(rec.get("id", ""))
                    rname  = str(rec.get("name", "Unknown"))
                    rval   = int(float(str(rec.get("value", 0)).replace(",", "") or 0))
                    remoji = str(rec.get("emoji") or "🌟")
                    rfp    = str(rec.get("file_path", ""))
                    is_frac = str(rec.get("is_fractional","")).lower() in ("true","1")
                    n_frac = int(float(str(rec.get("fraction_count", 100)) or 100))

                    # ── Card render ─────────────────────────
                    frac_badge = '<div class="g-card-fractional">⅒ FRACTIONAL</div>' if is_frac else ""

                    # Try to show real image if available
                    has_img = (rfp and os.path.exists(rfp) and
                               rfp.lower().endswith((".jpg",".jpeg",".png")))

                    if has_img:
                        b64 = img_to_b64(rfp)
                        if b64:
                            st.markdown(f"""
                            <div class="g-card">
                                <div class="g-card-img" style="padding:0; position:relative;">
                                    <img src="{b64}" style="width:100%; height:130px;
                                         object-fit:cover; display:block;">
                                    {frac_badge}
                                </div>
                                <div class="g-card-body">
                                    <div class="g-card-title">{rname}</div>
                                    <div class="g-card-value">{rval:,} 𝕀</div>
                                    <div class="g-card-id">{aid}</div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            # Fallback to emoji card
                            st.markdown(f"""
                            <div class="g-card">
                                <div class="g-card-img">{remoji}{frac_badge}</div>
                                <div class="g-card-body">
                                    <div class="g-card-title">{rname}</div>
                                    <div class="g-card-value">{rval:,} 𝕀</div>
                                    <div class="g-card-id">{aid}</div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div class="g-card">
                            <div class="g-card-img">
                                {remoji}
                                {frac_badge}
                            </div>
                            <div class="g-card-body">
                                <div class="g-card-title">{rname}</div>
                                <div class="g-card-value">{rval:,} 𝕀</div>
                                <div class="g-card-id">{aid}</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                    # ── Action buttons ─────────────────────
                    b1, b2 = st.columns(2)

                    # TITLE → Certificate
                    with b1:
                        if st.button("📜 TITLE", key=f"title_{aid}"):
                            st.session_state["cert_triggered"][aid] = True
                            st.session_state["cert_ever_downloaded"] = True
                            run_quest_checks(df_all, user)

                    if st.session_state["cert_triggered"].get(aid):
                        try:
                            pdf = make_certificate(rname, aid, user, rval)
                            safe_fn = rname.replace(" ", "_")[:28]
                            st.download_button(
                                "⬇️ Download",
                                data=pdf,
                                file_name=f"{safe_fn}_Certificate.pdf",
                                mime="application/pdf",
                                key=f"dl_{aid}",
                                use_container_width=True,
                            )
                            # Persist cert flag
                            df_all.loc[df_all["id"]==aid, "cert_downloaded"] = True
                            save_creations(df_all)
                        except Exception as e:
                            st.error(f"Certificate error: {e}")

                    # SPLIT → Fractional ownership
                    with b2:
                        split_lbl = "🔀 SPLIT" if not is_frac else "⅒ FRACS"
                        if st.button(split_lbl, key=f"split_{aid}"):
                            st.session_state["split_open"][aid] = (
                                not st.session_state["split_open"].get(aid, False)
                            )
                            if not is_frac:
                                # Mark fractional in DataFrame
                                df_all.loc[df_all["id"]==aid, "is_fractional"] = True
                                df_all.loc[df_all["id"]==aid, "fraction_count"] = 100
                                save_creations(df_all)
                                st.session_state["creations_df"] = df_all
                                run_quest_checks(df_all, user)

                    if st.session_state["split_open"].get(aid):
                        frac_val = rval / n_frac
                        st.success(
                            f"**{rname}** fractionalised into **{n_frac}** shares  \n"
                            f"Each share: **{frac_val:,.0f} 𝕀**  \n"
                            f"Status: **FRACTIONAL OWNERSHIP ACTIVE** ✦"
                        )


# ────────────────────────────────────────────────────────────
# TAB 2 — WALLET
# ────────────────────────────────────────────────────────────
with tab_wallet:
    st.markdown("### 💎 IMAGIX WALLET")

    wc1, wc2, wc3 = st.columns([1, 1.5, 1])
    with wc2:
        st.markdown(f"""
        <div class="wallet-card">
            <div class="wallet-label">CURRENT BALANCE</div>
            <div class="wallet-amount">{total_imagix:,} 𝕀</div>
            <div class="wallet-label" style="margin-top:8px;">IMAGIX · GENESIS LAYER</div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # Quest earnings breakdown
    st.markdown("#### ✦ Earnings Ledger")
    ledger_data = []
    for q in QUESTS:
        if q["id"] in st.session_state["quest_completed"]:
            ledger_data.append({
                "Quest": f"{q['icon']} {q['title']}",
                "Status": "✅ Completed",
                "Reward": f"+{q['reward']:,} 𝕀",
            })
        else:
            ledger_data.append({
                "Quest": f"{q['icon']} {q['title']}",
                "Status": "○ Pending",
                "Reward": f"+{q['reward']:,} 𝕀",
            })

    if ledger_data:
        df_ledger = pd.DataFrame(ledger_data)
        st.dataframe(
            df_ledger,
            use_container_width=True,
            hide_index=True,
        )

    total_potential = sum(q["reward"] for q in QUESTS)
    earned = sum(q["reward"] for q in QUESTS if q["id"] in st.session_state["quest_completed"])
    remaining = total_potential - earned

    st.divider()
    wcol1, wcol2, wcol3 = st.columns(3)
    wcol1.metric("EARNED", f"{earned:,} 𝕀")
    wcol2.metric("POTENTIAL", f"{total_potential:,} 𝕀")
    wcol3.metric("REMAINING", f"{remaining:,} 𝕀")


# ────────────────────────────────────────────────────────────
# TAB 3 — QUESTS & PROGRESS
# ────────────────────────────────────────────────────────────
with tab_quests:
    st.markdown("### ⚔️ QUESTS & PROGRESS")

    # Rank display
    qr1, qr2 = st.columns([2, 1])
    with qr1:
        st.markdown(f"""
        <div style="margin-bottom:18px;">
            <div style="font-family:'DM Mono',monospace; color:{C['teal']};
                 font-size:9px; letter-spacing:3px; margin-bottom:8px;">CURRENT RANK</div>
            <div class="rank-pill">{rank['name']}</div>
        </div>
        """, unsafe_allow_html=True)

        if not rank["maxed"]:
            needed = rank["next"] - total_imagix
            st.progress(rank["progress"],
                        text=f"{needed:,} IMAGIX needed to advance")
        else:
            st.progress(1.0, text="👑 Maximum rank — you are LEGEND")

    with qr2:
        st.markdown(f"""
        <div style="background:{C['card']}; border:1px solid rgba(157,78,221,0.4);
             border-radius:12px; padding:16px 20px; text-align:center;">
            <div style="font-family:'DM Mono',monospace; color:{C['teal']};
                 font-size:9px; letter-spacing:2px; margin-bottom:10px;">RANK TIERS</div>
            <div style="font-family:'Cinzel',serif; color:{C['muted']};
                 font-size:9.5px; line-height:2.1;">
                ✦ SPARK I–III · 0 – 25k<br>
                🔥 FLAME I–III · 50k – 175k<br>
                ⭐ STAR I–III · 275k – 600k<br>
                👑 LEGEND · 900k +
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()
    st.markdown("#### Active Quests")

    completed_ids = st.session_state["quest_completed"]
    done_count = 0
    for q in QUESTS:
        is_done = q["id"] in completed_ids
        done_count += int(is_done)
        css = "q-card done" if is_done else "q-card"
        st.markdown(f"""
        <div class="{css}">
            <div class="q-icon">{q['icon']}</div>
            <div class="q-info">
                <div class="q-title">{'✅ ' if is_done else '○ '}{q['title']}</div>
                <div class="q-desc">{q['desc']}</div>
            </div>
            <div class="q-reward">+{q['reward']:,} 𝕀</div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()
    st.markdown(f"""
    **Completed:** `{done_count} / {len(QUESTS)}`  &nbsp;·&nbsp;
    **Total earned:** `{total_imagix:,} 𝕀`  &nbsp;·&nbsp;
    **Remaining potential:** `{sum(q['reward'] for q in QUESTS if q['id'] not in completed_ids):,} 𝕀`
    """)


# ────────────────────────────────────────────────────────────
# TAB 4 — MARKETPLACE
# ────────────────────────────────────────────────────────────
with tab_market:
    st.markdown("### 🌠 GENESIS MARKETPLACE")
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,{C['card']},{C['card2']});
         border:1px solid rgba(242,201,76,0.4); border-radius:16px;
         padding:40px 32px; text-align:center; position:relative; overflow:hidden;">
        <div style="position:absolute; top:-40%; left:50%; transform:translateX(-50%);
             width:80%; height:80%;
             background:radial-gradient(ellipse, rgba(242,201,76,0.05) 0%, transparent 70%);
             pointer-events:none;"></div>
        <div style="font-size:54px; margin-bottom:16px;">🌠</div>
        <div style="font-family:'Cinzel',serif; color:{C['gold']};
             font-size:20px; font-weight:700; letter-spacing:2px;">GENESIS MARKETPLACE</div>
        <div style="font-family:'DM Mono',monospace; color:{C['teal']};
             font-size:11px; margin-top:10px; letter-spacing:2px;">
            Secure Sovereign Trading · Arriving in v0.8
        </div>
        <div style="font-family:'DM Mono',monospace; color:{C['muted']};
             font-size:10.5px; margin-top:20px; line-height:2;">
            ✦ List creations for sovereign trading<br>
            ✦ Fractional ownership exchange<br>
            ✦ IMAGIX escrow & settlement system<br>
            ✦ Sovereign-to-Sovereign auctions<br>
            ✦ Parental approval gates for large trades
        </div>
    </div>
    """, unsafe_allow_html=True)


# ────────────────────────────────────────────────────────────
# TAB 5 — UPLOAD
# ────────────────────────────────────────────────────────────
with tab_upload:
    st.markdown("### 🌱 REGISTER YOUR CREATION")
    st.caption("Inscribe your art, story, or craft onto the Genesis Layer — permanently.")

    with st.form("genesis_upload", clear_on_submit=True):
        creation_name = st.text_input(
            "Creation Name ✦",
            placeholder="e.g. The Adventures of Luna the Fox",
        )

        uc1, uc2 = st.columns(2)
        with uc1:
            emoji_pick = st.selectbox(
                "Creation Emblem",
                ["🌟","🐉","☁️","🤖","⚔️","🏰","🌙","🔮","🦋",
                 "🌊","🦅","🌸","💎","🔥","⚡","🎨","🎭","🏆",
                 "🦁","🌺","🎪","🏺","🗝️","📜","🌈","🦄","🐬"],
            )
        with uc2:
            imagined_val = st.number_input(
                "Imagined Value (IMAGIX)",
                min_value=100,
                max_value=10_000_000,
                value=10_000,
                step=500,
            )

        uploaded_file = st.file_uploader(
            "Upload your creation (image or PDF — optional)",
            type=["jpg","jpeg","png","pdf"],
            help="Images will appear as your card thumbnail in the Vault.",
        )

        description = st.text_area(
            "Creation Lore (optional)",
            placeholder="Describe the legend behind your creation…",
            max_chars=280,
            height=80,
        )

        submitted = st.form_submit_button(
            "🌟 INSCRIBE ON THE GENESIS LAYER",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        if not creation_name.strip():
            st.error("Every great creation must bear a name, Young Sovereign.")
        else:
            with st.spinner("Inscribing your creation on the Genesis Layer…"):
                try:
                    aid       = generate_asset_id(creation_name, user)
                    file_path = ""

                    # Save uploaded file to disk
                    if uploaded_file is not None:
                        safe_fn = (
                            uploaded_file.name
                            .encode("ascii", "ignore").decode("ascii")
                            .replace(" ", "_")
                        )
                        dest = f"{CREATIONS_DIR}/{user}/{aid}_{safe_fn}"
                        with open(dest, "wb") as fh:
                            fh.write(uploaded_file.getbuffer())
                        file_path = dest

                    new_rec = {
                        "id":              aid,
                        "name":            creation_name.strip(),
                        "sovereign":       user,
                        "value":           int(imagined_val),
                        "emoji":           emoji_pick,
                        "file_path":       file_path,
                        "created_at":      datetime.now().isoformat(),
                        "is_fractional":   False,
                        "cert_downloaded": False,
                        "fraction_count":  100,
                    }

                    df_all = pd.concat(
                        [df_all, pd.DataFrame([new_rec])],
                        ignore_index=True
                    )
                    save_creations(df_all)
                    st.session_state["creations_df"] = df_all

                    # Run quest detection immediately
                    run_quest_checks(df_all, user)

                    st.balloons()
                    st.success(
                        f"✦ **{creation_name}** has been inscribed on the Genesis Layer!  \n"
                        f"Genesis ID: `{aid}`  \n"
                        f"Imagined Value: **{int(imagined_val):,} IMAGIX**"
                    )
                    if description.strip():
                        st.info(f"📜 Lore sealed: *\"{description.strip()[:120]}\"*")

                except Exception as e:
                    st.error(
                        f"Inscription failed: {e}  \n"
                        "Contact the Keeper of the Genesis Layer."
                    )


# ══════════════════════════════════════════════════════════════
# ⑪ SIDEBAR — GENESIS TERMINAL v0.7
# ══════════════════════════════════════════════════════════════
with st.sidebar:
    # Terminal header
    st.markdown(f"""
    <div style="text-align:center; padding:16px 0 8px;">
        <div style="font-family:'Cinzel',serif; color:{C['gold']};
             font-size:14px; font-weight:900; letter-spacing:3px;">
            ◈ GENESIS TERMINAL
        </div>
        <div style="font-family:'DM Mono',monospace; color:{C['teal']};
             font-size:8px; letter-spacing:2px; margin-top:4px; opacity:0.8;">
            v0.7 · SOVEREIGN INTERFACE
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # Sovereign stats
    stats = [
        ("YOUNG SOVEREIGN",  user),
        ("RANK",             rank["name"]),
        ("IMAGIX BALANCE",   f"{total_imagix:,} 𝕀"),
        ("CREATIONS",        str(len(user_df))),
        ("QUESTS DONE",      f"{n_quests_done} / {len(QUESTS)}"),
        ("LAYER",            "GENESIS v0.7"),
        ("SESSION",          datetime.now().strftime("%H:%M · %b %d, %Y")),
    ]

    for label, val in stats:
        st.markdown(f"""
        <div class="terminal-block">
            <div class="terminal-key">{label}</div>
            <div class="terminal-val">{val}</div>
        </div>
        """, unsafe_allow_html=True)

    # Rank progress
    st.divider()
    if not rank["maxed"]:
        st.progress(rank["progress"])
        st.caption(f"{rank['next'] - total_imagix:,} 𝕀 to {RANK_TIERS[RANK_TIERS.index(next(t for t in RANK_TIERS if t[1]==rank['name']))+1][1] if rank['name'] != RANK_TIERS[-1][1] else 'MAX'}")
    else:
        st.progress(1.0)
        st.caption("👑 LEGEND — Maximum rank achieved")

    st.divider()

    # ── PARENTAL / SPONSOR MODE ────────────────────────────
    st.markdown(f"""
    <div style="font-family:'Cinzel',serif; color:{C['muted']};
         font-size:9px; letter-spacing:2px; margin-bottom:6px;">
        PARENTAL / SPONSOR MODE
    </div>
    """, unsafe_allow_html=True)

    parent_on = st.toggle(
        "Enable Sponsor View",
        value=st.session_state["parent_mode"],
        key="parent_toggle",
        help="Simulates a parent/sponsor seeing the child's activity.",
    )
    st.session_state["parent_mode"] = parent_on

    if parent_on:
        st.markdown(f"""
        <div class="parent-mode">
            <div class="parent-mode-title">👁 SPONSOR VIEW ACTIVE</div>
        </div>
        """, unsafe_allow_html=True)

        total_val = sum(
            float(str(r.get("value",0)).replace(",","") or 0)
            for r in user_df.to_dict("records")
        ) if not user_df.empty else 0

        n_cert = int(
            user_df["cert_downloaded"].astype(str)
            .str.lower().isin(["true","1"]).sum()
        ) if not user_df.empty else 0

        n_frac = int(
            user_df["is_fractional"].astype(str)
            .str.lower().isin(["true","1"]).sum()
        ) if not user_df.empty else 0

        sponsor_stats = [
            ("Kingdom",       user),
            ("Rank",          rank["name"]),
            ("Total Creations", str(len(user_df))),
            ("Portfolio Value", f"{total_val:,.0f} 𝕀"),
            ("Certs Issued",  str(n_cert)),
            ("Fractionalized", str(n_frac)),
            ("IMAGIX Earned", f"{total_imagix:,} 𝕀"),
            ("Quests Done",   f"{n_quests_done}/{len(QUESTS)}"),
        ]
        for lbl, v in sponsor_stats:
            st.markdown(f"""
            <div style="display:flex; justify-content:space-between;
                 padding:4px 0; border-bottom:1px solid rgba(157,78,221,0.15);">
                <span style="font-family:'DM Mono',monospace;
                     color:{C['muted']}; font-size:9px;">{lbl}</span>
                <span style="font-family:'Cinzel',serif;
                     color:{C['gold']}; font-size:10px; font-weight:700;">{v}</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("")
        st.markdown(f"""
        <div style="font-family:'DM Mono',monospace; color:{C['teal']};
             font-size:9px; margin-top:8px; line-height:1.7; opacity:0.8;">
            ✦ All actions require Sovereign consent<br>
            ✦ Approval gates on trades coming v0.8<br>
            ✦ This view is read-only (mock)
        </div>
        """, unsafe_allow_html=True)

    st.divider()
    st.caption(
        "Delphia Genesis v0.7  \n"
        "Where Imagination Becomes Sovereign  \n"
        "© Rey Delphi · Reino de Delphia · Kardashev VI"
    )


# ══════════════════════════════════════════════════════════════
# ⑫ FOOTER
# ══════════════════════════════════════════════════════════════
st.divider()
st.caption(
    "⬟ Delphia Genesis v0.7 — Where Imagination Becomes Sovereign  ·  "
    "Genesis Layer powered by the Delphia Multiverse  ·  Kardashev Type VI ⬟"
)