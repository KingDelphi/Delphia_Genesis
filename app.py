"""
╔══════════════════════════════════════════════════════════════════╗
║           DELPHIA GENESIS v0.8 — THE GRAND COVENANT             ║
║       Where Imagination Becomes Sovereign on the Genesis Layer    ║
║   Tutores LLM · Password System · Marketplace · Sponsor Gates    ║
║                     Rey Delphi · Kardashev VI                    ║
╚══════════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import pandas as pd
import os, hashlib, io, math, base64, json, random, re
from datetime import datetime, date
from pathlib import Path

# ─── ReportLab ───────────────────────────────────────────────
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.colors import HexColor

# ─── Pillow ──────────────────────────────────────────────────
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


# ══════════════════════════════════════════════════════════════
# ① DESIGN TOKENS
# ══════════════════════════════════════════════════════════════
C = {
    "space":   "#05121f",
    "celest":  "#0A2540",
    "card":    "#0e2240",
    "card2":   "#112B4D",
    "gold":    "#F2C94C",
    "gold2":   "#c8a000",
    "teal":    "#00E5C0",
    "purple":  "#9D4EDD",
    "purple2": "#6b2fa0",
    "white":   "#FFFFFF",
    "muted":   "#8899aa",
    "danger":  "#FF6B6B",
    "green":   "#2ECC71",
}

# ── File paths ────────────────────────────────────────────────
F = {
    "creations": "genesis_creations.csv",
    "quests":    "genesis_quests.csv",
    "wallets":   "genesis_wallets.csv",
    "users":     "genesis_users.csv",
    "market":    "genesis_market.csv",
    "dir":       "creations",
}

# ── Rank tiers ────────────────────────────────────────────────
RANK_TIERS = [
    (0,        "✦ SPARK I",   "spark"),
    (10_000,   "✦ SPARK II",  "spark"),
    (25_000,   "✦ SPARK III", "spark"),
    (50_000,   "🔥 FLAME I",  "flame"),
    (100_000,  "🔥 FLAME II", "flame"),
    (175_000,  "🔥 FLAME III","flame"),
    (275_000,  "⭐ STAR I",   "star"),
    (400_000,  "⭐ STAR II",  "star"),
    (600_000,  "⭐ STAR III", "star"),
    (900_000,  "👑 LEGEND",   "legend"),
]

# ── Tutors definition ─────────────────────────────────────────
TUTORS = [
    {
        "id": "delphito_bebito",
        "name": "Delphito el Bebito",
        "emoji": "🍼",
        "age_min": 6, "age_max": 9,
        "color": "#FFD1DC",
        "persona": (
            "Eres Delphito el Bebito, tutor de niños de 6-8 años en Delphia Genesis. "
            "Hablas de forma MUY simple, alegre y motivadora. Usas palabras fáciles, "
            "muchos emojis 🌟✨🎉, frases cortas y celebras todo con entusiasmo. "
            "Nunca usas palabras difíciles. Siempre dices cosas como '¡Qué chido!', "
            "'¡Lo lograste!', '¡Eres el mejor!'. Máximo 3 oraciones por respuesta."
        ),
    },
    {
        "id": "delphita_pinga",
        "name": "Delphita la Pinga",
        "emoji": "🏃‍♀️",
        "age_min": 8, "age_max": 12,
        "color": "#C8F7C5",
        "persona": (
            "Eres Delphita la Pinga, tutora traviesa y energética para niños de 8-10 años. "
            "Eres juguetona, divertida, usas lenguaje informal amigable. Haces bromas suaves, "
            "te emocionas mucho, usas onomatopeyas como '¡Boom!', '¡Wooow!', '¡Épico!'. "
            "Motivas con retos y competencia sana. Máximo 4 oraciones."
        ),
    },
    {
        "id": "chispitas",
        "name": "Chispitas",
        "emoji": "⚡",
        "age_min": 10, "age_max": 14,
        "color": "#FFF3CD",
        "persona": (
            "Eres Chispitas, tutora curiosa y científica para niños de 9-12 años. "
            "Explicas cosas con analogías creativas y preguntas inteligentes. "
            "Dices '¿Sabías que...?', '¡Interesante!', 'Imagina si...'. "
            "Conectas todo con conceptos del mundo real. Eres entusiasta de la ciencia y tecnología. "
            "Máximo 4 oraciones."
        ),
    },
    {
        "id": "delphito_bonito",
        "name": "Delphito el Bonito",
        "emoji": "😎",
        "age_min": 13, "age_max": 16,
        "color": "#D0E8FF",
        "persona": (
            "Eres Delphito el Bonito, tutor cool y estético para adolescentes de 12-14 años. "
            "Hablas con estilo, usas referencias a tendencias, eres motivador pero chill. "
            "Dices cosas como 'No cap', 'Literal fire 🔥', 'Vibe check', 'Main character energy'. "
            "Valoras la creatividad y el estilo personal. Máximo 4 oraciones."
        ),
    },
    {
        "id": "emperatriz_fenix",
        "name": "Delphina la Emperatriz Fénix",
        "emoji": "🦅",
        "age_min": 15, "age_max": 18,
        "color": "#E8D5FF",
        "persona": (
            "Eres Delphina la Emperatriz Fénix, tutora elegante y sabia para jóvenes de 14-16 años. "
            "Hablas con autoridad suave, usas metáforas poderosas, inspiras grandeza. "
            "Referencias a historia, arte y liderazgo. Dices 'Tu legado se forja hoy', "
            "'Los grandes soberanos actúan cuando otros dudan'. Sofisticada pero cercana. Máximo 5 oraciones."
        ),
    },
    {
        "id": "rey_delphi",
        "name": "Delphi, Rey de Delphia",
        "emoji": "👑",
        "age_min": 17, "age_max": 120,
        "color": "#F2C94C",
        "persona": (
            "Eres Delphi, Rey de Delphia, mentor supremo para jóvenes adultos de 16+ años. "
            "Hablas con profundidad filosófica, visión estratégica y sabiduría ancestral. "
            "Referencias a Kardashev, civilizaciones avanzadas, economía creativa, soberanía digital. "
            "Inspiras con grandeza cósmica pero con consejos prácticos y accionables. Máximo 5 oraciones."
        ),
    },
]

# ── Quests catalog ────────────────────────────────────────────
QUESTS = [
    # ── Onboarding
    {"id":"q_registered",     "title":"Sovereign Born",        "desc":"Enter the Genesis Layer for the first time.",             "reward":1_000,  "icon":"🌅","cat":"Onboarding",
     "check": lambda df,u,ss: True},
    {"id":"q_first_creation", "title":"First Genesis",         "desc":"Register your first creation.",                           "reward":5_000,  "icon":"🌱","cat":"Creation",
     "check": lambda df,u,ss: _count(df,u)>=1},
    {"id":"q_with_image",     "title":"Visual Sovereign",      "desc":"Upload a creation with an image.",                        "reward":4_000,  "icon":"🖼️","cat":"Creation",
     "check": lambda df,u,ss: _has_img(df,u)},
    {"id":"q_high_value",     "title":"Million Imaginer",      "desc":"Register a creation worth 1,000,000 IMAGIX or more.",     "reward":25_000, "icon":"💎","cat":"Creation",
     "check": lambda df,u,ss: _max_val(df,u)>=1_000_000},
    # ── Collection
    {"id":"q_three",          "title":"Trilogy of Wonders",    "desc":"Bring 3 creations to the Genesis Layer.",                 "reward":12_000, "icon":"🎨","cat":"Collection",
     "check": lambda df,u,ss: _count(df,u)>=3},
    {"id":"q_five",           "title":"Hand of Wonders",       "desc":"Amass 5 creations.",                                      "reward":18_000, "icon":"🖐","cat":"Collection",
     "check": lambda df,u,ss: _count(df,u)>=5},
    {"id":"q_ten",            "title":"Sovereign Gallery",     "desc":"Build a collection of 10 creations.",                     "reward":30_000, "icon":"🖼️","cat":"Collection",
     "check": lambda df,u,ss: _count(df,u)>=10},
    # ── Actions
    {"id":"q_cert",           "title":"Sacred Title Claimed",  "desc":"Download a Genesis Certificate.",                         "reward":3_000,  "icon":"📜","cat":"Actions",
     "check": lambda df,u,ss: ss.get("cert_ever",False)},
    {"id":"q_split",          "title":"Fractional Sovereign",  "desc":"Activate fractional ownership.",                          "reward":7_500,  "icon":"🔀","cat":"Actions",
     "check": lambda df,u,ss: _has_split(df,u)},
    {"id":"q_list_market",    "title":"Open for Trade",        "desc":"List a creation in the Marketplace.",                     "reward":8_000,  "icon":"🌠","cat":"Actions",
     "check": lambda df,u,ss: ss.get("listed_ever",False)},
    # ── Daily
    {"id":"q_daily",          "title":"Daily Genesis",         "desc":"Upload a creation today.",                                "reward":2_500,  "icon":"☀️","cat":"Daily",
     "check": lambda df,u,ss: _today(df,u)},
    {"id":"q_tutor",          "title":"Wisdom Seeker",         "desc":"Consult a Tutor for the first time.",                     "reward":2_000,  "icon":"🧙","cat":"Daily",
     "check": lambda df,u,ss: ss.get("tutor_used",False)},
    # ── Wealth
    {"id":"q_50k",            "title":"Golden Threshold",      "desc":"Accumulate 50,000 IMAGIX.",                               "reward":10_000, "icon":"💰","cat":"Wealth",
     "check": lambda df,u,ss: ss.get("imagix",0)>=50_000},
    {"id":"q_sponsor",        "title":"Guardian Shield",       "desc":"Sponsor Mode activated on your account.",                 "reward":5_000,  "icon":"🛡️","cat":"Wealth",
     "check": lambda df,u,ss: ss.get("sponsor_viewed",False)},
]

# ── Quest helpers (module-level, not lambdas in list) ─────────
def _count(df,u):
    return len(df[df.sovereign==u]) if not df.empty and "sovereign" in df.columns else 0

def _has_img(df,u):
    udf=df[df.sovereign==u] if not df.empty and "sovereign" in df.columns else pd.DataFrame()
    return any(str(r.get("file_path","")).lower().endswith((".jpg",".jpeg",".png")) for r in udf.to_dict("records"))

def _max_val(df,u):
    udf=df[df.sovereign==u] if not df.empty and "sovereign" in df.columns else pd.DataFrame()
    if udf.empty: return 0
    return pd.to_numeric(udf["value"],errors="coerce").fillna(0).max()

def _has_split(df,u):
    udf=df[df.sovereign==u] if not df.empty and "sovereign" in df.columns else pd.DataFrame()
    if udf.empty: return False
    return bool(udf["is_fractional"].astype(str).str.lower().isin(["true","1"]).any())

def _today(df,u):
    udf=df[df.sovereign==u] if not df.empty and "sovereign" in df.columns else pd.DataFrame()
    if udf.empty: return False
    t=date.today().isoformat()
    return any(str(r.get("created_at","")).startswith(t) for r in udf.to_dict("records"))

DEMO_SHOWCASE = [
    ("Star Dragon Awakening",      48_200,  "🐉"),
    ("Kingdom of Eternal Clouds", 125_000,  "☁️"),
    ("The Brave Robot Friend",     32_800,  "🤖"),
    ("Legendary Enchanted Sword",  67_500,  "⚔️"),
    ("Floating Family Castle",     89_000,  "🏰"),
    ("Crystal Phoenix Rising",     54_300,  "🦅"),
]

EMOJI_PICKS = [
    "🌟","🐉","☁️","🤖","⚔️","🏰","🌙","🔮","🦋",
    "🌊","🦅","🌸","💎","🔥","⚡","🎨","🎭","🏆",
    "🦁","🌺","🎪","🏺","🗝️","📜","🌈","🦄","🐬",
    "🌍","🚀","🎯","🎲","🧬","🔭","⚗️","🌋","🌌",
]

# ══════════════════════════════════════════════════════════════
# ② PAGE CONFIG — must be FIRST Streamlit call
# ══════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="DELPHIA GENESIS | IMAGINARIUM",
    page_icon="🌟",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ══════════════════════════════════════════════════════════════
# ③ THEME INJECTION
# ══════════════════════════════════════════════════════════════
def inject_theme():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700;900&family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=DM+Mono:wght@300;400;500&display=swap');

    :root {{
        --space:{C['space']}; --card:{C['card']}; --card2:{C['card2']};
        --gold:{C['gold']}; --gold2:{C['gold2']}; --teal:{C['teal']};
        --purple:{C['purple']}; --purple2:{C['purple2']};
        --muted:{C['muted']}; --white:{C['white']};
    }}

    html,body,[data-testid="stAppViewContainer"]{{background:var(--space);color:var(--gold);}}
    .stApp{{
        background:
            radial-gradient(ellipse 80% 60% at 15% 10%,rgba(13,45,74,.9) 0%,transparent 70%),
            radial-gradient(ellipse 60% 50% at 85% 85%,rgba(10,31,53,.8) 0%,transparent 70%),
            linear-gradient(180deg,#060f1a 0%,var(--space) 100%);
    }}

    /* Typography */
    h1,h2,h3{{font-family:'Cinzel',serif!important;color:var(--gold)!important;letter-spacing:1px;}}
    p,li,span,div{{font-family:'DM Mono',monospace;}}
    label{{font-family:'DM Mono',monospace!important;color:var(--teal)!important;font-size:11px!important;}}

    /* Buttons */
    .stButton>button{{
        background:linear-gradient(135deg,var(--purple),var(--purple2));
        color:var(--gold);border:1px solid rgba(242,201,76,.5);
        border-radius:8px;font-family:'Cinzel',serif;font-size:10px;
        font-weight:700;letter-spacing:1.5px;padding:8px 14px;
        transition:all .22s ease;width:100%;
    }}
    .stButton>button:hover{{
        background:linear-gradient(135deg,var(--gold),var(--gold2));
        color:var(--space);border-color:var(--gold);
        box-shadow:0 0 18px rgba(242,201,76,.45),0 4px 16px rgba(0,0,0,.4);
        transform:translateY(-2px);
    }}
    .stButton>button[kind="primary"],
    [data-testid="stFormSubmitButton"]>button{{
        background:linear-gradient(135deg,var(--gold),var(--gold2))!important;
        color:var(--space)!important;font-size:12px;padding:11px 28px;
        border:none!important;box-shadow:0 4px 20px rgba(242,201,76,.3);
    }}
    [data-testid="stFormSubmitButton"]>button:hover{{
        background:linear-gradient(135deg,#ffe080,var(--gold))!important;
        color:var(--space)!important;box-shadow:0 0 24px rgba(242,201,76,.6);
    }}
    .stDownloadButton>button{{
        background:linear-gradient(135deg,rgba(0,229,192,.13),rgba(0,229,192,.26))!important;
        color:var(--teal)!important;border:1px solid var(--teal)!important;
        font-family:'Cinzel',serif;font-size:10px;letter-spacing:1px;
        width:100%;transition:all .2s;
    }}
    .stDownloadButton>button:hover{{background:var(--teal)!important;color:var(--space)!important;box-shadow:0 0 16px rgba(0,229,192,.4);}}

    /* Inputs */
    .stTextInput input,.stNumberInput input,.stTextArea textarea{{
        background-color:{C['card']}!important;color:var(--teal)!important;
        border:1px solid rgba(157,78,221,.6)!important;border-radius:8px!important;
        font-family:'DM Mono',monospace!important;font-size:13px!important;
        caret-color:var(--gold);
    }}
    .stTextInput input:focus,.stNumberInput input:focus,.stTextArea textarea:focus{{
        border-color:var(--gold)!important;box-shadow:0 0 0 2px rgba(242,201,76,.15)!important;
    }}
    .stSelectbox [data-baseweb="select"]>div,.stDateInput input{{
        background-color:{C['card']}!important;border:1px solid rgba(157,78,221,.6)!important;
        color:var(--teal)!important;font-family:'DM Mono',monospace!important;
    }}
    [data-testid="stDateInput"]>div>div>input{{background:{C['card']}!important;color:var(--teal)!important;border:1px solid rgba(157,78,221,.6)!important;}}

    /* Password input */
    .stTextInput input[type="password"]{{color:var(--gold)!important;letter-spacing:3px;}}

    /* Tabs */
    .stTabs [data-baseweb="tab-list"]{{background:transparent;border-bottom:1px solid rgba(157,78,221,.4);gap:2px;}}
    .stTabs [data-baseweb="tab"]{{font-family:'Cinzel',serif;font-size:11px;letter-spacing:1px;color:var(--muted);padding:9px 16px;border-radius:8px 8px 0 0;border:1px solid transparent;border-bottom:none;transition:all .2s;}}
    .stTabs [data-baseweb="tab"]:hover{{color:var(--gold);background:rgba(242,201,76,.05);}}
    .stTabs [aria-selected="true"]{{background:var(--card2)!important;color:var(--gold)!important;border-color:rgba(0,229,192,.5)!important;border-bottom:1px solid var(--card2)!important;}}

    /* Metrics */
    [data-testid="metric-container"]{{background:linear-gradient(135deg,{C['card']},{C['card2']});border:1px solid rgba(157,78,221,.5);border-radius:12px;padding:12px 18px;transition:border-color .2s;}}
    [data-testid="metric-container"]:hover{{border-color:var(--gold);}}
    [data-testid="metric-container"] label{{color:var(--teal)!important;font-family:'Cinzel',serif!important;font-size:9px!important;letter-spacing:2px!important;text-transform:uppercase;}}
    [data-testid="stMetricValue"]{{color:var(--gold)!important;font-family:'Cinzel',serif!important;font-weight:700!important;}}

    /* Sidebar */
    [data-testid="stSidebar"]{{background:linear-gradient(180deg,#080f1e 0%,#0a1628 60%,{C['space']} 100%);border-right:1px solid rgba(157,78,221,.4);}}
    [data-testid="stSidebar"] section{{padding-top:0;}}

    /* Progress */
    .stProgress>div>div>div>div{{
        background:linear-gradient(90deg,#9D4EDD,#4facfe 30%,#00E5C0 55%,#43e97b 75%,#F2C94C);
        border-radius:4px;
    }}
    .stProgress>div>div{{background:rgba(255,255,255,.06);border-radius:4px;}}

    /* Alerts */
    .stSuccess>div{{background:rgba(46,204,113,.1)!important;border:1px solid rgba(46,204,113,.4)!important;color:{C['green']}!important;font-family:'DM Mono',monospace!important;border-radius:10px!important;}}
    .stInfo>div{{background:rgba(0,229,192,.08)!important;border:1px solid rgba(0,229,192,.35)!important;color:var(--teal)!important;font-family:'DM Mono',monospace!important;border-radius:10px!important;}}
    .stWarning>div{{background:rgba(242,201,76,.08)!important;border:1px solid rgba(242,201,76,.35)!important;color:var(--gold)!important;border-radius:10px!important;}}
    .stError>div{{background:rgba(255,107,107,.1)!important;border:1px solid rgba(255,107,107,.4)!important;color:{C['danger']}!important;border-radius:10px!important;}}

    /* File uploader */
    [data-testid="stFileUploader"]>div{{background:{C['card']}!important;border:2px dashed rgba(157,78,221,.5)!important;border-radius:14px!important;transition:border-color .2s;}}
    [data-testid="stFileUploader"]>div:hover{{border-color:var(--gold)!important;}}

    /* Divider / Scrollbar */
    hr{{border-color:rgba(157,78,221,.25)!important;margin:12px 0;}}
    ::-webkit-scrollbar{{width:5px;height:5px;}}
    ::-webkit-scrollbar-track{{background:transparent;}}
    ::-webkit-scrollbar-thumb{{background:rgba(157,78,221,.5);border-radius:3px;}}
    ::-webkit-scrollbar-thumb:hover{{background:var(--purple);}}
    .stCaption{{color:var(--muted)!important;font-size:10.5px!important;}}
    .stMarkdown{{color:var(--muted);}}
    .stMarkdown strong{{color:var(--gold)!important;}}
    .stMarkdown code{{background:rgba(0,229,192,.1)!important;color:var(--teal)!important;border:1px solid rgba(0,229,192,.2)!important;border-radius:4px;font-size:11px;}}

    /* ══ CUSTOM COMPONENTS ══════════════════════════════════ */

    /* Genesis Card */
    .g-card{{
        background:linear-gradient(145deg,{C['card']},{C['card2']});
        border:1px solid rgba(0,229,192,.3);border-radius:14px;
        overflow:hidden;transition:all .28s cubic-bezier(.4,0,.2,1);
        position:relative;margin-bottom:8px;
    }}
    .g-card:hover{{border-color:var(--gold);box-shadow:0 0 0 1px rgba(242,201,76,.15),0 8px 32px rgba(0,0,0,.5),0 0 40px rgba(242,201,76,.12);transform:translateY(-5px) scale(1.01);}}
    .g-card-img{{height:130px;background:linear-gradient(135deg,{C['celest']},#142f55);display:flex;align-items:center;justify-content:center;font-size:60px;border-bottom:1px solid rgba(0,229,192,.15);position:relative;overflow:hidden;}}
    .g-card-img::after{{content:'';position:absolute;inset:0;background:radial-gradient(ellipse at 50% 80%,rgba(157,78,221,.1) 0%,transparent 70%);}}
    .g-card-body{{padding:10px 13px 13px;}}
    .g-card-title{{font-family:'Playfair Display',serif;color:#dde8ff;font-size:12.5px;font-weight:700;line-height:1.35;min-height:32px;margin-bottom:5px;}}
    .g-card-value{{font-family:'Cinzel',serif;color:var(--gold);font-size:14px;font-weight:700;}}
    .g-card-id{{font-family:'DM Mono',monospace;color:var(--teal);font-size:8.5px;opacity:.65;margin-top:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}}
    .g-card-badge{{position:absolute;top:8px;right:8px;background:rgba(5,18,31,.88);border:1px solid var(--gold);border-radius:20px;padding:2px 9px;font-family:'Cinzel',serif;font-size:7.5px;color:var(--gold);letter-spacing:1px;backdrop-filter:blur(4px);}}
    .g-card-frac{{position:absolute;bottom:8px;left:8px;background:rgba(0,229,192,.15);border:1px solid var(--teal);border-radius:20px;padding:2px 8px;font-family:'Cinzel',serif;font-size:7px;color:var(--teal);}}
    .g-card-market{{position:absolute;top:8px;left:8px;background:rgba(157,78,221,.25);border:1px solid var(--purple);border-radius:20px;padding:2px 8px;font-family:'Cinzel',serif;font-size:7px;color:#cc99ff;}}

    /* Hero */
    .g-hero{{background:linear-gradient(135deg,#0b1d35 0%,#15284a 50%,#0a1827 100%);border:1px solid rgba(157,78,221,.5);border-radius:18px;padding:32px 40px;text-align:center;position:relative;overflow:hidden;margin-bottom:8px;}}
    .g-hero::before{{content:'';position:absolute;top:-60%;left:50%;transform:translateX(-50%);width:120%;height:120%;background:radial-gradient(ellipse,rgba(157,78,221,.1) 0%,transparent 65%);pointer-events:none;}}
    .g-hero-title{{font-family:'Cinzel',serif;font-size:clamp(20px,3vw,30px);font-weight:900;color:var(--gold);letter-spacing:5px;margin:0;text-shadow:0 0 30px rgba(242,201,76,.3);}}
    .g-hero-sub{{font-family:'DM Mono',monospace;color:var(--teal);font-size:11px;letter-spacing:3px;margin-top:8px;opacity:.9;}}

    /* Quest Card */
    .q-card{{background:linear-gradient(135deg,{C['card']},{C['card2']});border:1px solid rgba(157,78,221,.45);border-radius:12px;padding:14px 18px;margin-bottom:10px;display:flex;align-items:center;gap:14px;transition:all .2s;position:relative;}}
    .q-card:hover{{border-color:rgba(242,201,76,.4);transform:translateX(3px);}}
    .q-card.done{{border-color:rgba(0,229,192,.4);background:linear-gradient(135deg,rgba(0,229,192,.04),rgba(0,229,192,.02));}}
    .q-card.done::after{{content:'✓';position:absolute;right:16px;top:50%;transform:translateY(-50%);color:var(--teal);font-size:18px;font-weight:700;}}
    .q-icon{{font-size:26px;min-width:34px;text-align:center;}}
    .q-info{{flex:1;}}
    .q-title{{font-family:'Cinzel',serif;color:var(--gold);font-size:12px;font-weight:700;margin-bottom:2px;}}
    .q-desc{{font-family:'DM Mono',monospace;color:var(--muted);font-size:10.5px;line-height:1.4;}}
    .q-cat{{font-family:'Cinzel',serif;color:var(--purple);font-size:8px;letter-spacing:1px;margin-bottom:3px;}}
    .q-reward{{font-family:'Cinzel',serif;color:var(--teal);font-size:12px;font-weight:700;white-space:nowrap;margin-right:28px;}}

    /* Rank pill */
    .rank-pill{{background:linear-gradient(135deg,{C['card']},#1c3560);border:2px solid var(--gold);border-radius:50px;padding:7px 22px;display:inline-block;font-family:'Cinzel',serif;color:var(--gold);font-size:13px;font-weight:700;letter-spacing:2px;box-shadow:0 0 20px rgba(242,201,76,.18),inset 0 0 10px rgba(242,201,76,.05);}}

    /* Wallet */
    .wallet-card{{background:linear-gradient(145deg,#0a1e38,#0d2540);border:2px solid rgba(242,201,76,.5);border-radius:16px;padding:24px;text-align:center;position:relative;overflow:hidden;margin-bottom:16px;}}
    .wallet-card::before{{content:'';position:absolute;top:-40%;left:50%;transform:translateX(-50%);width:80%;height:80%;background:radial-gradient(ellipse,rgba(242,201,76,.06) 0%,transparent 70%);}}
    .wallet-amount{{font-family:'Cinzel',serif;color:var(--gold);font-size:clamp(22px,4vw,36px);font-weight:900;letter-spacing:2px;text-shadow:0 0 20px rgba(242,201,76,.4);}}
    .wallet-label{{font-family:'DM Mono',monospace;color:var(--teal);font-size:10px;letter-spacing:3px;margin-top:4px;opacity:.85;}}

    /* Tutor buttons */
    .tutor-btn{{display:inline-flex;align-items:center;gap:8px;background:rgba(10,37,64,.7);border-radius:12px;padding:10px 16px;margin:4px;cursor:pointer;transition:all .2s;border:1px solid rgba(157,78,221,.4);font-family:'Cinzel',serif;font-size:11px;}}
    .tutor-btn:hover{{border-color:var(--gold);background:rgba(20,50,90,.9);transform:scale(1.03);}}
    .tutor-chat{{background:linear-gradient(135deg,rgba(14,34,64,.95),rgba(17,43,77,.95));border:1px solid rgba(0,229,192,.3);border-radius:16px;padding:20px 24px;margin:12px 0;position:relative;}}
    .tutor-chat::before{{content:'';position:absolute;top:-6px;left:28px;width:12px;height:12px;background:{C['card']};border-left:1px solid rgba(0,229,192,.3);border-top:1px solid rgba(0,229,192,.3);transform:rotate(45deg);}}
    .tutor-name{{font-family:'Cinzel',serif;font-size:12px;font-weight:700;margin-bottom:8px;}}
    .tutor-msg{{font-family:'DM Mono',monospace;font-size:12px;color:#ccd6f0;line-height:1.7;}}

    /* Market card */
    .mkt-card{{background:linear-gradient(145deg,{C['card']},{C['card2']});border:1px solid rgba(157,78,221,.35);border-radius:12px;padding:14px 16px;margin-bottom:10px;display:flex;align-items:center;gap:14px;transition:all .2s;}}
    .mkt-card:hover{{border-color:rgba(242,201,76,.4);box-shadow:0 4px 20px rgba(0,0,0,.3);}}
    .mkt-emoji{{font-size:32px;min-width:40px;text-align:center;}}
    .mkt-info{{flex:1;}}
    .mkt-name{{font-family:'Playfair Display',serif;color:#dde8ff;font-size:13px;font-weight:700;}}
    .mkt-seller{{font-family:'DM Mono',monospace;color:var(--muted);font-size:10px;margin-top:2px;}}
    .mkt-price{{font-family:'Cinzel',serif;color:var(--gold);font-size:15px;font-weight:700;white-space:nowrap;}}

    /* Terminal */
    .term-block{{background:rgba(0,0,0,.25);border:1px solid rgba(0,229,192,.15);border-radius:10px;padding:12px 14px;margin:5px 0;}}
    .term-key{{font-size:8.5px;color:{C['teal']};letter-spacing:1.5px;text-transform:uppercase;opacity:.8;}}
    .term-val{{font-family:'Cinzel',serif;color:{C['gold']};font-size:12.5px;font-weight:700;margin-top:1px;}}

    /* Sponsor */
    .sponsor-row{{display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid rgba(157,78,221,.15);}}
    .sponsor-key{{font-family:'DM Mono',monospace;color:{C['muted']};font-size:9px;}}
    .sponsor-val{{font-family:'Cinzel',serif;color:{C['gold']};font-size:10px;font-weight:700;}}

    /* Showcase shimmer */
    @keyframes shimmer{{0%{{background-position:-200% center;}}100%{{background-position:200% center;}}}}
    .showcase-glow{{background:linear-gradient(90deg,transparent 0%,rgba(242,201,76,.06) 30%,rgba(0,229,192,.06) 50%,rgba(242,201,76,.06) 70%,transparent 100%);background-size:200% auto;animation:shimmer 4s linear infinite;border-radius:14px;}}

    /* Confetti flash */
    @keyframes popIn{{0%{{transform:scale(.5);opacity:0;}}70%{{transform:scale(1.1);}}100%{{transform:scale(1);opacity:1;}}}}
    .pop-badge{{animation:popIn .4s ease forwards;}}

    /* Mobile */
    @media(max-width:768px){{
        .g-hero{{padding:20px 16px;}}
        .g-hero-title{{font-size:18px;letter-spacing:2px;}}
        .g-card-img{{height:100px;font-size:44px;}}
        .q-card{{flex-wrap:wrap;}}
        .q-reward{{margin-right:0;}}
    }}
    </style>
    """, unsafe_allow_html=True)

