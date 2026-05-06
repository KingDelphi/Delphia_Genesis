"""
╔══════════════════════════════════════════════════════════════╗
║           DELPHIA GENESIS v0.6 — THE IMAGINARIUM             ║
║     Where Imagination Becomes Sovereign on the Genesis Layer  ║
║                   Rey Delphi · Kardashev VI                  ║
╚══════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import pandas as pd
import os
import hashlib
import io
from datetime import datetime
from pathlib import Path

# ─── ReportLab imports (robust PDF generation) ───────────────
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate

# ─── Optional: Pillow for image thumbnails ───────────────────
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


# ══════════════════════════════════════════════════════════════
# CONSTANTS & PALETTE
# ══════════════════════════════════════════════════════════════
CELESTIAL_BLUE   = "#0A2540"
GENESIS_GOLD     = "#F2C94C"
NEBULA_TEAL      = "#00E5C0"
STELLAR_PURPLE   = "#9D4EDD"
DEEP_SPACE       = "#05121f"
CARD_BG          = "#112B4D"
WHITE            = "#FFFFFF"

DATA_FILE        = "genesis_creations.csv"
CREATIONS_DIR    = "creations"
QUESTS_FILE      = "genesis_quests.csv"

RANK_THRESHOLDS  = [
    (0,       "✦ SPARK I",    "spark"),
    (10_000,  "✦ SPARK II",   "spark"),
    (25_000,  "✦ SPARK III",  "spark"),
    (50_000,  "🔥 FLAME I",   "flame"),
    (100_000, "🔥 FLAME II",  "flame"),
    (175_000, "🔥 FLAME III", "flame"),
    (275_000, "⭐ STAR I",    "star"),
    (400_000, "⭐ STAR II",   "star"),
    (600_000, "⭐ STAR III",  "star"),
    (900_000, "👑 LEGEND",    "legend"),
]

QUESTS_CATALOG = [
    {"id": "q_create_first",  "title": "First Creation",       "desc": "Upload your very first creation to the Genesis Layer.", "reward": 5_000,  "icon": "🌱"},
    {"id": "q_create_three",  "title": "Trilogy of Wonders",   "desc": "Upload 3 different creations.",                         "reward": 12_000, "icon": "🎨"},
    {"id": "q_daily_upload",  "title": "Daily Genesis",         "desc": "Upload a creation today.",                              "reward": 2_500,  "icon": "☀️"},
    {"id": "q_cert_download", "title": "Sacred Title Claimed",  "desc": "Download your first Genesis Certificate.",             "reward": 3_000,  "icon": "📜"},
    {"id": "q_split_asset",   "title": "Fractional Sovereign",  "desc": "Activate Split on any creation.",                       "reward": 7_500,  "icon": "🔀"},
    {"id": "q_reach_50k",     "title": "Golden Threshold",      "desc": "Accumulate 50,000 IMAGIX.",                             "reward": 10_000, "icon": "💰"},
]


# ══════════════════════════════════════════════════════════════
# PAGE CONFIG (must be first Streamlit call)
# ══════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="DELPHIA GENESIS | IMAGINARIUM",
    page_icon="🌟",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ══════════════════════════════════════════════════════════════
# THEME — GENESIS VISUAL SYSTEM
# ══════════════════════════════════════════════════════════════
def apply_genesis_theme():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700;900&family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=DM+Mono:wght@400;500&display=swap');

    :root {{
        --celestial: {CELESTIAL_BLUE};
        --gold:       {GENESIS_GOLD};
        --teal:       {NEBULA_TEAL};
        --purple:     {STELLAR_PURPLE};
        --space:      {DEEP_SPACE};
        --card:       {CARD_BG};
    }}

    html, body, [data-testid="stAppViewContainer"] {{
        background-color: var(--space);
        color: var(--gold);
    }}
    .stApp {{
        background: radial-gradient(ellipse at 20% 20%, #0d2d4a 0%, var(--space) 60%),
                    radial-gradient(ellipse at 80% 80%, #0a1f35 0%, var(--space) 60%);
    }}

    /* ─── Typography ─── */
    h1, h2, h3 {{ font-family: 'Cinzel', serif !important; color: var(--gold) !important; }}
    p, span, div {{ font-family: 'DM Mono', monospace; }}

    /* ─── Buttons ─── */
    .stButton > button {{
        background: linear-gradient(135deg, var(--purple), #6b2fa0);
        color: var(--gold);
        border: 1px solid var(--gold);
        border-radius: 8px;
        font-family: 'Cinzel', serif;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 1px;
        padding: 8px 16px;
        transition: all 0.25s ease;
    }}
    .stButton > button:hover {{
        background: linear-gradient(135deg, var(--gold), #d4a017);
        color: var(--space);
        box-shadow: 0 0 20px rgba(242,201,76,0.5);
        transform: translateY(-2px);
    }}
    .stButton > button[kind="primary"] {{
        background: linear-gradient(135deg, var(--gold), #c8a000);
        color: var(--space);
        font-size: 13px;
        padding: 10px 24px;
    }}

    /* ─── Inputs ─── */
    .stTextInput input, .stSelectbox select {{
        background-color: #0d2540 !important;
        color: var(--teal) !important;
        border: 1px solid var(--purple) !important;
        border-radius: 6px;
        font-family: 'DM Mono', monospace;
    }}

    /* ─── Tabs ─── */
    .stTabs [data-baseweb="tab-list"] {{
        background: transparent;
        border-bottom: 1px solid var(--purple);
        gap: 4px;
    }}
    .stTabs [data-baseweb="tab"] {{
        font-family: 'Cinzel', serif;
        font-size: 12px;
        color: #8899aa;
        padding: 8px 16px;
        border-radius: 6px 6px 0 0;
        border: 1px solid transparent;
    }}
    .stTabs [aria-selected="true"] {{
        background: var(--card) !important;
        color: var(--gold) !important;
        border: 1px solid var(--teal) !important;
        border-bottom: none !important;
    }}

    /* ─── Metrics ─── */
    [data-testid="metric-container"] {{
        background: var(--card);
        border: 1px solid var(--purple);
        border-radius: 10px;
        padding: 10px 16px;
    }}
    [data-testid="metric-container"] label {{
        color: var(--teal) !important;
        font-family: 'Cinzel', serif;
        font-size: 10px;
    }}
    [data-testid="metric-container"] [data-testid="stMetricValue"] {{
        color: var(--gold) !important;
        font-family: 'Cinzel', serif;
    }}

    /* ─── Sidebar ─── */
    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, #0c1f38, var(--space));
        border-right: 1px solid var(--purple);
    }}
    [data-testid="stSidebar"] * {{ color: #ccd6f0 !important; }}

    /* ─── Progress bar ─── */
    .stProgress > div > div {{
        background: linear-gradient(90deg, var(--purple), var(--teal), var(--gold));
    }}

    /* ─── Cards ─── */
    .genesis-card {{
        background: var(--card);
        border: 1px solid var(--teal);
        border-radius: 14px;
        overflow: hidden;
        transition: all 0.3s ease;
        position: relative;
        margin-bottom: 12px;
    }}
    .genesis-card:hover {{
        border-color: var(--gold);
        box-shadow: 0 0 30px rgba(242,201,76,0.35), 0 8px 32px rgba(0,0,0,0.5);
        transform: translateY(-5px);
    }}
    .card-img-zone {{
        height: 140px;
        background: linear-gradient(135deg, #0a2540, #1b3a6b);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 64px;
        border-bottom: 1px solid rgba(0,229,192,0.2);
    }}
    .card-body {{
        padding: 10px 12px 12px;
    }}
    .card-title {{
        font-family: 'Playfair Display', serif;
        color: #eef2ff;
        font-size: 13px;
        font-weight: 700;
        margin-bottom: 4px;
        line-height: 1.3;
        min-height: 34px;
    }}
    .card-price {{
        font-family: 'Cinzel', serif;
        color: var(--gold);
        font-size: 15px;
        font-weight: 700;
    }}
    .card-id {{
        font-family: 'DM Mono', monospace;
        color: var(--teal);
        font-size: 9px;
        opacity: 0.7;
        margin-top: 2px;
    }}
    .card-badge {{
        position: absolute;
        top: 8px;
        right: 8px;
        background: rgba(10,37,64,0.85);
        border: 1px solid var(--gold);
        border-radius: 20px;
        padding: 2px 8px;
        font-family: 'Cinzel', serif;
        font-size: 8px;
        color: var(--gold);
    }}

    /* ─── Hero banner ─── */
    .genesis-hero {{
        background: linear-gradient(135deg, #0c1e36 0%, #1a2f50 50%, #0a1827 100%);
        border: 1px solid var(--purple);
        border-radius: 16px;
        padding: 24px 32px;
        margin-bottom: 20px;
        text-align: center;
        position: relative;
        overflow: hidden;
    }}
    .genesis-hero::before {{
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(ellipse, rgba(157,78,221,0.08) 0%, transparent 70%);
        pointer-events: none;
    }}
    .hero-title {{
        font-family: 'Cinzel', serif;
        font-size: 28px;
        font-weight: 900;
        color: var(--gold);
        letter-spacing: 4px;
        margin: 0;
    }}
    .hero-sub {{
        font-family: 'DM Mono', monospace;
        color: var(--teal);
        font-size: 12px;
        letter-spacing: 2px;
        margin-top: 6px;
    }}

    /* ─── Quest cards ─── */
    .quest-card {{
        background: var(--card);
        border: 1px solid var(--purple);
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 16px;
        transition: all 0.2s;
    }}
    .quest-card.completed {{
        border-color: var(--teal);
        background: rgba(0,229,192,0.05);
        opacity: 0.75;
    }}
    .quest-icon {{ font-size: 28px; min-width: 36px; text-align: center; }}
    .quest-info {{ flex: 1; }}
    .quest-name {{
        font-family: 'Cinzel', serif;
        color: var(--gold);
        font-size: 13px;
        font-weight: 700;
    }}
    .quest-desc {{ font-family: 'DM Mono', monospace; color: #8899aa; font-size: 11px; margin-top: 2px; }}
    .quest-reward {{ font-family: 'Cinzel', serif; color: var(--teal); font-size: 13px; font-weight: 700; white-space: nowrap; }}

    /* ─── Rank badge ─── */
    .rank-display {{
        background: linear-gradient(135deg, var(--card), #1a3060);
        border: 2px solid var(--gold);
        border-radius: 50px;
        padding: 6px 20px;
        display: inline-block;
        font-family: 'Cinzel', serif;
        color: var(--gold);
        font-size: 14px;
        font-weight: 700;
        letter-spacing: 2px;
        box-shadow: 0 0 20px rgba(242,201,76,0.2);
    }}

    /* ─── Divider ─── */
    hr {{ border-color: rgba(157,78,221,0.3) !important; }}

    /* ─── Alerts ─── */
    .stSuccess, .stInfo, .stWarning {{
        border-radius: 10px;
        font-family: 'DM Mono', monospace;
    }}

    /* ─── File uploader ─── */
    [data-testid="stFileUploader"] {{
        background: var(--card);
        border: 2px dashed var(--purple);
        border-radius: 12px;
        padding: 20px;
    }}

    /* ─── Scrollbar ─── */
    ::-webkit-scrollbar {{ width: 6px; }}
    ::-webkit-scrollbar-track {{ background: var(--space); }}
    ::-webkit-scrollbar-thumb {{ background: var(--purple); border-radius: 3px; }}
    </style>
    """, unsafe_allow_html=True)