inject_theme()


# ══════════════════════════════════════════════════════════════
# ④ DATA LAYER
# ══════════════════════════════════════════════════════════════

CREATION_COLS = [
    "id","name","sovereign","value","emoji","file_path",
    "created_at","is_fractional","cert_downloaded","fraction_count",
    "listed_price","listed_at",
]
USER_COLS = ["kingdom","pw_hash","dob","sponsor_kingdom","sponsor_pw_hash"]

def ensure_dirs(user: str):
    Path(F["dir"]).mkdir(exist_ok=True)
    Path(f"{F['dir']}/{user}").mkdir(parents=True, exist_ok=True)

def _read(path, cols):
    if os.path.exists(path):
        try:
            df = pd.read_csv(path)
            for c in cols:
                if c not in df.columns: df[c] = ""
            return df
        except: pass
    return pd.DataFrame(columns=cols)

def _write(df, path):
    try: df.to_csv(path, index=False)
    except Exception as e: st.toast(f"⚠️ Save warning: {e}", icon="⚠️")

def load_creations(): return _read(F["creations"], CREATION_COLS)
def save_creations(df): _write(df, F["creations"])
def load_market(): return _read(F["market"], ["id","name","sovereign","value","emoji","listed_price","listed_at"])
def save_market(df): _write(df, F["market"])
def load_users(): return _read(F["users"], USER_COLS)
def save_users(df): _write(df, F["users"])

def load_wallet(user):
    df=_read(F["wallets"],["sovereign","imagix"])
    row=df[df.sovereign==user]
    return int(row.iloc[0]["imagix"]) if not row.empty else 0

def save_wallet(user, imagix):
    df=_read(F["wallets"],["sovereign","imagix"])
    if user in df.sovereign.values: df.loc[df.sovereign==user,"imagix"]=imagix
    else: df=pd.concat([df,pd.DataFrame([{"sovereign":user,"imagix":imagix}])],ignore_index=True)
    _write(df,F["wallets"])

def load_quests(user):
    df=_read(F["quests"],["sovereign","completed_ids"])
    row=df[df.sovereign==user]
    if not row.empty:
        raw=str(row.iloc[0]["completed_ids"])
        return set(x for x in raw.split(",") if x.strip())
    return set()

def save_quests(user, done):
    df=_read(F["quests"],["sovereign","completed_ids"])
    val=",".join(done)
    if user in df.sovereign.values: df.loc[df.sovereign==user,"completed_ids"]=val
    else: df=pd.concat([df,pd.DataFrame([{"sovereign":user,"completed_ids":val}])],ignore_index=True)
    _write(df,F["quests"])

def hash_pw(pw): return hashlib.sha256(pw.encode()).hexdigest()