apply_genesis_theme()


# ══════════════════════════════════════════════════════════════
# DATA LAYER — CSV persistence
# ══════════════════════════════════════════════════════════════

def ensure_dirs(user: str):
    """Ensure all required directories exist."""
    Path(CREATIONS_DIR).mkdir(exist_ok=True)
    Path(f"{CREATIONS_DIR}/{user}").mkdir(parents=True, exist_ok=True)


def load_creations() -> pd.DataFrame:
    """Load or initialize the creations DataFrame."""
    cols = ["id", "name", "sovereign", "value", "emoji", "file_path",
            "created_at", "splits_enabled", "cert_downloaded"]
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE)
            for c in cols:
                if c not in df.columns:
                    df[c] = "" if c in ("file_path", "emoji") else 0
            return df
        except Exception:
            pass
    return pd.DataFrame(columns=cols)


def save_creations(df: pd.DataFrame):
    """Persist creations DataFrame."""
    df.to_csv(DATA_FILE, index=False)


def load_quests(user: str) -> dict:
    """Load quest completion state for a user."""
    if os.path.exists(QUESTS_FILE):
        try:
            df = pd.read_csv(QUESTS_FILE)
            row = df[df["sovereign"] == user]
            if not row.empty:
                completed = str(row.iloc[0]["completed_ids"])
                return set(completed.split(",")) if completed.strip() else set()
        except Exception:
            pass
    return set()