def register_user(kingdom, pw, dob_str, sponsor="", sponsor_pw=""):
    df=load_users()
    if kingdom in df.kingdom.values: return False,"Kingdom name already taken."
    new={"kingdom":kingdom,"pw_hash":hash_pw(pw),"dob":dob_str,
         "sponsor_kingdom":sponsor,"sponsor_pw_hash":hash_pw(sponsor_pw) if sponsor_pw else ""}
    df=pd.concat([df,pd.DataFrame([new])],ignore_index=True)
    save_users(df)
    return True,"Registered!"

def verify_user(kingdom, pw):
    df=load_users()
    row=df[df.kingdom==kingdom]
    if row.empty: return False,"Kingdom not found."
    if row.iloc[0]["pw_hash"]!=hash_pw(pw): return False,"Wrong password."
    return True,""

def get_user_dob(kingdom):
    df=load_users(); row=df[df.kingdom==kingdom]
    if not row.empty:
        try: return datetime.strptime(str(row.iloc[0]["dob"]),"%Y-%m-%d").date()
        except: pass
    return None

def calc_age(dob):
    if not dob: return 99
    today=date.today()
    return today.year-dob.year-((today.month,today.day)<(dob.month,dob.day))

def generate_id(name, sovereign):
    raw=f"{name}::{sovereign}::{datetime.now().isoformat()}"
    return "GEN-"+hashlib.sha256(raw.encode()).hexdigest()[:8].upper()

def img_to_b64(path):
    try:
        with open(path,"rb") as f: data=base64.b64encode(f.read()).decode()
        ext=Path(path).suffix.lower().lstrip(".")
        mime={"jpg":"jpeg","jpeg":"jpeg","png":"png"}.get(ext,"jpeg")
        return f"data:image/{mime};base64,{data}"
    except: return None


# ══════════════════════════════════════════════════════════════
# ⑤ RANK ENGINE
# ══════════════════════════════════════════════════════════════
def get_rank(imagix):
    name,curr=RANK_TIERS[0][1],0
    nxt=RANK_TIERS[1][0]
    for i,(t,n,_) in enumerate(RANK_TIERS):
        if imagix>=t:
            name,curr=n,t
            nxt=RANK_TIERS[i+1][0] if i+1<len(RANK_TIERS) else t
    span=nxt-curr
    prog=min((imagix-curr)/span,1.0) if span>0 else 1.0
    return {"name":name,"progress":prog,"curr":curr,"next":nxt,"maxed":nxt==curr}


# ══════════════════════════════════════════════════════════════
# ⑥ QUEST ENGINE
# ══════════════════════════════════════════════════════════════
def run_quests(df, user):
    done=st.session_state["quest_completed"]
    ss_extra={
        "imagix":     st.session_state["imagix"],
        "cert_ever":  st.session_state.get("cert_ever",False),
        "tutor_used": st.session_state.get("tutor_used",False),
        "listed_ever":st.session_state.get("listed_ever",False),
        "sponsor_viewed":st.session_state.get("sponsor_viewed",False),
    }
    newly=[]
    for q in QUESTS:
        if q["id"] in done: continue
        try:
            if q["check"](df,user,ss_extra):
                done.add(q["id"])
                st.session_state["imagix"]+=q["reward"]
                newly.append(q)
        except: pass
    if newly:
        st.session_state["quest_completed"]=done
        save_quests(user,done)
        save_wallet(user,st.session_state["imagix"])
        for q in newly:
            st.toast(f"⚡ QUEST: {q['icon']} {q['title']} · +{q['reward']:,} 𝕀",icon="🏆")


# ══════════════════════════════════════════════════════════════
# ⑦ TUTORS
# ══════════════════════════════════════════════════════════════
def get_active_tutors(age):
    return [t for t in TUTORS if t["age_min"]<=age<=t["age_max"]]

def get_tutor_message(tutor, context_tab, user, df):
    """
    Build a prompt and call the Anthropic API for a tutor message.
    Falls back to a canned response if the API is unavailable.
    """
    n_creations=_count(df,user)
    imagix=st.session_state.get("imagix",0)
    ctx_map={
        "vault":     f"El usuario está viendo su Vault con {n_creations} creaciones.",
        "upload":    "El usuario quiere subir una nueva creación.",
        "quests":    f"El usuario está viendo sus Quests. Tiene {len(st.session_state.get('quest_completed',set()))} completadas.",
        "wallet":    f"El usuario está viendo su Wallet con {imagix:,} IMAGIX.",
        "market":    "El usuario está explorando el Marketplace.",
        "default":   f"El usuario {user} está explorando Delphia Genesis.",
    }
    context=ctx_map.get(context_tab,"")

    prompt=(
        f"{tutor['persona']}\n\n"
        f"Contexto actual: {context}\n"
        f"El usuario se llama '{user}' y tiene {n_creations} creaciones y {imagix:,} IMAGIX.\n"
        f"Dale un mensaje de bienvenida, consejo o motivación acorde a tu personalidad. "
        f"Sé específico al contexto. No uses markdown con asteriscos. Responde solo el mensaje, sin prefijos."
    )

    # ── Try real API ──────────────────────────────────────────
    try:
        import urllib.request, json as _json
        payload=_json.dumps({
            "model":"claude-sonnet-4-20250514",
            "max_tokens":300,
            "messages":[{"role":"user","content":prompt}]
        }).encode()
        req=urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=payload,
            headers={"Content-Type":"application/json","anthropic-version":"2023-06-01"},
            method="POST"
        )
        with urllib.request.urlopen(req,timeout=8) as resp:
            data=_json.loads(resp.read())
            return data["content"][0]["text"].strip()
    except Exception:
        pass

    # ── Fallback canned responses ─────────────────────────────
    fallbacks={
        "delphito_bebito": f"¡Hola {user}! 🌟 ¡Estás haciendo cosas súper chidas aquí! ¡Sigue creando y serás el mejor soberano del universo! ✨",
        "delphita_pinga":  f"¡Oye {user}! ¡Boom! 💥 Tu vault se ve epic. ¡Sube más creaciones y conquista el Genesis Layer! ¡Wooow!",
        "chispitas":       f"¡{user}! ¿Sabías que cada creación que registras queda sellada para siempre en la Genesis Layer? ⚡ ¡Como un experimento científico inmortal!",
        "delphito_bonito": f"No cap, {user} — tu vault tiene main character energy 🔥 Sigue construyendo tu legado, literal fire.",
        "emperatriz_fenix":f"Joven Soberano {user} — cada obra que inscribes es un ladrillo de tu legado. 🦅 Los grandes imperios se construyen con paciencia y visión.",
        "rey_delphi":      f"Soberano {user}, en el Multiverso Delphia, cada creación es un acto de voluntad cósmica. 👑 Tu imaginación es la moneda más valiosa del universo Kardashev VI.",
    }
    return fallbacks.get(tutor["id"],f"¡Bienvenido {user}! Sigue creando en el Genesis Layer.")