def save_quests(user: str, completed: set):
    """Persist quest completion for a user."""
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
    raw = f"{name}-{sovereign}-{datetime.now().isoformat()}"
    return "GEN-" + hashlib.sha256(raw.encode()).hexdigest()[:8].upper()


# ══════════════════════════════════════════════════════════════
# RANK ENGINE
# ══════════════════════════════════════════════════════════════

def get_rank_info(imagix: int) -> dict:
    rank_name = RANK_THRESHOLDS[0][1]
    current_threshold = 0
    next_threshold = RANK_THRESHOLDS[1][0]

    for i, (threshold, name, tier) in enumerate(RANK_THRESHOLDS):
        if imagix >= threshold:
            rank_name = name
            current_threshold = threshold
            if i + 1 < len(RANK_THRESHOLDS):
                next_threshold = RANK_THRESHOLDS[i + 1][0]
            else:
                next_threshold = current_threshold  # Legend — maxed

    progress = 0.0
    span = next_threshold - current_threshold
    if span > 0:
        progress = min((imagix - current_threshold) / span, 1.0)
    else:
        progress = 1.0

    return {
        "rank": rank_name,
        "progress": progress,
        "current_threshold": current_threshold,
        "next_threshold": next_threshold,
    }


# ══════════════════════════════════════════════════════════════
# PDF CERTIFICATE — ReportLab (robust, unicode-safe)
# ══════════════════════════════════════════════════════════════

def create_genesis_certificate(asset_name: str, asset_id: str,
                                sovereign: str, value: int) -> bytes:
    """
    Generate a beautiful Genesis Certificate PDF using ReportLab.
    Returns raw PDF bytes — safe for st.download_button.
    """
    buf = io.BytesIO()
    W, H = A4  # 595 x 842 pts

    c = canvas.Canvas(buf, pagesize=A4)
    c.setTitle(f"Genesis Certificate — {asset_name}")

    # ── Background ──────────────────────────────────────────
    c.setFillColor(HexColor("#05121f"))
    c.rect(0, 0, W, H, fill=1, stroke=0)

    # Radial glow (simulated with layered translucent circles)
    for r, alpha in [(260, 0.04), (200, 0.06), (130, 0.09), (70, 0.06)]:
        c.setFillColorRGB(0.38, 0.31, 0.87, alpha=alpha)
        c.circle(W / 2, H / 2, r, fill=1, stroke=0)

    # ── Outer border ────────────────────────────────────────
    c.setStrokeColor(HexColor(GENESIS_GOLD))
    c.setLineWidth(2.5)
    c.roundRect(18, 18, W - 36, H - 36, 14, fill=0, stroke=1)

    # Inner border
    c.setStrokeColor(HexColor(STELLAR_PURPLE))
    c.setLineWidth(0.8)
    c.roundRect(26, 26, W - 52, H - 52, 10, fill=0, stroke=1)

    # ── Corner ornaments ────────────────────────────────────
    for ox, oy in [(28, 28), (W - 28, 28), (28, H - 28), (W - 28, H - 28)]:
        c.setStrokeColor(HexColor(GENESIS_GOLD))
        c.setLineWidth(1.2)
        c.circle(ox, oy, 6, fill=0, stroke=1)
        c.setFillColor(HexColor(GENESIS_GOLD))
        c.circle(ox, oy, 2.5, fill=1, stroke=0)

    # ── Top header band ─────────────────────────────────────
    c.setFillColor(HexColor("#0c1e36"))
    c.roundRect(30, H - 110, W - 60, 80, 8, fill=1, stroke=0)

    c.setFillColor(HexColor(GENESIS_GOLD))
    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(W / 2, H - 68, "DELPHIA GENESIS")

    c.setFillColor(HexColor(NEBULA_TEAL))
    c.setFont("Helvetica", 10)
    c.drawCentredString(W / 2, H - 90, "CERTIFICATE  OF  IMAGINATION  ·  GENESIS LAYER")

    # ── Central star ────────────────────────────────────────
    # Draw a custom 5-point star
    import math

    def draw_star(cx, cy, r_outer, r_inner, points=5):
        path = c.beginPath()
        for i in range(points * 2):
            angle = math.pi / points * i - math.pi / 2
            r = r_outer if i % 2 == 0 else r_inner
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            if i == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)
        path.close()
        c.drawPath(path, fill=1, stroke=1)

    star_y = H - 195
    # Glow
    c.setFillColorRGB(0.95, 0.79, 0.30, alpha=0.12)
    c.setStrokeColor(HexColor(GENESIS_GOLD))
    c.circle(W / 2, star_y, 52, fill=1, stroke=0)

    c.setFillColor(HexColor(GENESIS_GOLD))
    c.setStrokeColor(HexColor(STELLAR_PURPLE))
    c.setLineWidth(1.5)
    draw_star(W / 2, star_y, 38, 16)

    # ── Decorative horizontal rule ───────────────────────────
    rule_y = H - 240
    c.setStrokeColor(HexColor(STELLAR_PURPLE))
    c.setLineWidth(0.6)
    c.line(50, rule_y, W - 50, rule_y)
    c.setStrokeColor(HexColor(GENESIS_GOLD))
    c.setLineWidth(0.4)
    c.line(60, rule_y - 4, W - 60, rule_y - 4)

    # ── Fields ──────────────────────────────────────────────
    def draw_field(label: str, value: str, y: float):
        # Label
        c.setFillColor(HexColor(NEBULA_TEAL))
        c.setFont("Helvetica", 8)
        c.drawCentredString(W / 2, y + 16, label.upper())
        # Underline
        c.setStrokeColor(HexColor(STELLAR_PURPLE))
        c.setLineWidth(0.4)
        c.line(80, y + 12, W - 80, y + 12)
        # Value
        c.setFillColor(HexColor(WHITE))
        c.setFont("Helvetica-Bold", 14)
        # Truncate long strings
        display_val = value if len(value) <= 48 else value[:45] + "…"
        c.drawCentredString(W / 2, y, display_val)

    fields = [
        ("CREATION",        str(asset_name)[:60]),
        ("GENESIS ID",      str(asset_id)),
        ("YOUNG SOVEREIGN", str(sovereign)[:40]),
        ("IMAGINED VALUE",  f"{int(value):,} IMAGIX"),
        ("DATE SEALED",     datetime.now().strftime("%B %Y").upper()),
        ("STATUS",          "SACRED & IMMUTABLE"),
    ]

    field_start_y = H - 285
    field_gap     = 52

    for i, (label, val) in enumerate(fields):
        draw_field(label, val, field_start_y - i * field_gap)

    # ── Bottom ornamental line ───────────────────────────────
    bottom_y = field_start_y - len(fields) * field_gap + 10
    c.setStrokeColor(HexColor(GENESIS_GOLD))
    c.setLineWidth(0.6)
    c.line(50, bottom_y, W - 50, bottom_y)
    c.setStrokeColor(HexColor(STELLAR_PURPLE))
    c.setLineWidth(0.4)
    c.line(60, bottom_y - 4, W - 60, bottom_y - 4)

    # ── Signature area ──────────────────────────────────────
    sig_y = bottom_y - 55
    c.setFillColor(HexColor(STELLAR_PURPLE))
    c.setFont("Helvetica", 8)
    c.drawCentredString(W / 2, sig_y + 20, "— Signed by the Keeper of the Genesis Layer —")

    c.setFillColor(HexColor(GENESIS_GOLD))
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(W / 2, sig_y, "REY DELPHI · REINO DE DELPHIA · KARDASHEV VI")

    # ── Footer ──────────────────────────────────────────────
    c.setFillColor(HexColor(NEBULA_TEAL))
    c.setFont("Helvetica", 7.5)
    c.drawCentredString(W / 2, 35, "Delphia Genesis v0.6  ·  Where Imagination Becomes Sovereign  ·  delphia.genesis")

    c.save()
    return buf.getvalue()