# ══════════════════════════════════════════════════════════════
# ⑧ PDF CERTIFICATE v0.8 (premium + SHA-256 hash)
# ══════════════════════════════════════════════════════════════
def make_certificate(name, asset_id, sovereign, value):
    buf=io.BytesIO()
    W,H=A4
    c=rl_canvas.Canvas(buf,pagesize=A4)
    c.setTitle(f"Genesis Certificate · {name}")

    # ── Background ────────────────────────────────────────────
    c.setFillColor(HexColor("#04101e"))
    c.rect(0,0,W,H,fill=1,stroke=0)

    # Star field
    rng=random.Random(42)
    for _ in range(110):
        sx,sy=rng.uniform(25,W-25),rng.uniform(60,H-60)
        c.setFillColorRGB(1,1,1,alpha=rng.uniform(.08,.4))
        c.circle(sx,sy,rng.uniform(.25,1.1),fill=1,stroke=0)

    # Glow rings
    for r,a in [(220,.02),(150,.04),(90,.07),(50,.06),(28,.05)]:
        c.setFillColorRGB(.35,.28,.82,alpha=a)
        c.circle(W/2,H/2,r,fill=1,stroke=0)

    # ── Borders ───────────────────────────────────────────────
    c.setStrokeColor(HexColor(C["gold"])); c.setLineWidth(3)
    c.roundRect(14,14,W-28,H-28,18,fill=0,stroke=1)
    c.setStrokeColor(HexColor(C["purple"])); c.setLineWidth(.9)
    c.roundRect(22,22,W-44,H-44,13,fill=0,stroke=1)
    c.setStrokeColor(HexColor(C["gold"])); c.setLineWidth(.35)
    c.setDash(4,3); c.roundRect(28,28,W-56,H-56,11,fill=0,stroke=1); c.setDash()

    # Corner ornaments
    for ox,oy in [(24,24),(W-24,24),(24,H-24),(W-24,H-24)]:
        c.setStrokeColor(HexColor(C["gold"])); c.setLineWidth(1.4)
        c.circle(ox,oy,7,fill=0,stroke=1)
        c.setFillColor(HexColor(C["gold"])); c.circle(ox,oy,3,fill=1,stroke=0)

    # ── Header ────────────────────────────────────────────────
    c.setFillColorRGB(.04,.10,.19,alpha=.95)
    c.roundRect(30,H-110,W-60,80,8,fill=1,stroke=0)
    c.setStrokeColor(HexColor(C["gold"])); c.setLineWidth(.6)
    c.roundRect(30,H-110,W-60,80,8,fill=0,stroke=1)
    c.setFillColor(HexColor(C["gold"])); c.setFont("Helvetica-Bold",25)
    c.drawCentredString(W/2,H-64,"DELPHIA GENESIS")
    c.setFillColor(HexColor(C["teal"])); c.setFont("Helvetica",9.5)
    c.drawCentredString(W/2,H-86,"✦  CERTIFICATE OF IMAGINATION  ·  GENESIS LAYER v0.8  ✦")

    # ── Star ─────────────────────────────────────────────────
    star_cy=H-190
    def draw_star(cx,cy,ro,ri,pts=5):
        path=c.beginPath()
        for i in range(pts*2):
            angle=math.pi/pts*i-math.pi/2
            r=ro if i%2==0 else ri
            path.moveTo(cx+r*math.cos(angle),cy+r*math.sin(angle)) if i==0 else path.lineTo(cx+r*math.cos(angle),cy+r*math.sin(angle))
        path.close(); c.drawPath(path,fill=1,stroke=1)

    for r,a in [(58,.06),(44,.10),(32,.08)]:
        c.setFillColorRGB(.95,.79,.30,alpha=a); c.circle(W/2,star_cy,r,fill=1,stroke=0)
    c.setFillColor(HexColor(C["gold"])); c.setStrokeColor(HexColor(C["purple"])); c.setLineWidth(1.2)
    draw_star(W/2,star_cy,35,14)
    c.setStrokeColor(HexColor(C["teal"])); c.setLineWidth(.7)
    c.setFillColorRGB(0,0,0,alpha=0); c.circle(W/2,star_cy,52,fill=0,stroke=1)

    # ── Decorative rule ───────────────────────────────────────
    ry=H-236
    c.setStrokeColor(HexColor(C["purple"])); c.setLineWidth(.7)
    c.line(46,ry,W-46,ry)
    c.setStrokeColor(HexColor(C["gold"])); c.setLineWidth(.35)
    c.line(56,ry-5,W-56,ry-5)

    # ── Fields ────────────────────────────────────────────────
    def draw_field(lbl,val,y):
        c.setFillColor(HexColor(C["teal"])); c.setFont("Helvetica",7.5)
        c.drawCentredString(W/2,y+17,lbl.upper())
        c.setStrokeColor(HexColor(C["purple"])); c.setLineWidth(.35)
        c.line(72,y+13,W-72,y+13)
        c.setFillColor(HexColor(C["white"])); c.setFont("Helvetica-Bold",13)
        disp=val[:50]+"…" if len(val)>50 else val
        c.drawCentredString(W/2,y,disp)

    sha256=hashlib.sha256(f"{asset_id}::{name}::{sovereign}".encode()).hexdigest().upper()
    fields=[
        ("Creation",       str(name)[:55]),
        ("Genesis ID",     str(asset_id)),
        ("Young Sovereign",str(sovereign)[:45]),
        ("Imagined Value", f"{int(value):,} IMAGIX"),
        ("Date Sealed",    datetime.now().strftime("%d %B %Y").upper()),
        ("Status",         "SACRED & IMMUTABLE"),
    ]
    fy,gap=H-278,48
    for i,(lbl,v) in enumerate(fields):
        draw_field(lbl,v,fy-i*gap)

    # ── SHA-256 HASH block ────────────────────────────────────
    hash_y=fy-len(fields)*gap-18
    c.setFillColorRGB(.04,.10,.19,alpha=.8)
    c.roundRect(36,hash_y-28,W-72,44,6,fill=1,stroke=0)
    c.setStrokeColor(HexColor(C["purple"])); c.setLineWidth(.5)
    c.roundRect(36,hash_y-28,W-72,44,6,fill=0,stroke=1)
    c.setFillColor(HexColor(C["teal"])); c.setFont("Helvetica",7)
    c.drawCentredString(W/2,hash_y+8,"GENESIS HASH · SHA-256 INTEGRITY SEAL")
    c.setFillColor(HexColor(C["gold"])); c.setFont("Helvetica-Bold",7.5)
    c.drawCentredString(W/2,hash_y-14,sha256[:32])
    c.drawCentredString(W/2,hash_y-24,sha256[32:])

    # ── Bottom rules ──────────────────────────────────────────
    bot_y=hash_y-42
    c.setStrokeColor(HexColor(C["gold"])); c.setLineWidth(.7)
    c.line(46,bot_y,W-46,bot_y)
    c.setStrokeColor(HexColor(C["purple"])); c.setLineWidth(.35)
    c.line(56,bot_y-5,W-56,bot_y-5)

    # ── Signature ─────────────────────────────────────────────
    sig_y=bot_y-46
    c.setFillColor(HexColor(C["purple"])); c.setFont("Helvetica",8)
    c.drawCentredString(W/2,sig_y+16,"— Signed by the Keeper of the Genesis Layer —")
    c.setFillColor(HexColor(C["gold"])); c.setFont("Helvetica-Bold",11)
    c.drawCentredString(W/2,sig_y,"REY DELPHI  ·  REINO DE DELPHIA  ·  KARDASHEV VI")

    # ── Footer ────────────────────────────────────────────────
    c.setFillColor(HexColor(C["teal"])); c.setFont("Helvetica",7)
    c.drawCentredString(W/2,28,"Delphia Genesis v0.8  ·  Where Imagination Becomes Sovereign  ·  delphia.genesis")

    c.save()
    return buf.getvalue()


# ══════════════════════════════════════════════════════════════
# ⑨ SESSION STATE (mover antes de cualquier lógica)
# ══════════════════════════════════════════════════════════════
_DEFAULTS={
    "authenticated":False,"user":"","imagix":0,
    "quest_completed":set(),"creations_df":None,
    "split_open":{},"cert_triggered":{},"cert_ever":False,
    "parent_mode":False,"tutor_open":None,"tutor_used":False,
    "listed_ever":False,"sponsor_viewed":False,
    "active_tab":"vault","market_refresh":False,
}
for k,v in _DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ══════════════════════════════════════════════════════════════
# ⑩ AUTH — Register / Login
# ══════════════════════════════════════════════════════════════
if not st.session_state["authenticated"]:
    st.markdown("""
    <div class="g-hero" style="margin-top:40px;padding:48px 40px;">
        <div class="g-hero-title">⬟ DELPHIA GENESIS ⬟</div>
        <div class="g-hero-sub">THE IMAGINARIUM · GENESIS LAYER v0.8</div>
    </div>
    """,unsafe_allow_html=True)

    _,mid,_=st.columns([1,1.6,1])
    with mid:
        auth_tab_login, auth_tab_reg = st.tabs(["🔑 LOGIN","🌟 REGISTER"])

        with auth_tab_login:
            st.markdown(f"<div style='font-family:DM Mono;color:{C['muted']};font-size:11px;margin-bottom:16px;'>Enter your Kingdom to access your Sovereign Vault.</div>",unsafe_allow_html=True)
            lk=st.text_input("Kingdom Name",key="l_kingdom",placeholder="Astra Nova",label_visibility="collapsed")
            lp=st.text_input("Password",key="l_pw",type="password",placeholder="Your sacred password",label_visibility="collapsed")
            st.write("")
            if st.button("✦ ENTER THE IMAGINARIUM",type="primary",use_container_width=True,key="login_btn"):
                if not lk.strip() or not lp.strip():
                    st.warning("Kingdom name and password required.")
                else:
                    ok,msg=verify_user(lk.strip(),lp.strip())
                    if ok:
                        u=lk.strip()
                        st.session_state["authenticated"]=True
                        st.session_state["user"]=u
                        st.session_state["quest_completed"]=load_quests(u)
                        st.session_state["imagix"]=load_wallet(u)
                        ensure_dirs(u)
                        st.rerun()
                    else:
                        st.error(f"⚠️ {msg}")

        with auth_tab_reg:
            st.markdown(f"<div style='font-family:DM Mono;color:{C['muted']};font-size:11px;margin-bottom:16px;'>Create your Kingdom on the Genesis Layer.</div>",unsafe_allow_html=True)
            rk=st.text_input("Kingdom Name ✦",key="r_kingdom",placeholder="e.g. Astra Nova",label_visibility="collapsed")
            rp=st.text_input("Sacred Password",key="r_pw",type="password",placeholder="Choose a strong password",label_visibility="collapsed")
            rp2=st.text_input("Confirm Password",key="r_pw2",type="password",placeholder="Repeat your password",label_visibility="collapsed")
            rdob=st.date_input("Date of Birth",key="r_dob",min_value=date(1990,1,1),max_value=date.today(),value=date(2010,1,1))
            st.caption("Used to match you with the right Tutors on the Genesis Layer.")
            st.write("")

            with st.expander("👁 Add a Sponsor / Parent (optional)"):
                sp_kingdom=st.text_input("Sponsor Kingdom Name",key="sp_k",placeholder="Parent's Kingdom",label_visibility="visible")
                sp_pw=st.text_input("Sponsor Password",key="sp_p",type="password",placeholder="Sponsor's password",label_visibility="visible")
                st.caption("Your sponsor can view your progress and approve large actions.")

            if st.button("🌟 FORGE MY KINGDOM",type="primary",use_container_width=True,key="reg_btn"):
                if not rk.strip():
                    st.error("Your Kingdom needs a name.")
                elif len(rp)<4:
                    st.error("Password must be at least 4 characters.")
                elif rp!=rp2:
                    st.error("Passwords do not match.")
                else:
                    ok,msg=register_user(
                        rk.strip(),rp,rdob.isoformat(),
                        st.session_state.get("sp_k",""),
                        st.session_state.get("sp_p","")
                    )
                    if ok:
                        u=rk.strip()
                        st.session_state["authenticated"]=True
                        st.session_state["user"]=u
                        st.session_state["quest_completed"]=set()
                        st.session_state["imagix"]=0
                        ensure_dirs(u)
                        st.success("✦ Kingdom forged! Welcome to the Genesis Layer.")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(msg)
    st.stop()