# ══════════════════════════════════════════════════════════════
# SESSION STATE INIT
# ══════════════════════════════════════════════════════════════

def init_session():
    defaults = {
        "authenticated": False,
        "user": "",
        "imagix": 0,
        "quest_completed": set(),
        "creations_df": None,
        "show_split_info": {},
        "cert_triggered": {},
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session()


# ══════════════════════════════════════════════════════════════
# QUEST ENGINE
# ══════════════════════════════════════════════════════════════

def check_and_award_quest(quest_id: str, user: str):
    """Award a quest if not already completed. Returns reward amount or 0."""
    if quest_id not in st.session_state["quest_completed"]:
        st.session_state["quest_completed"].add(quest_id)
        save_quests(user, st.session_state["quest_completed"])
        reward = next((q["reward"] for q in QUESTS_CATALOG if q["id"] == quest_id), 0)
        st.session_state["imagix"] += reward
        if reward:
            st.toast(f"⚡ QUEST COMPLETE! +{reward:,} IMAGIX awarded!", icon="🏆")
        return reward
    return 0

def imagix_from_quests(completed: set) -> int:
    return sum(q["reward"] for q in QUESTS_CATALOG if q["id"] in completed)


# ══════════════════════════════════════════════════════════════
# LOGIN GATE
# ══════════════════════════════════════════════════════════════

if not st.session_state["authenticated"]:
    st.markdown("""
    <div class="genesis-hero" style="margin-top:60px; padding:48px;">
        <div class="hero-title">⬟ DELPHIA GENESIS ⬟</div>
        <div class="hero-sub">THE IMAGINARIUM · GENESIS LAYER v0.6</div>
    </div>
    """, unsafe_allow_html=True)

    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        st.markdown("### 🌟 Enter the Genesis Layer")
        kingdom_name = st.text_input("Kingdom Name", placeholder="e.g. Astra Nova",
                                      key="login_input", label_visibility="visible")
        st.caption("Your sovereign identity within the Delphia Multiverse.")

        if st.button("✦ ENTER THE IMAGINARIUM", type="primary", use_container_width=True):
            if kingdom_name.strip():
                st.session_state["authenticated"] = True
                st.session_state["user"] = kingdom_name.strip()
                # Load quests
                completed = load_quests(kingdom_name.strip())
                st.session_state["quest_completed"] = completed
                st.session_state["imagix"] = imagix_from_quests(completed)
                st.rerun()
            else:
                st.warning("Your kingdom must have a name, Young Sovereign.")
    st.stop()


# ══════════════════════════════════════════════════════════════
# MAIN APP — authenticated
# ══════════════════════════════════════════════════════════════

user = st.session_state["user"]
ensure_dirs(user)

# Load (or refresh) creations
if st.session_state["creations_df"] is None:
    st.session_state["creations_df"] = load_creations()

df_all: pd.DataFrame = st.session_state["creations_df"]
user_df = df_all[df_all["sovereign"] == user].copy()

# Compute IMAGIX & rank
total_imagix = st.session_state["imagix"]
rank_info = get_rank_info(total_imagix)


# ── HEADER ────────────────────────────────────────────────────
hc = st.columns([4, 1, 1, 1, 1])
hc[0].markdown(f"""
<div style="font-family:'Cinzel',serif; font-size:18px; color:{GENESIS_GOLD}; padding-top:8px;">
    🌟 {user} &nbsp;·&nbsp; <span style="color:{NEBULA_TEAL};">{rank_info['rank']}</span>
</div>
""", unsafe_allow_html=True)

hc[1].metric("IMAGIX", f"{total_imagix:,} 𝕀")
hc[2].metric("CREATIONS", len(user_df))
hc[3].metric("QUESTS DONE", len(st.session_state["quest_completed"]))
if hc[4].button("✦ LOGOUT"):
    for k in ["authenticated", "user", "imagix", "quest_completed",
              "creations_df", "show_split_info", "cert_triggered"]:
        del st.session_state[k]
    st.rerun()

# Rank progress bar
prog_col, _ = st.columns([3, 1])
with prog_col:
    next_t = rank_info["next_threshold"]
    curr_t = rank_info["current_threshold"]
    if next_t > curr_t:
        st.progress(rank_info["progress"],
                    text=f"Progress to next rank · {total_imagix:,} / {next_t:,} IMAGIX")
    else:
        st.progress(1.0, text="👑 LEGEND — Supreme Sovereign of the Genesis Layer")

st.divider()


# ══════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════

tab_vault, tab_quests, tab_market, tab_upload = st.tabs([
    "🌌 MY CREATIONS VAULT",
    "⚔️ QUESTS & PROGRESS",
    "🌠 MARKETPLACE",
    "🌱 UPLOAD CREATION",
])


# ────────────────────────────────────────────────────────────
# TAB 1 — VAULT
# ────────────────────────────────────────────────────────────
with tab_vault:
    st.markdown(f"### 🌌 SOVEREIGN CREATIONS VAULT")
    st.caption(f"{len(user_df)} creation(s) registered on the Genesis Layer")

    # Seed demo data if user has none
    if user_df.empty:
        st.info("🌠 Your vault is empty. Upload your first creation to begin your Genesis journey!")
        demo_examples = [
            ("Star Dragon Awakening",      48_200, "🐉"),
            ("Kingdom of Eternal Clouds", 125_000, "☁️"),
            ("The Brave Robot Friend",     32_800, "🤖"),
            ("Legendary Enchanted Sword",  67_500, "⚔️"),
            ("My Family's Floating Castle",89_000, "🏰"),
        ]
        st.markdown("#### ✦ Genesis Showcase — Creations from the Multiverse")
        cols = st.columns(5)
        for i, (name, value, emoji) in enumerate(demo_examples):
            with cols[i]:
                st.markdown(f"""
                <div class="genesis-card">
                    <div class="card-img-zone">{emoji}</div>
                    <div class="card-body">
                        <div class="card-badge">SHOWCASE</div>
                        <div class="card-title">{name}</div>
                        <div class="card-price">{value:,} 𝕀</div>
                        <div class="card-id">DEMO ONLY</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        # Render user's real creations in rows of 4
        records = user_df.to_dict("records")
        for row_start in range(0, len(records), 4):
            row_records = records[row_start:row_start + 4]
            cols = st.columns(4)
            for col_idx, record in enumerate(row_records):
                with cols[col_idx]:
                    emoji = record.get("emoji") or "🌟"
                    name  = str(record.get("name", "Unknown"))
                    value = int(record.get("value", 0))
                    asset_id = str(record.get("id", ""))

                    # Check for uploaded image thumbnail
                    fp = str(record.get("file_path", ""))
                    has_image = (fp and os.path.exists(fp) and
                                 fp.lower().endswith((".jpg", ".jpeg", ".png")))

                    if has_image and PIL_AVAILABLE:
                        try:
                            img = Image.open(fp)
                            st.image(img, use_container_width=True)
                        except Exception:
                            st.markdown(f"""<div class="card-img-zone">{emoji}</div>""",
                                        unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div class="genesis-card">
                            <div class="card-img-zone">{emoji}</div>
                            <div class="card-body">
                                <div class="card-title">{name}</div>
                                <div class="card-price">{value:,} 𝕀</div>
                                <div class="card-id">{asset_id}</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                    bt_col1, bt_col2 = st.columns(2)

                    # ── TITLE button → generate certificate ──
                    with bt_col1:
                        if st.button("📜 TITLE", key=f"title_{asset_id}"):
                            st.session_state["cert_triggered"][asset_id] = True
                            check_and_award_quest("q_cert_download", user)

                    if st.session_state["cert_triggered"].get(asset_id):
                        try:
                            pdf_bytes = create_genesis_certificate(
                                name, asset_id, user, value)
                            safe_name = name.replace(" ", "_")[:30]
                            st.download_button(
                                label="⬇️ Download Certificate",
                                data=pdf_bytes,
                                file_name=f"{safe_name}_Genesis_Certificate.pdf",
                                mime="application/pdf",
                                key=f"dl_{asset_id}",
                                use_container_width=True,
                            )
                            # Mark cert_downloaded in CSV
                            df_all.loc[df_all["id"] == asset_id,
                                        "cert_downloaded"] = True
                            save_creations(df_all)
                        except Exception as e:
                            st.error(f"Certificate generation failed: {e}")

                    # ── SPLIT button ──────────────────────────
                    with bt_col2:
                        if st.button("🔀 SPLIT", key=f"split_{asset_id}"):
                            st.session_state["show_split_info"][asset_id] = (
                                not st.session_state["show_split_info"].get(asset_id, False)
                            )
                            # Update DB
                            df_all.loc[df_all["id"] == asset_id,
                                        "splits_enabled"] = True
                            save_creations(df_all)
                            check_and_award_quest("q_split_asset", user)

                    if st.session_state["show_split_info"].get(asset_id):
                        fractions = 100
                        frac_val = value / fractions
                        st.success(
                            f"✦ **{name}** split into **{fractions} fractions**  \n"
                            f"Each fraction: **{frac_val:,.0f} 𝕀**  \n"
                            f"Status: FRACTIONAL OWNERSHIP ENABLED"
                        )


# ────────────────────────────────────────────────────────────
# TAB 2 — QUESTS & PROGRESS
# ────────────────────────────────────────────────────────────
with tab_quests:
    st.markdown("### ⚔️ QUESTS & PROGRESS")

    # Rank roadmap
    rank_col1, rank_col2 = st.columns([2, 1])
    with rank_col1:
        st.markdown(f"""
        <div style="margin-bottom:16px;">
            <span style="font-family:'Cinzel',serif; color:{GENESIS_GOLD}; font-size:13px;">
                CURRENT RANK
            </span><br>
            <div class="rank-display">{rank_info['rank']}</div>
        </div>
        """, unsafe_allow_html=True)

        if rank_info["next_threshold"] > rank_info["current_threshold"]:
            needed = rank_info["next_threshold"] - total_imagix
            st.progress(rank_info["progress"],
                        text=f"{needed:,} IMAGIX needed to advance")
        else:
            st.progress(1.0, text="👑 Maximum rank achieved — you are LEGEND")

    with rank_col2:
        st.markdown(f"""
        <div style="background:{CARD_BG}; border:1px solid {STELLAR_PURPLE};
             border-radius:12px; padding:16px; text-align:center;">
            <div style="font-family:'DM Mono',monospace; color:{NEBULA_TEAL}; font-size:10px;">
                RANK TIERS
            </div>
            <div style="font-family:'Cinzel',serif; color:#8899aa; font-size:10px; margin-top:8px; line-height:2;">
                ✦ SPARK I–III · 0–25k<br>
                🔥 FLAME I–III · 50k–175k<br>
                ⭐ STAR I–III · 275k–600k<br>
                👑 LEGEND · 900k+
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()
    st.markdown("#### Active Quests")

    for q in QUESTS_CATALOG:
        completed_flag = q["id"] in st.session_state["quest_completed"]
        css_class = "quest-card completed" if completed_flag else "quest-card"
        check = "✅" if completed_flag else "○"
        st.markdown(f"""
        <div class="{css_class}">
            <div class="quest-icon">{q['icon']}</div>
            <div class="quest-info">
                <div class="quest-name">{check} {q['title']}</div>
                <div class="quest-desc">{q['desc']}</div>
            </div>
            <div class="quest-reward">+{q['reward']:,} 𝕀</div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()
    st.markdown(f"""
    **Total IMAGIX earned from quests:** `{total_imagix:,} 𝕀`  
    **Quests completed:** `{len(st.session_state['quest_completed'])} / {len(QUESTS_CATALOG)}`
    """)


# ────────────────────────────────────────────────────────────
# TAB 3 — MARKETPLACE
# ────────────────────────────────────────────────────────────
with tab_market:
    st.markdown("### 🌠 GENESIS MARKETPLACE")
    st.markdown(f"""
    <div style="background:{CARD_BG}; border:1px solid {GENESIS_GOLD};
         border-radius:14px; padding:32px; text-align:center;">
        <div style="font-size:56px; margin-bottom:16px;">🌠</div>
        <div style="font-family:'Cinzel',serif; color:{GENESIS_GOLD}; font-size:20px; font-weight:700;">
            GENESIS MARKETPLACE
        </div>
        <div style="font-family:'DM Mono',monospace; color:{NEBULA_TEAL}; font-size:12px; margin-top:12px;">
            Secure Sovereign Trading · Coming in v0.7
        </div>
        <div style="font-family:'DM Mono',monospace; color:#8899aa; font-size:11px; margin-top:16px; line-height:1.8;">
            ✦ List your creations for safe trading<br>
            ✦ Fractional ownership exchange<br>
            ✦ IMAGIX escrow system<br>
            ✦ Sovereign-to-Sovereign auctions
        </div>
    </div>
    """, unsafe_allow_html=True)


# ────────────────────────────────────────────────────────────
# TAB 4 — UPLOAD CREATION
# ────────────────────────────────────────────────────────────
with tab_upload:
    st.markdown("### 🌱 REGISTER YOUR CREATION")
    st.caption("Upload your art, story, or craft to the Genesis Layer.")

    with st.form("upload_form", clear_on_submit=True):
        creation_name = st.text_input(
            "Creation Name ✦",
            placeholder="e.g. The Adventures of Luna the Fox")

        col_e, col_v = st.columns(2)
        with col_e:
            emoji_choice = st.selectbox(
                "Creation Emblem",
                ["🌟", "🐉", "☁️", "🤖", "⚔️", "🏰", "🌙", "🔮", "🦋",
                 "🌊", "🦅", "🌸", "💎", "🔥", "⚡", "🎨", "🎭", "🏆"])
        with col_v:
            imagined_value = st.number_input(
                "Imagined Value (IMAGIX)",
                min_value=100, max_value=10_000_000, value=10_000, step=500)

        uploaded_file = st.file_uploader(
            "Upload your creation file (image or PDF)",
            type=["jpg", "jpeg", "png", "pdf"],
            help="Images will display as your creation thumbnail.")

        submitted = st.form_submit_button("🌟 REGISTER IN GENESIS", type="primary",
                                           use_container_width=True)

    if submitted:
        if not creation_name.strip():
            st.error("Every great creation must have a name, Young Sovereign.")
        else:
            with st.spinner("Inscribing your creation on the Genesis Layer..."):
                try:
                    asset_id  = generate_asset_id(creation_name, user)
                    file_path = ""

                    # Save uploaded file
                    if uploaded_file:
                        safe_fn = (uploaded_file.name
                                   .encode("ascii", "ignore")
                                   .decode("ascii")
                                   .replace(" ", "_"))
                        dest = f"{CREATIONS_DIR}/{user}/{asset_id}_{safe_fn}"
                        with open(dest, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        file_path = dest

                    # Build new record
                    new_row = {
                        "id":             asset_id,
                        "name":           creation_name.strip(),
                        "sovereign":      user,
                        "value":          int(imagined_value),
                        "emoji":          emoji_choice,
                        "file_path":      file_path,
                        "created_at":     datetime.now().isoformat(),
                        "splits_enabled": False,
                        "cert_downloaded": False,
                    }

                    # Append and persist
                    df_all = pd.concat(
                        [df_all, pd.DataFrame([new_row])],
                        ignore_index=True)
                    save_creations(df_all)
                    st.session_state["creations_df"] = df_all

                    # Check quests
                    user_count = len(df_all[df_all["sovereign"] == user])
                    check_and_award_quest("q_create_first", user)
                    if user_count >= 3:
                        check_and_award_quest("q_create_three", user)
                    check_and_award_quest("q_daily_upload", user)
                    if st.session_state["imagix"] >= 50_000:
                        check_and_award_quest("q_reach_50k", user)

                    st.balloons()
                    st.success(
                        f"✦ **{creation_name}** has been inscribed on the Genesis Layer!  \n"
                        f"Genesis ID: `{asset_id}`  \n"
                        f"Imagined Value: **{int(imagined_value):,} IMAGIX**"
                    )

                except Exception as e:
                    st.error(f"Genesis inscription failed: {e}  \n"
                             f"Contact the Keeper of the Genesis Layer.")


# ══════════════════════════════════════════════════════════════
# SIDEBAR — GENESIS TERMINAL
# ══════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(f"""
    <div style="text-align:center; padding:12px 0;">
        <div style="font-family:'Cinzel',serif; color:{GENESIS_GOLD};
             font-size:16px; font-weight:900; letter-spacing:2px;">
            ◈ GENESIS TERMINAL
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    sidebar_fields = [
        ("YOUNG SOVEREIGN", user),
        ("RANK",            rank_info["rank"]),
        ("IMAGIX",          f"{total_imagix:,} 𝕀"),
        ("CREATIONS",       str(len(user_df))),
        ("QUESTS DONE",     f"{len(st.session_state['quest_completed'])} / {len(QUESTS_CATALOG)}"),
        ("LAYER",           "GENESIS v0.6"),
        ("SESSION",         datetime.now().strftime("%H:%M · %b %d")),
    ]

    for label, val in sidebar_fields:
        st.markdown(f"""
        <div style="margin-bottom:10px;">
            <div style="font-size:9px; color:{NEBULA_TEAL}; font-family:'DM Mono',monospace;
                 letter-spacing:1px;">{label}</div>
            <div style="font-size:13px; color:{GENESIS_GOLD}; font-family:'Cinzel',serif;
                 font-weight:700;">{val}</div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # Quick rank progress in sidebar
    if rank_info["next_threshold"] > rank_info["current_threshold"]:
        st.progress(rank_info["progress"])
        needed = rank_info["next_threshold"] - total_imagix
        st.caption(f"{needed:,} IMAGIX to next rank")

    st.divider()
    st.caption("Delphia Genesis v0.6  \nWhere Imagination Becomes Sovereign  \n© Rey Delphi · Kardashev VI")


# ══════════════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════════════
st.divider()
st.caption(
    "⬟ Delphia Genesis v0.6 — Where Imagination Becomes Sovereign · "
    "Genesis Layer powered by the Delphia Multiverse · Kardashev Type VI ⬟"
)