# ══════════════════════════════════════════════════════════════
# ⑪ MAIN APP — Solo después de autenticación
# ══════════════════════════════════════════════════════════════
user: str = st.session_state["user"]
ensure_dirs(user)

# Cargar datos solo si ya estamos autenticados
if st.session_state["creations_df"] is None:
    st.session_state["creations_df"] = load_creations()

df_all: pd.DataFrame = st.session_state["creations_df"]
user_df = df_all[df_all["sovereign"] == user].copy() if not df_all.empty and "sovereign" in df_all.columns else pd.DataFrame(columns=CREATION_COLS)

# ←←← Mover run_quests AQUÍ, después de cargar df_all
run_quests(df_all, user)

total_imagix = st.session_state["imagix"]
rank = get_rank(total_imagix)
n_done = len(st.session_state["quest_completed"])

# User age & active tutors (solo después de auth)
dob = get_user_dob(user)
age = calc_age(dob)
active_tutors = get_active_tutors(age)


# ── HEADER ───────────────────────────────────────────────────
h1,h2,h3,h4,h5=st.columns([4,1,1,1,1])
h1.markdown(f"""
<div style="padding-top:8px;">
    <span style="font-family:'Cinzel',serif;font-size:17px;color:{C['gold']};font-weight:700;">🌟 {user}</span>
    &nbsp;<span style="color:{C['muted']};font-size:13px;">·</span>&nbsp;
    <span class="rank-pill" style="font-size:11px;padding:4px 14px;">{rank['name']}</span>
</div>""",unsafe_allow_html=True)
h2.metric("IMAGIX",f"{total_imagix:,} 𝕀")
h3.metric("CREATIONS",len(user_df))
h4.metric("QUESTS",f"{n_done}/{len(QUESTS)}")
if h5.button("✦ LOGOUT"):
    for k in list(_DEFAULTS.keys()):
        if k in st.session_state: del st.session_state[k]
    st.rerun()

# Rainbow rank bar
pb,_=st.columns([3,1])
with pb:
    if not rank["maxed"]:
        st.progress(rank["progress"],text=f"Progress to next rank · {total_imagix:,} / {rank['next']:,} IMAGIX")
    else:
        st.progress(1.0,text="👑 LEGEND — Supreme Sovereign of the Genesis Layer")

st.divider()


# ══════════════════════════════════════════════════════════════
# TUTORS FLOATING PANEL (shown above tabs when a tutor is open)
# ══════════════════════════════════════════════════════════════
def render_tutors(context_tab="default"):
    if not active_tutors: return
    st.markdown(f"""
    <div style="font-family:'Cinzel',serif;color:{C['teal']};font-size:9px;letter-spacing:2px;margin-bottom:8px;">
        ✦ GENESIS TUTORS — Choose your guide
    </div>""",unsafe_allow_html=True)

    tutor_cols=st.columns(len(active_tutors))
    for i,t in enumerate(active_tutors):
        with tutor_cols[i]:
            if st.button(f"{t['emoji']} {t['name']}",key=f"tutor_btn_{t['id']}_{context_tab}"):
                if st.session_state["tutor_open"]==t["id"]:
                    st.session_state["tutor_open"]=None
                else:
                    with st.spinner(f"{t['emoji']} {t['name']} está pensando…"):
                        msg=get_tutor_message(t,context_tab,user,df_all)
                    st.session_state[f"tutor_msg_{t['id']}"]=msg
                    st.session_state["tutor_open"]=t["id"]
                    if not st.session_state["tutor_used"]:
                        st.session_state["tutor_used"]=True
                        run_quests(df_all,user)

    if st.session_state["tutor_open"]:
        tid=st.session_state["tutor_open"]
        t=next((x for x in active_tutors if x["id"]==tid),None)
        if t:
            msg=st.session_state.get(f"tutor_msg_{tid}","…")
            st.markdown(f"""
            <div class="tutor-chat">
                <div class="tutor-name" style="color:{t['color']};">{t['emoji']} {t['name']}</div>
                <div class="tutor-msg">{msg}</div>
            </div>""",unsafe_allow_html=True)

    st.divider()


# ══════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════
tab_vault,tab_wallet,tab_quests,tab_market,tab_upload=st.tabs([
    "🌌 MY VAULT","💎 WALLET","⚔️ QUESTS","🌠 MARKETPLACE","🌱 UPLOAD",
])


# ────────────────────────────────────────────────────────────
# TAB: VAULT
# ────────────────────────────────────────────────────────────
with tab_vault:
    render_tutors("vault")

    vc1,vc2=st.columns([3,1])
    vc1.markdown("### 🌌 SOVEREIGN CREATIONS VAULT")
    with vc2:
        sort_opt=st.selectbox("Sort by",["Newest","Highest Value","Alphabetical"],label_visibility="collapsed")

    if user_df.empty:
        st.info("🌠 Your vault awaits its first creation. Upload below to begin your Genesis journey!")
        st.markdown(f"""<div style="font-family:'Cinzel',serif;color:{C['gold']};font-size:14px;margin:20px 0 12px;letter-spacing:1px;">✦ GENESIS SHOWCASE — Creations from the Multiverse</div>""",unsafe_allow_html=True)
        dc=st.columns(6)
        for i,(dn,dv,de) in enumerate(DEMO_SHOWCASE):
            with dc[i%6]:
                st.markdown(f"""
                <div class="g-card showcase-glow">
                    <div class="g-card-img"><span style="font-size:60px;">{de}</span></div>
                    <div class="g-card-body">
                        <div class="g-card-badge">SHOWCASE</div>
                        <div class="g-card-title">{dn}</div>
                        <div class="g-card-value">{dv:,} 𝕀</div>
                        <div class="g-card-id">DEMO · GENESIS MULTIVERSE</div>
                    </div>
                </div>""",unsafe_allow_html=True)
    else:
        sdf=user_df.copy()
        if sort_opt=="Newest":    sdf=sdf.sort_values("created_at",ascending=False)
        elif sort_opt=="Highest Value":
            sdf["_v"]=pd.to_numeric(sdf["value"],errors="coerce").fillna(0); sdf=sdf.sort_values("_v",ascending=False)
        else: sdf=sdf.sort_values("name")
        st.caption(f"{len(sdf)} creation(s) on the Genesis Layer")

        # Portfolio summary
        total_val=pd.to_numeric(sdf["value"],errors="coerce").fillna(0).sum()
        sc1,sc2,sc3=st.columns(3)
        sc1.metric("PORTFOLIO VALUE",f"{total_val:,.0f} 𝕀")
        sc2.metric("FRACTIONALISED",int(sdf["is_fractional"].astype(str).str.lower().isin(["true","1"]).sum()))
        sc3.metric("CERTS ISSUED",int(sdf["cert_downloaded"].astype(str).str.lower().isin(["true","1"]).sum()))

        records=sdf.to_dict("records")
        CPR=4
        for rs in range(0,len(records),CPR):
            cols=st.columns(CPR)
            for ci,rec in enumerate(records[rs:rs+CPR]):
                with cols[ci]:
                    aid=str(rec.get("id",""))
                    rn=str(rec.get("name","Unknown"))
                    rv=int(float(str(rec.get("value",0)).replace(",","") or 0))
                    re_=str(rec.get("emoji") or "🌟")
                    rfp=str(rec.get("file_path",""))
                    is_frac=str(rec.get("is_fractional","")).lower() in ("true","1")
                    is_listed=bool(str(rec.get("listed_price","")).strip() not in ("","nan","0"))

                    frac_badge=f'<div class="g-card-frac">⅒ FRACTIONAL</div>' if is_frac else ""
                    mkt_badge=f'<div class="g-card-market">🌠 LISTED</div>' if is_listed else ""

                    has_img=(rfp and os.path.exists(rfp) and rfp.lower().endswith((".jpg",".jpeg",".png")))
                    b64=img_to_b64(rfp) if has_img else None

                    if b64:
                        st.markdown(f"""
                        <div class="g-card">
                            <div class="g-card-img" style="padding:0;position:relative;">
                                <img src="{b64}" style="width:100%;height:130px;object-fit:cover;display:block;">
                                {frac_badge}{mkt_badge}
                            </div>
                            <div class="g-card-body">
                                <div class="g-card-title">{rn}</div>
                                <div class="g-card-value">{rv:,} 𝕀</div>
                                <div class="g-card-id">{aid}</div>
                            </div>
                        </div>""",unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div class="g-card">
                            <div class="g-card-img">
                                <span style="font-size:60px;position:relative;z-index:1;">{re_}</span>
                                {frac_badge}{mkt_badge}
                            </div>
                            <div class="g-card-body">
                                <div class="g-card-title">{rn}</div>
                                <div class="g-card-value">{rv:,} 𝕀</div>
                                <div class="g-card-id">{aid}</div>
                            </div>
                        </div>""",unsafe_allow_html=True)

                    # ── TITLE button
                    if st.button("📜 TITLE",key=f"title_{aid}"):
                        st.session_state["cert_triggered"][aid]=True
                        if not st.session_state["cert_ever"]:
                            st.session_state["cert_ever"]=True
                            run_quests(df_all,user)
                        st.rerun()

                    if st.session_state["cert_triggered"].get(aid):
                        try:
                            pdf=make_certificate(rn,aid,user,rv)
                            st.download_button(
                                "⬇️ Download Certificate",data=pdf,
                                file_name=f"{rn[:24].replace(' ','_')}_Certificate.pdf",
                                mime="application/pdf",key=f"dl_{aid}",use_container_width=True)
                            df_all.loc[df_all["id"]==aid,"cert_downloaded"]=True
                            save_creations(df_all)
                        except Exception as e:
                            st.error(f"Certificate error: {e}")

                    # ── SPLIT button
                    split_lbl="🔀 SPLIT" if not is_frac else "⅒ FRACS"
                    if st.button(split_lbl,key=f"split_{aid}"):
                        st.session_state["split_open"][aid]=(not st.session_state["split_open"].get(aid,False))
                        if not is_frac:
                            df_all.loc[df_all["id"]==aid,"is_fractional"]=True
                            df_all.loc[df_all["id"]==aid,"fraction_count"]=100
                            save_creations(df_all)
                            st.session_state["creations_df"]=df_all
                            run_quests(df_all,user)
                        st.rerun()

                    if st.session_state["split_open"].get(aid):
                        n_f=int(float(str(rec.get("fraction_count",100)) or 100))
                        fv=rv/n_f
                        st.success(f"**{rn}** → **{n_f}** shares · **{fv:,.0f} 𝕀** each ✦")

                    # ── LIST in Marketplace button
                    list_lbl="🌠 DELIST" if is_listed else "🌠 LIST"
                    if st.button(list_lbl,key=f"list_{aid}"):
                        if not is_listed:
                            # List it
                            df_all.loc[df_all["id"]==aid,"listed_price"]=rv
                            df_all.loc[df_all["id"]==aid,"listed_at"]=datetime.now().isoformat()
                            save_creations(df_all)
                            # Add to market
                            mdf=load_market()
                            if aid not in mdf["id"].values:
                                mdf=pd.concat([mdf,pd.DataFrame([{
                                    "id":aid,"name":rn,"sovereign":user,
                                    "value":rv,"emoji":re_,"listed_price":rv,
                                    "listed_at":datetime.now().isoformat()
                                }])],ignore_index=True)
                            save_market(mdf)
                            st.session_state["listed_ever"]=True
                            run_quests(df_all,user)
                            st.success(f"✦ **{rn}** is now listed in the Marketplace!")
                        else:
                            df_all.loc[df_all["id"]==aid,"listed_price"]=""
                            df_all.loc[df_all["id"]==aid,"listed_at"]=""
                            save_creations(df_all)
                            mdf=load_market()
                            mdf=mdf[mdf["id"]!=aid]
                            save_market(mdf)
                            st.info(f"✦ **{rn}** removed from Marketplace.")
                        st.session_state["creations_df"]=load_creations()
                        st.rerun()


# ────────────────────────────────────────────────────────────
# TAB: WALLET
# ────────────────────────────────────────────────────────────
with tab_wallet:
    render_tutors("wallet")
    st.markdown("### 💎 IMAGIX WALLET")

    _,wm,_=st.columns([1,1.5,1])
    with wm:
        st.markdown(f"""
        <div class="wallet-card">
            <div class="wallet-label">CURRENT BALANCE</div>
            <div class="wallet-amount">{total_imagix:,} 𝕀</div>
            <div class="wallet-label" style="margin-top:8px;">IMAGIX · GENESIS LAYER v0.8</div>
        </div>""",unsafe_allow_html=True)

    st.divider()

    # Portfolio stats
    if not user_df.empty:
        pv=pd.to_numeric(user_df["value"],errors="coerce").fillna(0).sum()
        credit_est=int(pv*0.25+total_imagix*1.5)
        pc1,pc2,pc3=st.columns(3)
        pc1.metric("VAULT VALUE",f"{pv:,.0f} 𝕀")
        pc2.metric("IMAGIX EARNED",f"{total_imagix:,} 𝕀")
        pc3.metric("CREDIT CAPACITY",f"~{credit_est:,} 𝕀",help="Estimated based on vault + wallet")

    st.divider()
    st.markdown("#### ✦ Earnings Ledger")

    # Beautiful ledger table using HTML
    rows_html=""
    for cat in ["Onboarding","Creation","Collection","Actions","Daily","Wealth"]:
        cat_quests=[q for q in QUESTS if q.get("cat")==cat]
        if not cat_quests: continue
        rows_html+=f'<tr><td colspan="3" style="background:rgba(157,78,221,.1);padding:6px 12px;font-family:Cinzel,serif;font-size:9px;color:{C["purple"]};letter-spacing:2px;text-transform:uppercase;">{cat}</td></tr>'
        for q in cat_quests:
            done_flag=q["id"] in st.session_state["quest_completed"]
            status="✅ DONE" if done_flag else "○ PENDING"
            status_col=C["teal"] if done_flag else C["muted"]
            reward_col=C["gold"] if done_flag else C["muted"]
            rows_html+=f"""
            <tr style="border-bottom:1px solid rgba(157,78,221,.15);">
                <td style="padding:8px 12px;font-family:'DM Mono',monospace;font-size:11px;color:#ccd6f0;">{q['icon']} {q['title']}</td>
                <td style="padding:8px 12px;font-family:'DM Mono',monospace;font-size:10px;color:{status_col};">{status}</td>
                <td style="padding:8px 12px;font-family:'Cinzel',serif;font-size:11px;font-weight:700;color:{reward_col};text-align:right;">+{q['reward']:,} 𝕀</td>
            </tr>"""

    st.markdown(f"""
    <table style="width:100%;border-collapse:collapse;background:linear-gradient(135deg,{C['card']},{C['card2']});border:1px solid rgba(157,78,221,.3);border-radius:12px;overflow:hidden;">
        <thead>
            <tr style="border-bottom:1px solid rgba(157,78,221,.4);">
                <th style="padding:10px 12px;font-family:'Cinzel',serif;font-size:9px;color:{C['teal']};letter-spacing:2px;text-align:left;">QUEST</th>
                <th style="padding:10px 12px;font-family:'Cinzel',serif;font-size:9px;color:{C['teal']};letter-spacing:2px;text-align:left;">STATUS</th>
                <th style="padding:10px 12px;font-family:'Cinzel',serif;font-size:9px;color:{C['teal']};letter-spacing:2px;text-align:right;">REWARD</th>
            </tr>
        </thead>
        <tbody>{rows_html}</tbody>
    </table>""",unsafe_allow_html=True)

    st.write("")
    total_pot=sum(q["reward"] for q in QUESTS)
    earned=sum(q["reward"] for q in QUESTS if q["id"] in st.session_state["quest_completed"])
    wc1,wc2,wc3=st.columns(3)
    wc1.metric("EARNED",f"{earned:,} 𝕀")
    wc2.metric("TOTAL POTENTIAL",f"{total_pot:,} 𝕀")
    wc3.metric("REMAINING",f"{total_pot-earned:,} 𝕀")


# ────────────────────────────────────────────────────────────
# TAB: QUESTS
# ────────────────────────────────────────────────────────────
with tab_quests:
    render_tutors("quests")
    st.markdown("### ⚔️ QUESTS & PROGRESS")

    qc1,qc2=st.columns([2,1])
    with qc1:
        st.markdown(f"""<div style="margin-bottom:18px;"><div style="font-family:'DM Mono',monospace;color:{C['teal']};font-size:9px;letter-spacing:3px;margin-bottom:8px;">CURRENT RANK</div><div class="rank-pill">{rank['name']}</div></div>""",unsafe_allow_html=True)
        if not rank["maxed"]:
            st.progress(rank["progress"],text=f"{rank['next']-total_imagix:,} IMAGIX needed to advance")
        else:
            st.progress(1.0,text="👑 Maximum rank — you are LEGEND")
    with qc2:
        st.markdown(f"""
        <div style="background:{C['card']};border:1px solid rgba(157,78,221,.4);border-radius:12px;padding:16px 20px;text-align:center;">
            <div style="font-family:'DM Mono',monospace;color:{C['teal']};font-size:9px;letter-spacing:2px;margin-bottom:10px;">RANK TIERS</div>
            <div style="font-family:'Cinzel',serif;color:{C['muted']};font-size:9.5px;line-height:2.1;">
                ✦ SPARK I–III · 0–25k<br>🔥 FLAME I–III · 50k–175k<br>⭐ STAR I–III · 275k–600k<br>👑 LEGEND · 900k+
            </div>
        </div>""",unsafe_allow_html=True)

    st.divider()
    done_ids=st.session_state["quest_completed"]
    for cat in ["Onboarding","Creation","Collection","Actions","Daily","Wealth"]:
        cat_qs=[q for q in QUESTS if q.get("cat")==cat]
        if not cat_qs: continue
        st.markdown(f"""<div style="font-family:'Cinzel',serif;color:{C['purple']};font-size:10px;letter-spacing:2px;margin:16px 0 8px;text-transform:uppercase;">◈ {cat}</div>""",unsafe_allow_html=True)
        for q in cat_qs:
            done=q["id"] in done_ids
            css="q-card done" if done else "q-card"
            st.markdown(f"""
            <div class="{css}">
                <div class="q-icon">{q['icon']}</div>
                <div class="q-info">
                    <div class="q-title">{'✅ ' if done else '○ '}{q['title']}</div>
                    <div class="q-desc">{q['desc']}</div>
                </div>
                <div class="q-reward">+{q['reward']:,} 𝕀</div>
            </div>""",unsafe_allow_html=True)

    st.divider()
    dc=len(done_ids); rem_pot=sum(q["reward"] for q in QUESTS if q["id"] not in done_ids)
    st.markdown(f"**Completed:** `{dc} / {len(QUESTS)}`  ·  **Earned:** `{total_imagix:,} 𝕀`  ·  **Remaining potential:** `{rem_pot:,} 𝕀`")


# ────────────────────────────────────────────────────────────
# TAB: MARKETPLACE
# ────────────────────────────────────────────────────────────
with tab_market:
    render_tutors("market")
    st.markdown("### 🌠 GENESIS MARKETPLACE")
    
    # Asegurar balance actual
    current_balance = st.session_state.get("imagix", 0)

    mdf = load_market()
    if mdf.empty or "id" not in mdf.columns:
        st.info("No creations listed yet — be the first Sovereign to trade!")
    else:
        for _, mrow in mdf.iterrows():
            mid = str(mrow.get("id",""))
            mn = str(mrow.get("name",""))
            ms = str(mrow.get("sovereign",""))
            me = str(mrow.get("emoji","🌟"))
            mp = int(float(str(mrow.get("listed_price", 0)) or 0))
            is_own = (ms == user)

            st.markdown(f"""
            <div class="mkt-card">
                <div class="mkt-emoji">{me}</div>
                <div style="flex:1;">
                    <div style="font-family:'Playfair Display',serif; color:#dde8ff; font-size:13px;">{mn}</div>
                    <div style="font-family:'DM Mono',monospace; color:{C['muted']}; font-size:10px;">by {ms}</div>
                </div>
                <div style="font-family:'Cinzel',serif; color:{C['gold']}; font-size:15px; font-weight:700;">{mp:,} 𝕀</div>
            </div>""", unsafe_allow_html=True)

            if not is_own:
                if st.button(f"💰 BUY · {mid}", key=f"btn_buy_{mid}"):
                    if current_balance >= mp:
                        # 1. Cobrar al comprador
                        st.session_state["imagix"] -= mp
                        save_wallet(user, st.session_state["imagix"])

                        # 2. PAGAR AL VENDEDOR (Fuga sellada)
                        seller_bal = load_wallet(ms)
                        save_wallet(ms, seller_bal + mp)

                        # 3. Transferir propiedad y limpiar mercado
                        mdf2 = load_market(); mdf2 = mdf2[mdf2["id"] != mid]; save_market(mdf2)
                        cdf2 = load_creations()
                        cdf2.loc[cdf2["id"] == mid, "sovereign"] = user
                        cdf2.loc[cdf2["id"] == mid, "listed_price"] = ""
                        save_creations(cdf2)
                        
                        st.session_state["creations_df"] = load_creations()
                        st.success(f"✦ ¡Adquiriste {mn}! El pago fue enviado a {ms}.")
                        st.rerun()
                    else:
                        st.error(f"Necesitas {mp - current_balance:,} 𝕀 adicionales.")


# ────────────────────────────────────────────────────────────
# TAB: UPLOAD
# ────────────────────────────────────────────────────────────
with tab_upload:
    render_tutors("upload")
    st.markdown("### 🌱 REGISTER YOUR CREATION")
    st.caption("Inscribe your art, story, or craft onto the Genesis Layer — permanently.")

    with st.form("genesis_upload",clear_on_submit=True):
        cn=st.text_input("Creation Name ✦",placeholder="e.g. The Adventures of Luna the Fox")
        uc1,uc2=st.columns(2)
        with uc1:
            ep=st.selectbox("Creation Emblem",EMOJI_PICKS)
        with uc2:
            iv=st.number_input("Imagined Value (IMAGIX)",min_value=100,max_value=10_000_000,value=10_000,step=500)
        uf=st.file_uploader("Upload your creation (image or PDF — optional)",type=["jpg","jpeg","png","pdf"],
            help="Images appear as card thumbnails in your Vault.")
        desc=st.text_area("Creation Lore (optional)",placeholder="Describe the legend behind your creation…",max_chars=280,height=80)
        ok_sub=st.form_submit_button("🌟 INSCRIBE ON THE GENESIS LAYER",type="primary",use_container_width=True)

    if ok_sub:
        if not cn.strip():
            st.error("Every great creation must bear a name, Young Sovereign.")
        else:
            with st.spinner("Inscribing your creation on the Genesis Layer…"):
                try:
                    aid=generate_id(cn,user)
                    fp=""
                    if uf is not None:
                        sfn=(uf.name.encode("ascii","ignore").decode("ascii").replace(" ","_"))
                        dest=f"{F['dir']}/{user}/{aid}_{sfn}"
                        with open(dest,"wb") as fh: fh.write(uf.getbuffer())
                        fp=dest
                    new_rec={
                        "id":aid,"name":cn.strip(),"sovereign":user,
                        "value":int(iv),"emoji":ep,"file_path":fp,
                        "created_at":datetime.now().isoformat(),
                        "is_fractional":False,"cert_downloaded":False,
                        "fraction_count":100,"listed_price":"","listed_at":"",
                    }
                    df_all=pd.concat([df_all,pd.DataFrame([new_rec])],ignore_index=True)
                    save_creations(df_all)
                    st.session_state["creations_df"]=df_all
                    run_quests(df_all,user)
                    st.balloons()
                    st.success(f"✦ **{cn}** inscribed! Genesis ID: `{aid}` · Value: **{int(iv):,} IMAGIX**")
                    if desc.strip(): st.info(f"📜 Lore sealed: *\"{desc.strip()[:120]}\"*")
                    st.rerun()
                except Exception as e:
                    st.error(f"Inscription failed: {e} — Contact the Keeper of the Genesis Layer.")


# ══════════════════════════════════════════════════════════════
# SIDEBAR — GENESIS TERMINAL v0.8
# ══════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(f"""
    <div style="text-align:center;padding:16px 0 8px;">
        <div style="font-family:'Cinzel',serif;color:{C['gold']};font-size:14px;font-weight:900;letter-spacing:3px;">◈ GENESIS TERMINAL</div>
        <div style="font-family:'DM Mono',monospace;color:{C['teal']};font-size:8px;letter-spacing:2px;margin-top:4px;opacity:.8;">v0.8 · SOVEREIGN INTERFACE</div>
    </div>""",unsafe_allow_html=True)
    st.divider()

    # Stats
    total_val_s=pd.to_numeric(user_df["value"],errors="coerce").fillna(0).sum() if not user_df.empty else 0
    for lbl,val in [
        ("YOUNG SOVEREIGN",user),
        ("AGE",f"{age} years" if dob else "Unknown"),
        ("RANK",rank["name"]),
        ("IMAGIX BALANCE",f"{total_imagix:,} 𝕀"),
        ("VAULT VALUE",f"{total_val_s:,.0f} 𝕀"),
        ("CREATIONS",str(len(user_df))),
        ("QUESTS DONE",f"{n_done} / {len(QUESTS)}"),
        ("TUTORS",f"{len(active_tutors)} available"),
        ("SESSION",datetime.now().strftime("%H:%M · %b %d")),
    ]:
        st.markdown(f"""<div class="term-block"><div class="term-key">{lbl}</div><div class="term-val">{val}</div></div>""",unsafe_allow_html=True)

    st.divider()
    if not rank["maxed"]:
        st.progress(rank["progress"])
        st.caption(f"{rank['next']-total_imagix:,} 𝕀 to next rank")
    else:
        st.progress(1.0); st.caption("👑 LEGEND — Maximum rank achieved")

    st.divider()

    # ── SPONSOR / PARENTAL MODE ────────────────────────────
    st.markdown(f"""<div style="font-family:'Cinzel',serif;color:{C['muted']};font-size:9px;letter-spacing:2px;margin-bottom:6px;">PARENTAL / SPONSOR MODE</div>""",unsafe_allow_html=True)
    parent_on=st.toggle("Enable Sponsor View",value=st.session_state["parent_mode"],key="parent_toggle",help="Sponsor/parent read-only dashboard.")
    st.session_state["parent_mode"]=parent_on

    if parent_on:
        if not st.session_state["sponsor_viewed"]:
            st.session_state["sponsor_viewed"]=True
            run_quests(df_all,user)

        df_u=load_users(); urow=df_u[df_u.kingdom==user]
        has_sponsor=(not urow.empty and str(urow.iloc[0].get("sponsor_kingdom","")).strip() not in ("","nan"))

        if has_sponsor:
            sp_k=str(urow.iloc[0]["sponsor_kingdom"])
            sp_pw_h=str(urow.iloc[0].get("sponsor_pw_hash",""))
            sponsor_input=st.text_input("Sponsor Password",type="password",key="sp_verify_pw",label_visibility="collapsed",placeholder="Sponsor password")
            if st.button("🔓 VERIFY SPONSOR",key="verify_sp",use_container_width=True):
                if hash_pw(sponsor_input)==sp_pw_h:
                    st.session_state["sponsor_ok"]=True
                    st.success(f"✦ Sponsor verified: {sp_k}")
                else:
                    st.error("Wrong sponsor password.")
        else:
            st.session_state["sponsor_ok"]=True  # No sponsor set — allow demo view

        if st.session_state.get("sponsor_ok"):
            n_cert_s=int(user_df["cert_downloaded"].astype(str).str.lower().isin(["true","1"]).sum()) if not user_df.empty else 0
            n_frac_s=int(user_df["is_fractional"].astype(str).str.lower().isin(["true","1"]).sum()) if not user_df.empty else 0
            n_listed=int((user_df["listed_price"].astype(str).str.strip().isin(["","nan"])==False).sum()) if not user_df.empty else 0
            for lbl,val in [
                ("Kingdom",user),("Rank",rank["name"]),
                ("Creations",str(len(user_df))),
                ("Portfolio",f"{total_val_s:,.0f} 𝕀"),
                ("Certs Issued",str(n_cert_s)),
                ("Fractionalised",str(n_frac_s)),
                ("Listed",str(n_listed)),
                ("IMAGIX",f"{total_imagix:,} 𝕀"),
                ("Quests",f"{n_done}/{len(QUESTS)}"),
            ]:
                st.markdown(f"""<div class="sponsor-row"><span class="sponsor-key">{lbl}</span><span class="sponsor-val">{val}</span></div>""",unsafe_allow_html=True)

            # Reset password section
            st.write("")
            with st.expander("🔑 Reset Kingdom Password"):
                new_pw=st.text_input("New Password",type="password",key="reset_pw_new")
                new_pw2=st.text_input("Confirm New Password",type="password",key="reset_pw2")
                if st.button("🔄 RESET PASSWORD",key="reset_pw_btn"):
                    if len(new_pw)<4: st.error("Password too short.")
                    elif new_pw!=new_pw2: st.error("Passwords don't match.")
                    else:
                        df_u.loc[df_u.kingdom==user,"pw_hash"]=hash_pw(new_pw)
                        save_users(df_u)
                        st.success("✦ Password reset by Sponsor.")

            st.markdown(f"""<div style="font-family:'DM Mono',monospace;color:{C['teal']};font-size:9px;margin-top:10px;line-height:1.8;opacity:.8;">✦ Read-only Sponsor view<br>✦ Trade approval gates · v0.9<br>✦ Activity log · v0.9</div>""",unsafe_allow_html=True)

    st.divider()
    st.caption("Delphia Genesis v0.8\nWhere Imagination Becomes Sovereign\n© Rey Delphi · Kardashev VI")


# ══════════════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════════════
st.divider()
st.caption("⬟ Delphia Genesis v0.8 — Where Imagination Becomes Sovereign · Genesis Layer · Kardashev Type VI ⬟")