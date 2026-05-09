"""
╔══════════════════════════════════════════════════════════════════════╗
║      DELPHIA GENESIS v0.9.2.1 — CLARITY & CONTROL · MICRO PATCH    ║
║                                                                      ║
║  Fixes: TITLE flash (no finally rerun) · Quest Banner HTML clean     ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import pandas as pd
import os, hashlib, io, math, base64, json, random, urllib.request
from datetime import datetime, date
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.colors import HexColor

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


# ══════════════════════════════════════════════════════════════════════
# ① DESIGN TOKENS
# ══════════════════════════════════════════════════════════════════════
C = {
    "space":   "#05121f",
    "celest":  "#0A2540",
    "card":    "#0d1f3a",
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
    "orange":  "#F39C12",
}

F = {
    "creations": "genesis_creations.csv",
    "quests":    "genesis_quests.csv",
    "wallets":   "genesis_wallets.csv",
    "users":     "genesis_users.csv",
    "market":    "genesis_market.csv",
    "activity":  "genesis_activity.csv",
    "dir":       "creations",
}

MINOR_AGE           = 18
SPONSOR_SESSION_KEY = "sponsor_verified_session"

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

EMOJI_PICKS = [
    "🌟","🐉","☁️","🤖","⚔️","🏰","🌙","🔮","🦋","🌊","🦅","🌸",
    "💎","🔥","⚡","🎨","🎭","🏆","🦁","🌺","🎪","🏺","🗝️","📜",
    "🌈","🦄","🐬","🌍","🚀","🎯","🎲","🧬","🔭","⚗️","🌋","🌌",
    "🐺","🦊","🐲","🌞","🎸","🎻","🏹","🗡️","🧿","🔱","⚜️","🌀",
]

DEMO_SHOWCASE = [
    ("Star Dragon Awakening",       48_200, "🐉"),
    ("Kingdom of Eternal Clouds",  125_000, "☁️"),
    ("The Brave Robot Friend",      32_800, "🤖"),
    ("Legendary Enchanted Sword",   67_500, "⚔️"),
    ("Floating Family Castle",      89_000, "🏰"),
    ("Crystal Phoenix Rising",      54_300, "🦅"),
]

# ── Activity action metadata ─────────────────────────────────────────
ACT_META = {
    "UPLOAD":      ("📤", "teal",   "New Creation"),
    "CERT_GEN":    ("📜", "gold",   "Certificate"),
    "SPLIT":       ("🔀", "purple", "Fractionalised"),
    "LIST":        ("🌠", "purple", "Listed"),
    "DELIST":      ("✕",  "muted",  "Delisted"),
    "BUY":         ("💰", "green",  "Purchased"),
    "QUESTS_DONE": ("⚡", "gold",   "Quest Done"),
    "LOGIN":       ("🔑", "teal",   "Login"),
    "REGISTER":    ("🌟", "gold",   "Registered"),
    "PWD_RESET":   ("🔑", "orange", "Password Reset"),
}


# ══════════════════════════════════════════════════════════════════════
# ② TUTORS v2
# ══════════════════════════════════════════════════════════════════════
TUTORS = [
    {
        "id":"delphito_bebito","name":"Delphito el Bebito","emoji":"🍼",
        "age_min":6,"age_max":9,"color":"#FFD1DC","short":"Bebito",
        "persona":(
            "Eres Delphito el Bebito, el amigo más alegre de los niños de 6-8 años en Delphia Genesis. "
            "Hablas de forma MUY simple. Usas emojis 🌟✨🎉🎈 y frases cortísimas. NUNCA uses palabras difíciles. Máximo 2-3 oraciones."
        ),
        "fallbacks":{
            "vault":"¡Wooow! 🌟 ¡Tienes cosas súper bonitas aquí! ¡Sigue guardando más! ✨",
            "upload":"¡Yay! 🎉 ¡Vas a poner algo nuevo! ¡Eso es lo mejor! ¡Hazlo ya! 🌈",
            "quests":"¡Mira cuántas medallas puedes ganar! ⭐ ¡Tú puedes atrapar todas! 🏆",
            "wallet":"¡Tienes muchos IMAGIX! 💰 ¡Eres muy rico! ¡Sigue así! 🌟",
            "market":"¡Aquí puedes ver cosas de otros amigos! 👀 ¡Qué emocionante! 🎪",
            "activity":"¡Mira todo lo que has hecho! 🎉 ¡Eres muy activo! ¡Sigue así! ⭐",
            "default":"¡Hola! 🌟 ¡Estás en el lugar más mágico del universo! ¡Juega y crea! ✨",
        },
    },
    {
        "id":"chispitas_junior","name":"Chispitas Jr.","emoji":"⚡",
        "age_min":7,"age_max":10,"color":"#FFF3CD","short":"Chispitas Jr.",
        "persona":(
            "Eres Chispitas Jr., tutora curiosa para niños de 7-10 años. "
            "Explicas con ejemplos de juguetes y superhéroes. Dices '¿Sabías que...?'. Máximo 3 oraciones."
        ),
        "fallbacks":{
            "vault":"¿Sabías que tu Vault es como un cofre del tesoro mágico? ⚡ ¡Cada creación que guardas brilla más!",
            "upload":"¡Es como ser un inventor! ⚡ Cuando subes una creación, queda guardada para SIEMPRE. ¡Qué poder!",
            "quests":"¡Las Quests son como misiones de superhéroe! ⚡ Completa cada una y ganarás IMAGIX. ¿Cuál atacas primero?",
            "wallet":"Tu Wallet es como una alcancía mágica ⚡ ¡Cada quest le mete más brillo!",
            "market":"¡El Marketplace es como una feria mágica! ⚡ ¡Fascinante!",
            "activity":"¡Tu historial de actividad es como el diario de un explorador! ⚡ ¡Cada línea es una aventura!",
            "default":"¡Bienvenido al Genesis Layer! ⚡ Es como un videojuego donde TÚ eres el héroe.",
        },
    },
    {
        "id":"delphita_pinga","name":"Delphita la Pinga","emoji":"🏃‍♀️",
        "age_min":9,"age_max":13,"color":"#C8F7C5","short":"Delphita",
        "persona":(
            "Eres Delphita la Pinga, tutora traviesa y energética para niños de 9-12 años. "
            "Usas '¡Boom!', '¡Épico!', '¡Sin límites!'. Lanzas mini-retos. Máximo 4 oraciones."
        ),
        "fallbacks":{
            "vault":"¡BOOM! 💥 Tu vault está tomando forma épica. ¿A que puedes añadir 2 más esta semana?",
            "upload":"¡Este es el momento! 🏃‍♀️ ¡Sube tu creación AHORA! ¡Épico!",
            "quests":"¡Tienes quests sin completar! 👀 ¿Vas a dejar pasar IMAGIX gratis? ¡Imposible!",
            "wallet":"¡Mira ese saldo! 💰 ¡Podría ser el doble! ¡Completa las quests y BOOM!",
            "market":"¡El Marketplace es un campo de batalla económica! 🏃‍♀️ ¡Lista y conquista!",
            "activity":"¡Mira tu historial de batallas épicas! 🏃‍♀️ ¡Cada acción cuenta, Soberano!",
            "default":"¡Oye, Soberano! 🏃‍♀️ ¿Qué estás esperando? ¡Boom!",
        },
    },
    {
        "id":"chispitas","name":"Chispitas","emoji":"🔬",
        "age_min":11,"age_max":14,"color":"#E8F4FD","short":"Chispitas",
        "persona":(
            "Eres Chispitas, tutora científica para jóvenes de 11-14 años. "
            "Conectas Delphia con economía y propiedad intelectual. Máximo 4 oraciones."
        ),
        "fallbacks":{
            "vault":"🔬 Tu Vault es un portafolio de activos creativos. Los artistas exitosos documentan cada obra.",
            "upload":"🔬 Registrar una creación es como patentar una idea. La documentación temprana es crucial.",
            "quests":"🔬 Las Quests son gamificación basada en hitos reales. Cada una desarrolla un hábito valioso.",
            "wallet":"🔬 El IMAGIX es moneda de mérito basada en acciones reales.",
            "market":"🔬 El Marketplace simula un mercado de activos creativos. ¿Qué precio refleja el valor real?",
            "activity":"🔬 Tu Activity Log es un registro de tus decisiones como creador. ¿Qué patrón ves?",
            "default":"🔬 El Genesis Layer combina economía conductual y creatividad. Fascinante.",
        },
    },
    {
        "id":"delphito_bonito","name":"Delphito el Bonito","emoji":"😎",
        "age_min":13,"age_max":16,"color":"#D0E8FF","short":"El Bonito",
        "persona":(
            "Eres Delphito el Bonito, tutor cool para adolescentes de 13-15 años. "
            "Usas 'no cap', 'real talk', 'main character energy'. Máximo 4 oraciones."
        ),
        "fallbacks":{
            "vault":"Real talk — tu Vault es tu portafolio. 😎 Main character energy, siempre.",
            "upload":"No cap — subir una creación es el move más inteligente hoy. 😎 Con estilo.",
            "quests":"Las Quests son free IMAGIX esperándote. 😎 Real talk — ignorarlas es dejar valor sobre la mesa.",
            "wallet":"Tu IMAGIX es el score de tu soberanía creativa. 😎 Sigue sumando.",
            "market":"El Marketplace es donde los creators serios juegan. 😎 Main character move.",
            "activity":"Tu Activity Log es el receipts de tu carrera como creator. 😎 Todo queda registrado.",
            "default":"Hey Soberano 😎 El Genesis Layer es tu canvas digital. Real talk.",
        },
    },
    {
        "id":"emperatriz_fenix","name":"Delphina la Emperatriz Fénix","emoji":"🦅",
        "age_min":15,"age_max":18,"color":"#E8D5FF","short":"Emperatriz",
        "persona":(
            "Eres Delphina la Emperatriz Fénix, mentora elegante para jóvenes de 15-17 años. "
            "Metáforas poderosas, referencias a arte y liderazgo. Máximo 5 oraciones."
        ),
        "fallbacks":{
            "vault":"🦅 Tu Vault es la primera página de tu legado creativo. Cada obra inscrita es un acto de soberanía.",
            "upload":"🦅 Crear y documentar una obra separa al artesano del artista. Inscribe con intención.",
            "quests":"🦅 Las Quests son el mapa de tu evolución. Los grandes imperios se construyen decision a decision.",
            "wallet":"🦅 El IMAGIX mide tu contribución. Que crezca es señal de que tu obra tiene impacto.",
            "market":"🦅 El Marketplace es el primer mercado de tu obra. Establece precios que reflejen tu visión.",
            "activity":"🦅 Tu historial de actividad es el pergamino de tu soberanía. Léelo con orgullo.",
            "default":"🦅 Bienvenida al Genesis Layer, Joven Soberana. Tu imaginación tiene peso y forma.",
        },
    },
    {
        "id":"rey_delphi","name":"Delphi, Rey de Delphia","emoji":"👑",
        "age_min":17,"age_max":120,"color":"#F2C94C","short":"Rey Delphi",
        "persona":(
            "Eres Delphi, Rey de Delphia — mentor supremo para jóvenes adultos de 17+ años. "
            "Profundidad filosófica, sabiduría Kardashev VI. Máximo 5 oraciones con peso."
        ),
        "fallbacks":{
            "vault":"👑 Tu Vault es el primer nodo de tu imperio creativo. En Kardashev VI, la imaginación documentada es el activo más escaso.",
            "upload":"👑 Registrar una creación es un acto de soberanía digital. Actúa ahora.",
            "quests":"👑 Las Quests mapean tu evolución. Cada hito entrena la disciplina que construye imperios.",
            "wallet":"👑 El IMAGIX es un proxy de tu impacto. La verdadera riqueza es crear valor que otros deseen.",
            "market":"👑 El Marketplace es donde tu visión encuentra la economía real. Actúa con estrategia.",
            "activity":"👑 Tu Activity Log es el registro de tus actos soberanos. Cada línea es historia del Genesis Layer.",
            "default":"👑 Soberano — el Genesis Layer es tu plataforma de soberanía creativa. Actúa con intención.",
        },
    },
]

def get_active_tutors(age: int) -> list:
    eligible = [t for t in TUTORS if t["age_min"] <= age <= t["age_max"]]
    return eligible[:2] if len(eligible) > 2 else eligible


# ══════════════════════════════════════════════════════════════════════
# ③ QUESTS CATALOG
# ══════════════════════════════════════════════════════════════════════
def _q_count(df, u):
    return len(df[df.sovereign == u]) if not df.empty and "sovereign" in df.columns else 0

def _q_has_img(df, u):
    udf = df[df.sovereign == u] if not df.empty and "sovereign" in df.columns else pd.DataFrame()
    return any(str(r.get("file_path","")).lower().endswith((".jpg",".jpeg",".png"))
               for r in udf.to_dict("records"))

def _q_max_val(df, u):
    udf = df[df.sovereign == u] if not df.empty and "sovereign" in df.columns else pd.DataFrame()
    if udf.empty: return 0
    return float(pd.to_numeric(udf["value"], errors="coerce").fillna(0).max())

def _q_has_split(df, u):
    udf = df[df.sovereign == u] if not df.empty and "sovereign" in df.columns else pd.DataFrame()
    if udf.empty: return False
    return bool(udf["is_fractional"].astype(str).str.lower().isin(["true","1"]).any())

def _q_today_upload(df, u):
    udf = df[df.sovereign == u] if not df.empty and "sovereign" in df.columns else pd.DataFrame()
    if udf.empty: return False
    t = date.today().isoformat()
    return any(str(r.get("created_at","")).startswith(t) for r in udf.to_dict("records"))

def _q_has_listing(df, u):
    udf = df[df.sovereign == u] if not df.empty and "sovereign" in df.columns else pd.DataFrame()
    if udf.empty: return False
    return bool((udf["listed_price"].astype(str).str.strip().isin(["","nan","0"]) == False).any())

QUESTS = [
    {"id":"q_born",    "title":"Sovereign Born",      "desc":"Enter the Genesis Layer for the first time.",       "reward":1_000,  "icon":"🌅","cat":"Onboarding", "check": lambda df,u,ss: True},
    {"id":"q_first",   "title":"First Genesis",       "desc":"Register your very first creation.",                "reward":5_000,  "icon":"🌱","cat":"Onboarding", "check": lambda df,u,ss: _q_count(df,u)>=1},
    {"id":"q_img",     "title":"Visual Sovereign",    "desc":"Upload a creation with an image file.",             "reward":4_000,  "icon":"🖼️","cat":"Creation",   "check": lambda df,u,ss: _q_has_img(df,u)},
    {"id":"q_million", "title":"Million Imaginer",    "desc":"Register a creation worth >= 1,000,000 IMAGIX.",    "reward":25_000, "icon":"💎","cat":"Creation",   "check": lambda df,u,ss: _q_max_val(df,u)>=1_000_000},
    {"id":"q_lore",    "title":"Lorekeeper",          "desc":"Add a lore description to a creation.",            "reward":2_000,  "icon":"📖","cat":"Creation",   "check": lambda df,u,ss: ss.get("lore_added",False)},
    {"id":"q_three",   "title":"Trilogy of Wonders",  "desc":"Bring 3 creations to the Genesis Layer.",          "reward":12_000, "icon":"🎨","cat":"Collection", "check": lambda df,u,ss: _q_count(df,u)>=3},
    {"id":"q_five",    "title":"Hand of Wonders",     "desc":"Amass 5 creations.",                               "reward":18_000, "icon":"🖐","cat":"Collection", "check": lambda df,u,ss: _q_count(df,u)>=5},
    {"id":"q_ten",     "title":"Sovereign Gallery",   "desc":"Build a collection of 10 creations.",              "reward":30_000, "icon":"🏛️","cat":"Collection", "check": lambda df,u,ss: _q_count(df,u)>=10},
    {"id":"q_cert",    "title":"Sacred Title Claimed","desc":"Download a Genesis Certificate.",                   "reward":3_000,  "icon":"📜","cat":"Actions",    "check": lambda df,u,ss: ss.get("cert_ever",False)},
    {"id":"q_split",   "title":"Fractional Sovereign","desc":"Activate fractional ownership.",                    "reward":7_500,  "icon":"🔀","cat":"Actions",    "check": lambda df,u,ss: _q_has_split(df,u)},
    {"id":"q_list",    "title":"Open for Trade",      "desc":"List a creation in the Marketplace.",              "reward":8_000,  "icon":"🌠","cat":"Actions",    "check": lambda df,u,ss: _q_has_listing(df,u)},
    {"id":"q_sold",    "title":"First Trade",         "desc":"Sell a creation in the Marketplace.",              "reward":15_000, "icon":"🤝","cat":"Actions",    "check": lambda df,u,ss: ss.get("sold_ever",False)},
    {"id":"q_daily",   "title":"Daily Genesis",       "desc":"Upload a creation today.",                         "reward":2_500,  "icon":"☀️","cat":"Daily",      "check": lambda df,u,ss: _q_today_upload(df,u)},
    {"id":"q_tutor",   "title":"Wisdom Seeker",       "desc":"Consult a Genesis Tutor.",                         "reward":2_000,  "icon":"🧙","cat":"Daily",      "check": lambda df,u,ss: ss.get("tutor_used",False)},
    {"id":"q_deep_q",  "title":"Deep Thinker",        "desc":"Ask a Deep Question to a Tutor.",                  "reward":3_500,  "icon":"🔮","cat":"Daily",      "check": lambda df,u,ss: ss.get("deep_q_used",False)},
    {"id":"q_50k",     "title":"Golden Threshold",    "desc":"Accumulate 50,000 IMAGIX.",                        "reward":10_000, "icon":"💰","cat":"Wealth",     "check": lambda df,u,ss: ss.get("imagix",0)>=50_000},
    {"id":"q_bought",  "title":"First Acquisition",   "desc":"Purchase a creation from the Marketplace.",        "reward":12_000, "icon":"🛒","cat":"Wealth",     "check": lambda df,u,ss: ss.get("bought_ever",False)},
    {"id":"q_sponsor", "title":"Guardian Shield",     "desc":"A Sponsor is connected to your account.",          "reward":5_000,  "icon":"🛡️","cat":"Wealth",     "check": lambda df,u,ss: ss.get("has_sponsor",False)},
]


# ══════════════════════════════════════════════════════════════════════
# ④ PAGE CONFIG  — must be FIRST Streamlit call
# ══════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="DELPHIA GENESIS | IMAGINARIUM",
    page_icon="🌟",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ══════════════════════════════════════════════════════════════════════
# ⑤ THEME
# ══════════════════════════════════════════════════════════════════════
def inject_theme():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700;900&family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=DM+Mono:wght@300;400;500&display=swap');

    :root{{
        --space:{C['space']};--card:{C['card']};--card2:{C['card2']};
        --gold:{C['gold']};--gold2:{C['gold2']};--teal:{C['teal']};
        --purple:{C['purple']};--purple2:{C['purple2']};
        --muted:{C['muted']};--white:{C['white']};
    }}
    html,body,[data-testid="stAppViewContainer"]{{background:var(--space);color:var(--gold);}}
    .stApp{{
        background:
            radial-gradient(ellipse 80% 60% at 15% 10%,rgba(13,45,74,.9) 0%,transparent 70%),
            radial-gradient(ellipse 60% 50% at 85% 85%,rgba(10,31,53,.8) 0%,transparent 70%),
            linear-gradient(180deg,#060f1a 0%,var(--space) 100%);
    }}
    h1,h2,h3{{font-family:'Cinzel',serif!important;color:var(--gold)!important;letter-spacing:1px;}}
    p,li,span,div{{font-family:'DM Mono',monospace;}}
    label{{font-family:'DM Mono',monospace!important;color:var(--teal)!important;font-size:11px!important;}}

    /* ── Buttons ── */
    .stButton>button{{background:linear-gradient(135deg,var(--purple),var(--purple2));color:var(--gold);border:1px solid rgba(242,201,76,.45);border-radius:8px;font-family:'Cinzel',serif;font-size:10px;font-weight:700;letter-spacing:1.5px;padding:8px 14px;transition:all .22s ease;width:100%;}}
    .stButton>button:hover{{background:linear-gradient(135deg,var(--gold),var(--gold2));color:var(--space);border-color:var(--gold);box-shadow:0 0 18px rgba(242,201,76,.45),0 4px 16px rgba(0,0,0,.4);transform:translateY(-2px);}}
    .stButton>button[kind="primary"],[data-testid="stFormSubmitButton"]>button{{background:linear-gradient(135deg,var(--gold),var(--gold2))!important;color:var(--space)!important;font-size:12px;padding:11px 28px;border:none!important;box-shadow:0 4px 20px rgba(242,201,76,.3);}}
    [data-testid="stFormSubmitButton"]>button:hover{{background:linear-gradient(135deg,#ffe080,var(--gold))!important;color:var(--space)!important;}}
    .stDownloadButton>button{{background:linear-gradient(135deg,rgba(0,229,192,.12),rgba(0,229,192,.24))!important;color:var(--teal)!important;border:1px solid var(--teal)!important;font-family:'Cinzel',serif;font-size:10px;letter-spacing:1px;width:100%;transition:all .2s;}}
    .stDownloadButton>button:hover{{background:var(--teal)!important;color:var(--space)!important;}}

    /* ── Inputs ── */
    .stTextInput input,.stNumberInput input,.stTextArea textarea{{background-color:{C['card']}!important;color:var(--teal)!important;border:1px solid rgba(157,78,221,.6)!important;border-radius:8px!important;font-family:'DM Mono',monospace!important;font-size:13px!important;caret-color:var(--gold);}}
    .stTextInput input:focus,.stNumberInput input:focus,.stTextArea textarea:focus{{border-color:var(--gold)!important;box-shadow:0 0 0 2px rgba(242,201,76,.15)!important;}}
    .stTextInput input[type="password"]{{color:var(--gold)!important;letter-spacing:3px;}}
    .stSelectbox [data-baseweb="select"]>div{{background-color:{C['card']}!important;border:1px solid rgba(157,78,221,.6)!important;color:var(--teal)!important;font-family:'DM Mono',monospace!important;}}
    [data-testid="stDateInput"]>div>div>input{{background:{C['card']}!important;color:var(--teal)!important;border:1px solid rgba(157,78,221,.6)!important;}}

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"]{{background:transparent;border-bottom:1px solid rgba(157,78,221,.4);gap:2px;flex-wrap:wrap;}}
    .stTabs [data-baseweb="tab"]{{font-family:'Cinzel',serif;font-size:10px;letter-spacing:1px;color:var(--muted);padding:8px 13px;border-radius:8px 8px 0 0;border:1px solid transparent;border-bottom:none;transition:all .2s;}}
    .stTabs [data-baseweb="tab"]:hover{{color:var(--gold);background:rgba(242,201,76,.05);}}
    .stTabs [aria-selected="true"]{{background:var(--card2)!important;color:var(--gold)!important;border-color:rgba(0,229,192,.5)!important;border-bottom:1px solid var(--card2)!important;}}

    /* ── Metrics ── */
    [data-testid="metric-container"]{{background:linear-gradient(135deg,{C['card']},{C['card2']});border:1px solid rgba(157,78,221,.5);border-radius:12px;padding:12px 18px;transition:border-color .2s;}}
    [data-testid="metric-container"]:hover{{border-color:var(--gold);}}
    [data-testid="metric-container"] label{{color:var(--teal)!important;font-family:'Cinzel',serif!important;font-size:9px!important;letter-spacing:2px!important;text-transform:uppercase;}}
    [data-testid="stMetricValue"]{{color:var(--gold)!important;font-family:'Cinzel',serif!important;font-weight:700!important;}}

    /* ── Sidebar ── */
    [data-testid="stSidebar"]{{background:linear-gradient(180deg,#080f1e 0%,#0a1628 60%,{C['space']} 100%);border-right:1px solid rgba(157,78,221,.4);}}
    [data-testid="stSidebar"] section{{padding-top:0;}}

    /* ── Progress bar ── */
    .stProgress>div>div>div>div{{
        background:linear-gradient(90deg,#9D4EDD 0%,#4facfe 25%,#00E5C0 50%,#43e97b 75%,#F2C94C 100%);
        border-radius:4px;
        transition:width .4s ease;
    }}
    .stProgress>div>div{{background:rgba(255,255,255,.06);border-radius:4px;}}

    /* ── Alerts ── */
    .stSuccess>div{{background:rgba(46,204,113,.1)!important;border:1px solid rgba(46,204,113,.4)!important;color:{C['green']}!important;font-family:'DM Mono',monospace!important;border-radius:10px!important;}}
    .stInfo>div{{background:rgba(0,229,192,.08)!important;border:1px solid rgba(0,229,192,.35)!important;color:var(--teal)!important;font-family:'DM Mono',monospace!important;border-radius:10px!important;}}
    .stWarning>div{{background:rgba(242,201,76,.08)!important;border:1px solid rgba(242,201,76,.35)!important;color:var(--gold)!important;border-radius:10px!important;}}
    .stError>div{{background:rgba(255,107,107,.1)!important;border:1px solid rgba(255,107,107,.4)!important;color:{C['danger']}!important;border-radius:10px!important;}}
    [data-testid="stFileUploader"]>div{{background:{C['card']}!important;border:2px dashed rgba(157,78,221,.5)!important;border-radius:14px!important;}}
    [data-testid="stFileUploader"]>div:hover{{border-color:var(--gold)!important;}}

    hr{{border-color:rgba(157,78,221,.25)!important;margin:12px 0;}}
    ::-webkit-scrollbar{{width:5px;height:5px;}}
    ::-webkit-scrollbar-track{{background:transparent;}}
    ::-webkit-scrollbar-thumb{{background:rgba(157,78,221,.5);border-radius:3px;}}
    .stCaption{{color:var(--muted)!important;font-size:10.5px!important;}}
    .stMarkdown{{color:var(--muted);}}
    .stMarkdown strong{{color:var(--gold)!important;}}
    .stMarkdown code{{background:rgba(0,229,192,.1)!important;color:var(--teal)!important;border:1px solid rgba(0,229,192,.2)!important;border-radius:4px;font-size:11px;}}

    /* ═══ CUSTOM COMPONENTS ═══════════════════════════════════════ */

    /* ── Genesis Card ── */
    .g-card{{background:linear-gradient(145deg,{C['card']},{C['card2']});border:1px solid rgba(0,229,192,.28);border-radius:14px;overflow:hidden;transition:all .28s cubic-bezier(.4,0,.2,1);position:relative;margin-bottom:8px;}}
    .g-card:hover{{border-color:var(--gold);box-shadow:0 0 0 1px rgba(242,201,76,.15),0 8px 32px rgba(0,0,0,.5),0 0 40px rgba(242,201,76,.12);transform:translateY(-4px) scale(1.01);}}
    .g-card-img{{height:130px;background:linear-gradient(135deg,{C['celest']},#142f55);display:flex;align-items:center;justify-content:center;font-size:56px;border-bottom:1px solid rgba(0,229,192,.15);position:relative;overflow:hidden;}}
    .g-card-img::after{{content:'';position:absolute;inset:0;background:radial-gradient(ellipse at 50% 80%,rgba(157,78,221,.1) 0%,transparent 70%);pointer-events:none;}}
    .g-card-body{{padding:10px 13px 12px;}}
    .g-card-title{{font-family:'Playfair Display',serif;color:#dde8ff;font-size:12.5px;font-weight:700;line-height:1.35;min-height:32px;margin-bottom:4px;}}
    .g-card-value{{font-family:'Cinzel',serif;color:var(--gold);font-size:14px;font-weight:700;}}
    .g-card-id{{font-family:'DM Mono',monospace;color:var(--teal);font-size:8px;opacity:.6;margin-top:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}}
    .g-badge-gold{{position:absolute;top:8px;right:8px;background:rgba(5,18,31,.9);border:1px solid var(--gold);border-radius:20px;padding:2px 9px;font-family:'Cinzel',serif;font-size:7.5px;color:var(--gold);letter-spacing:1px;}}
    .g-badge-teal{{position:absolute;bottom:8px;left:8px;background:rgba(0,229,192,.15);border:1px solid var(--teal);border-radius:20px;padding:2px 8px;font-family:'Cinzel',serif;font-size:7px;color:var(--teal);}}
    .g-badge-purple{{position:absolute;top:8px;left:8px;background:rgba(157,78,221,.25);border:1px solid var(--purple);border-radius:20px;padding:2px 8px;font-family:'Cinzel',serif;font-size:7px;color:#cc99ff;}}
    .g-cert-ready{{position:absolute;top:8px;right:8px;background:rgba(0,229,192,.15);border:1px solid var(--teal);border-radius:20px;padding:2px 9px;font-family:'Cinzel',serif;font-size:7px;color:var(--teal);letter-spacing:1px;}}

    /* ── Hero ── */
    .g-hero{{background:linear-gradient(135deg,#0b1d35 0%,#15284a 50%,#0a1827 100%);border:1px solid rgba(157,78,221,.5);border-radius:18px;padding:32px 40px;text-align:center;position:relative;overflow:hidden;margin-bottom:8px;}}
    .g-hero::before{{content:'';position:absolute;top:-60%;left:50%;transform:translateX(-50%);width:120%;height:120%;background:radial-gradient(ellipse,rgba(157,78,221,.1) 0%,transparent 65%);pointer-events:none;}}
    .g-hero-title{{font-family:'Cinzel',serif;font-size:clamp(20px,3vw,30px);font-weight:900;color:var(--gold);letter-spacing:5px;margin:0;text-shadow:0 0 30px rgba(242,201,76,.3);}}
    .g-hero-sub{{font-family:'DM Mono',monospace;color:var(--teal);font-size:11px;letter-spacing:3px;margin-top:8px;opacity:.9;}}

    /* ── Quest Card ── */
    .q-card{{background:linear-gradient(135deg,{C['card']},{C['card2']});border:1px solid rgba(157,78,221,.4);border-radius:12px;padding:13px 16px;margin-bottom:9px;display:flex;align-items:center;gap:13px;transition:all .2s;position:relative;}}
    .q-card:hover{{border-color:rgba(242,201,76,.4);transform:translateX(3px);}}
    .q-card.done{{border-color:rgba(0,229,192,.4);background:linear-gradient(135deg,rgba(0,229,192,.04),rgba(0,229,192,.02));}}
    .q-card.done::after{{content:'✓';position:absolute;right:14px;top:50%;transform:translateY(-50%);color:var(--teal);font-size:18px;font-weight:700;}}
    .q-icon{{font-size:24px;min-width:32px;text-align:center;}}
    .q-info{{flex:1;}}
    .q-title{{font-family:'Cinzel',serif;color:var(--gold);font-size:12px;font-weight:700;margin-bottom:2px;}}
    .q-desc{{font-family:'DM Mono',monospace;color:var(--muted);font-size:10px;line-height:1.4;}}
    .q-reward{{font-family:'Cinzel',serif;color:var(--teal);font-size:12px;font-weight:700;white-space:nowrap;margin-right:26px;}}

    /* ── Rank ── */
    .rank-pill{{background:linear-gradient(135deg,{C['card']},#1c3560);border:2px solid var(--gold);border-radius:50px;padding:7px 22px;display:inline-block;font-family:'Cinzel',serif;color:var(--gold);font-size:13px;font-weight:700;letter-spacing:2px;box-shadow:0 0 20px rgba(242,201,76,.18),inset 0 0 10px rgba(242,201,76,.05);}}

    /* ── Wallet ── */
    .wallet-card{{background:linear-gradient(145deg,#0a1e38,#0d2540);border:2px solid rgba(242,201,76,.5);border-radius:16px;padding:24px;text-align:center;position:relative;overflow:hidden;margin-bottom:16px;}}
    .wallet-card::before{{content:'';position:absolute;top:-40%;left:50%;transform:translateX(-50%);width:80%;height:80%;background:radial-gradient(ellipse,rgba(242,201,76,.06) 0%,transparent 70%);}}
    .wallet-amount{{font-family:'Cinzel',serif;color:var(--gold);font-size:clamp(22px,4vw,36px);font-weight:900;letter-spacing:2px;text-shadow:0 0 20px rgba(242,201,76,.4);}}
    .wallet-label{{font-family:'DM Mono',monospace;color:var(--teal);font-size:10px;letter-spacing:3px;margin-top:4px;opacity:.85;}}

    /* ── Tutor bubble ── */
    .tutor-chat{{background:linear-gradient(135deg,rgba(13,30,60,.96),rgba(16,40,72,.96));border:1px solid rgba(0,229,192,.3);border-radius:16px;padding:18px 22px;margin:10px 0 4px;position:relative;}}
    .tutor-chat::before{{content:'';position:absolute;top:-7px;left:30px;width:13px;height:13px;background:{C['card']};border-left:1px solid rgba(0,229,192,.3);border-top:1px solid rgba(0,229,192,.3);transform:rotate(45deg);}}
    .tutor-name{{font-family:'Cinzel',serif;font-size:12px;font-weight:700;margin-bottom:8px;}}
    .tutor-msg{{font-family:'DM Mono',monospace;font-size:12px;color:#ccd6f0;line-height:1.75;}}

    /* ── Marketplace ── */
    .mkt-row{{background:linear-gradient(145deg,{C['card']},{C['card2']});border:1px solid rgba(157,78,221,.32);border-radius:12px;padding:14px 16px;margin-bottom:10px;display:flex;align-items:center;gap:14px;transition:all .2s;}}
    .mkt-row:hover{{border-color:rgba(242,201,76,.4);box-shadow:0 4px 20px rgba(0,0,0,.3);}}
    .mkt-emoji{{font-size:30px;min-width:38px;text-align:center;}}
    .mkt-name{{font-family:'Playfair Display',serif;color:#dde8ff;font-size:13px;font-weight:700;}}
    .mkt-seller{{font-family:'DM Mono',monospace;color:var(--muted);font-size:10px;margin-top:2px;}}
    .mkt-price{{font-family:'Cinzel',serif;color:var(--gold);font-size:15px;font-weight:700;white-space:nowrap;}}

    /* ── Buy success panel ── */
    .buy-success{{background:linear-gradient(135deg,rgba(46,204,113,.08),rgba(0,229,192,.06));border:1px solid rgba(46,204,113,.4);border-radius:14px;padding:20px 24px;margin:12px 0;}}
    .buy-success-title{{font-family:'Cinzel',serif;color:{C['green']};font-size:14px;font-weight:700;margin-bottom:12px;}}
    .buy-detail-row{{display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid rgba(46,204,113,.1);}}
    .buy-detail-key{{font-family:'DM Mono',monospace;color:var(--muted);font-size:10px;}}
    .buy-detail-val{{font-family:'Cinzel',serif;color:{C['green']};font-size:10px;font-weight:700;}}

    /* ── Quest completion banner ── */
    .quest-banner{{background:linear-gradient(135deg,rgba(242,201,76,.1),rgba(157,78,221,.08));border:1px solid rgba(242,201,76,.4);border-radius:14px;padding:16px 20px;margin-bottom:16px;}}
    .quest-banner-header{{font-family:'Cinzel',serif;color:{C['gold']};font-size:13px;font-weight:700;margin-bottom:10px;}}
    .quest-banner-total{{color:{C['teal']};}}
    .quest-row{{display:flex;align-items:center;gap:10px;padding:5px 0;border-bottom:1px solid rgba(242,201,76,.08);}}
    .quest-row:last-child{{border-bottom:none;}}
    .quest-row-icon{{font-size:16px;min-width:22px;}}
    .quest-row-name{{font-family:'DM Mono',monospace;color:#ccd6f0;font-size:11px;flex:1;}}
    .quest-row-reward{{font-family:'Cinzel',serif;color:{C['teal']};font-size:11px;font-weight:700;white-space:nowrap;}}

    /* ── Activity Log ── */
    .act-item{{display:flex;align-items:flex-start;gap:12px;padding:10px 0;border-bottom:1px solid rgba(157,78,221,.15);transition:background .15s;}}
    .act-item:hover{{background:rgba(157,78,221,.04);border-radius:8px;padding-left:6px;}}
    .act-icon{{font-size:18px;min-width:26px;text-align:center;margin-top:2px;}}
    .act-info{{flex:1;}}
    .act-action{{font-family:'Cinzel',serif;font-size:11px;font-weight:700;}}
    .act-detail{{font-family:'DM Mono',monospace;color:var(--muted);font-size:10px;margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:340px;}}
    .act-time{{font-family:'DM Mono',monospace;color:var(--muted);font-size:9px;white-space:nowrap;opacity:.7;text-align:right;min-width:80px;}}

    /* ── Terminal ── */
    .term-block{{background:rgba(0,0,0,.25);border:1px solid rgba(0,229,192,.14);border-radius:10px;padding:10px 13px;margin:5px 0;}}
    .term-key{{font-size:8px;color:{C['teal']};letter-spacing:1.5px;text-transform:uppercase;opacity:.8;}}
    .term-val{{font-family:'Cinzel',serif;color:{C['gold']};font-size:12px;font-weight:700;margin-top:1px;}}

    /* ── Sponsor ── */
    .sp-row{{display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid rgba(157,78,221,.15);}}
    .sp-key{{font-family:'DM Mono',monospace;color:{C['muted']};font-size:9px;}}
    .sp-val{{font-family:'Cinzel',serif;color:{C['gold']};font-size:10px;font-weight:700;}}

    /* ── Shimmer ── */
    @keyframes shimmer{{0%{{background-position:-200% center;}}100%{{background-position:200% center;}}}}
    .showcase-glow{{background:linear-gradient(90deg,transparent 0%,rgba(242,201,76,.06) 30%,rgba(0,229,192,.06) 50%,rgba(242,201,76,.06) 70%,transparent 100%);background-size:200% auto;animation:shimmer 4s linear infinite;border-radius:14px;}}

    /* ── Deep Q button ── */
    .deep-q-btn .stButton>button{{background:linear-gradient(135deg,rgba(243,156,18,.15),rgba(243,156,18,.08))!important;border:1px solid rgba(243,156,18,.6)!important;color:{C['orange']}!important;font-size:9px!important;}}
    .deep-q-btn .stButton>button:hover{{background:linear-gradient(135deg,rgba(243,156,18,.35),rgba(243,156,18,.2))!important;color:{C['white']}!important;border-color:{C['orange']}!important;}}

    /* ── Ledger ── */
    .ledger-table{{width:100%;border-collapse:collapse;background:linear-gradient(135deg,{C['card']},{C['card2']});border:1px solid rgba(157,78,221,.3);border-radius:12px;overflow:hidden;}}
    .ledger-table th{{padding:10px 14px;font-family:'Cinzel',serif;font-size:8.5px;color:{C['teal']};letter-spacing:2px;text-align:left;border-bottom:1px solid rgba(157,78,221,.4);}}
    .ledger-table td{{padding:9px 14px;font-family:'DM Mono',monospace;font-size:11px;border-bottom:1px solid rgba(157,78,221,.12);}}
    .ledger-cat{{background:rgba(157,78,221,.1);padding:6px 14px;font-family:'Cinzel',serif;font-size:8px;color:{C['purple']};letter-spacing:2px;text-transform:uppercase;}}

    /* ── Mobile ── */
    @media(max-width:768px){{.g-hero{{padding:20px 16px;}}.g-hero-title{{font-size:18px;letter-spacing:2px;}}.g-card-img{{height:100px;font-size:44px;}}.q-card{{flex-wrap:wrap;}}.q-reward{{margin-right:0;}}}}
    </style>
    """, unsafe_allow_html=True)

inject_theme()


# ══════════════════════════════════════════════════════════════════════
# ⑥ DATA LAYER
# ══════════════════════════════════════════════════════════════════════
CREATION_COLS = ["id","name","sovereign","value","emoji","file_path",
                 "created_at","is_fractional","cert_downloaded","fraction_count",
                 "listed_price","listed_at","lore"]
USER_COLS     = ["kingdom","pw_hash","dob","sponsor_kingdom","sponsor_pw_hash"]
MARKET_COLS   = ["id","name","sovereign","value","emoji","listed_price","listed_at"]
ACTIVITY_COLS = ["ts","sovereign","action","detail"]

def ensure_dirs(user: str):
    Path(F["dir"]).mkdir(exist_ok=True)
    Path(f"{F['dir']}/{user}").mkdir(parents=True, exist_ok=True)

def _read(path: str, cols: list) -> pd.DataFrame:
    if os.path.exists(path):
        try:
            df = pd.read_csv(path, dtype=str).fillna("")
            for c in cols:
                if c not in df.columns: df[c] = ""
            return df
        except Exception: pass
    return pd.DataFrame(columns=cols)

def _write(df: pd.DataFrame, path: str):
    try: df.to_csv(path, index=False)
    except Exception as e: st.toast(f"⚠️ Save error: {e}", icon="⚠️")

def load_creations() -> pd.DataFrame: return _read(F["creations"], CREATION_COLS)
def save_creations(df):               _write(df, F["creations"])
def load_market()    -> pd.DataFrame: return _read(F["market"],    MARKET_COLS)
def save_market(df):                  _write(df, F["market"])
def load_users()     -> pd.DataFrame: return _read(F["users"],     USER_COLS)
def save_users(df):                   _write(df, F["users"])

def load_wallet(user: str) -> int:
    df = _read(F["wallets"], ["sovereign","imagix"])
    row = df[df.sovereign == user]
    if not row.empty:
        try: return int(float(str(row.iloc[0]["imagix"])))
        except: pass
    return 0

def save_wallet(user: str, imagix: int):
    df = _read(F["wallets"], ["sovereign","imagix"])
    if user in df.sovereign.values:
        df.loc[df.sovereign == user, "imagix"] = str(imagix)
    else:
        df = pd.concat([df, pd.DataFrame([{"sovereign":user,"imagix":str(imagix)}])], ignore_index=True)
    _write(df, F["wallets"])

def load_quests_done(user: str) -> set:
    df  = _read(F["quests"], ["sovereign","completed_ids"])
    row = df[df.sovereign == user]
    if not row.empty:
        raw = str(row.iloc[0]["completed_ids"])
        return {x for x in raw.split(",") if x.strip()}
    return set()

def save_quests_done(user: str, done: set):
    df  = _read(F["quests"], ["sovereign","completed_ids"])
    val = ",".join(sorted(done))
    if user in df.sovereign.values:
        df.loc[df.sovereign == user, "completed_ids"] = val
    else:
        df = pd.concat([df, pd.DataFrame([{"sovereign":user,"completed_ids":val}])], ignore_index=True)
    _write(df, F["quests"])

def log_activity(sovereign: str, action: str, detail: str = ""):
    row = {"ts": datetime.now().isoformat(), "sovereign": sovereign, "action": action, "detail": detail}
    df  = _read(F["activity"], ACTIVITY_COLS)
    df  = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    _write(df.tail(500), F["activity"])

def load_activity(user: str, n: int = 20) -> list:
    """Load last N activity events for a user, newest first."""
    df = _read(F["activity"], ACTIVITY_COLS)
    if df.empty: return []
    udf = df[df.sovereign == user].copy()
    if udf.empty: return []
    udf = udf.sort_values("ts", ascending=False).head(n)
    return udf.to_dict("records")

def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

def register_user(kingdom, pw, dob_str, sponsor="", sponsor_pw="") -> tuple:
    df = load_users()
    if kingdom in df.kingdom.values: return False, "Kingdom name already taken."
    new = {"kingdom":kingdom,"pw_hash":hash_pw(pw),"dob":dob_str,
           "sponsor_kingdom":sponsor,"sponsor_pw_hash":hash_pw(sponsor_pw) if sponsor_pw else ""}
    df = pd.concat([df, pd.DataFrame([new])], ignore_index=True)
    save_users(df)
    log_activity(kingdom, "REGISTER", f"DOB={dob_str} sponsor={bool(sponsor)}")
    return True, "Registered!"

def verify_user(kingdom, pw) -> tuple:
    df  = load_users()
    row = df[df.kingdom == kingdom]
    if row.empty: return False, "Kingdom not found."
    if row.iloc[0]["pw_hash"] != hash_pw(pw): return False, "Wrong password."
    return True, ""

def get_user_row(kingdom) -> dict | None:
    df  = load_users()
    row = df[df.kingdom == kingdom]
    return row.iloc[0].to_dict() if not row.empty else None

def get_user_dob(kingdom) -> date | None:
    urow = get_user_row(kingdom)
    if urow:
        try: return datetime.strptime(str(urow["dob"]), "%Y-%m-%d").date()
        except: pass
    return None

def calc_age(dob: date | None) -> int:
    if not dob: return 99
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

def generate_id(name: str, sovereign: str) -> str:
    raw = f"{name}::{sovereign}::{datetime.now().isoformat()}"
    return "GEN-" + hashlib.sha256(raw.encode()).hexdigest()[:8].upper()

def safe_int(val, default: int = 0) -> int:
    try:
        s = str(val).replace(",","").strip()
        return int(float(s)) if s not in ("","nan","None") else default
    except (ValueError, TypeError): return default

def img_to_b64(path: str) -> str | None:
    """Convert image file to base64 data-URI. Returns None on any failure."""
    try:
        if not path or not os.path.exists(path): return None
        if not path.lower().endswith((".jpg",".jpeg",".png")): return None
        with open(path,"rb") as f: data = base64.b64encode(f.read()).decode()
        ext  = Path(path).suffix.lower().lstrip(".")
        mime = {"jpg":"jpeg","jpeg":"jpeg","png":"png"}.get(ext,"jpeg")
        return f"data:image/{mime};base64,{data}"
    except Exception: return None


# ══════════════════════════════════════════════════════════════════════
# ⑦ RANK ENGINE
# ══════════════════════════════════════════════════════════════════════
def get_rank(imagix: int) -> dict:
    name, curr = RANK_TIERS[0][1], 0
    nxt = RANK_TIERS[1][0]
    for i,(t,n,_) in enumerate(RANK_TIERS):
        if imagix >= t:
            name,curr = n,t
            nxt = RANK_TIERS[i+1][0] if i+1<len(RANK_TIERS) else t
    span = nxt-curr
    prog = min((imagix-curr)/span,1.0) if span>0 else 1.0
    return {"name":name,"progress":prog,"curr":curr,"next":nxt,"maxed":nxt==curr}


# ══════════════════════════════════════════════════════════════════════
# ⑧ QUEST ENGINE — idempotent, banner-based notifications
# ══════════════════════════════════════════════════════════════════════
def run_quests(df: pd.DataFrame, user: str) -> int:
    ss_extra = {
        "imagix":      st.session_state.get("imagix",0),
        "cert_ever":   st.session_state.get("cert_ever",False),
        "tutor_used":  st.session_state.get("tutor_used",False),
        "deep_q_used": st.session_state.get("deep_q_used",False),
        "sold_ever":   st.session_state.get("sold_ever",False),
        "bought_ever": st.session_state.get("bought_ever",False),
        "lore_added":  st.session_state.get("lore_added",False),
        "has_sponsor": st.session_state.get("has_sponsor",False),
    }
    done  = st.session_state["quest_completed"]
    newly = []
    delta = 0

    for q in QUESTS:
        if q["id"] in done: continue
        try:
            if q["check"](df, user, ss_extra):
                done.add(q["id"])
                st.session_state["imagix"] += q["reward"]
                delta += q["reward"]
                newly.append(q)
        except Exception: pass

    if newly:
        st.session_state["quest_completed"] = done
        save_quests_done(user, done)
        save_wallet(user, st.session_state["imagix"])
        existing = st.session_state.get("quest_banner", [])
        st.session_state["quest_banner"] = existing + newly
        log_activity(user, "QUESTS_DONE", str([q["id"] for q in newly]))

    return delta


# ══════════════════════════════════════════════════════════════════════
# ⑨ QUEST BANNER — v0.9.2.1 FIX: clean HTML, no raw-tag bleed
# ══════════════════════════════════════════════════════════════════════
def render_quest_banner():
    """
    v0.9.2.1 FIX: Renders quest completion banner using st.container()
    with separate st.markdown calls — avoids HTML parse issues that caused
    raw tag display in v0.9.2.
    """
    banner_quests = st.session_state.get("quest_banner", [])
    if not banner_quests:
        return

    total_reward = sum(q["reward"] for q in banner_quests)
    count        = len(banner_quests)
    header_text  = "Quest Completed!" if count == 1 else f"{count} Quests Completed!"

    # Build quest rows HTML safely — plain ASCII tags, no nested f-strings
    rows_parts = []
    for q in banner_quests:
        icon   = q.get("icon", "⚡")
        title  = q.get("title", "")
        reward = q.get("reward", 0)
        rows_parts.append(
            '<div class="quest-row">'
            f'<span class="quest-row-icon">{icon}</span>'
            f'<span class="quest-row-name">{title}</span>'
            f'<span class="quest-row-reward">+{reward:,} &#120128;</span>'
            '</div>'
        )
    rows_html = "\n".join(rows_parts)

    banner_html = (
        '<div class="quest-banner">'
        '<div class="quest-banner-header">'
        '&#9889; ' + header_text
        '&nbsp;&middot;&nbsp;'
        f'<span class="quest-banner-total">+{total_reward:,} IMAGIX earned</span>'
        '</div>'
        f'{rows_html}'
        '</div>'
    )

    st.markdown(banner_html, unsafe_allow_html=True)

    if st.button("✕ Dismiss", key="dismiss_banner"):
        st.session_state["quest_banner"] = []
        st.rerun()


# ══════════════════════════════════════════════════════════════════════
# ⑩ TUTORS — API + rich fallbacks
# ══════════════════════════════════════════════════════════════════════
def call_claude(prompt: str, max_tokens: int = 300) -> str | None:
    try:
        payload = json.dumps({
            "model": "claude-sonnet-4-20250514",
            "max_tokens": max_tokens,
            "messages": [{"role":"user","content":prompt}],
        }).encode()
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=payload,
            headers={"Content-Type":"application/json","anthropic-version":"2023-06-01"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            return data["content"][0]["text"].strip()
    except Exception: return None

def get_tutor_message(tutor: dict, context_tab: str, user: str, df: pd.DataFrame) -> str:
    n_c    = _q_count(df, user)
    imagix = st.session_state.get("imagix", 0)
    n_q    = len(st.session_state.get("quest_completed", set()))
    ctx_map = {
        "vault":    f"El usuario ve su Vault con {n_c} creaciones.",
        "upload":   "El usuario está en la pantalla de subir una nueva creación.",
        "quests":   f"El usuario ve sus Quests. Lleva {n_q} completadas.",
        "wallet":   f"El usuario ve su Wallet con {imagix:,} IMAGIX.",
        "market":   "El usuario explora el Marketplace.",
        "activity": f"El usuario ve su historial de actividad en Delphia Genesis.",
        "default":  f"El usuario {user} explora Delphia Genesis.",
    }
    prompt = (
        f"{tutor['persona']}\n\n"
        f"CONTEXTO: {ctx_map.get(context_tab, ctx_map['default'])}\n"
        f"USUARIO: '{user}' · {n_c} creaciones · {imagix:,} IMAGIX · {n_q} quests.\n"
        f"Da UN mensaje corto en tu voz. Específico al contexto. Sin asteriscos. Solo el mensaje."
    )
    return call_claude(prompt) or tutor["fallbacks"].get(context_tab, tutor["fallbacks"]["default"])

def get_deep_answer(tutor: dict, question: str, user: str, df: pd.DataFrame) -> str:
    n_c    = _q_count(df, user)
    imagix = st.session_state.get("imagix", 0)
    prompt = (
        f"{tutor['persona']}\n\n"
        f"El usuario {user} ({n_c} creaciones, {imagix:,} IMAGIX) pregunta:\n'{question}'\n\n"
        f"Responde en tu voz. Máximo 6 oraciones. Sin asteriscos. Solo la respuesta."
    )
    return (call_claude(prompt, max_tokens=500)
            or f"Esa es una pregunta fascinante, Soberano {user}. "
               "En el Genesis Layer, cada creación lleva el peso de la imaginación que la originó. "
               "Reflexiona — esa es la verdadera sabiduría.")


# ══════════════════════════════════════════════════════════════════════
# ⑪ PDF CERTIFICATE
# ══════════════════════════════════════════════════════════════════════
def make_certificate(name: str, asset_id: str, sovereign: str, value: int) -> bytes:
    buf  = io.BytesIO()
    W, H = A4
    c    = rl_canvas.Canvas(buf, pagesize=A4)
    c.setTitle(f"Genesis Certificate · {name}")

    c.setFillColor(HexColor("#04101e")); c.rect(0,0,W,H,fill=1,stroke=0)
    rng = random.Random(42)
    for _ in range(120):
        sx,sy = rng.uniform(22,W-22),rng.uniform(55,H-55)
        c.setFillColorRGB(1,1,1,alpha=rng.uniform(.07,.42))
        c.circle(sx,sy,rng.uniform(.25,1.2),fill=1,stroke=0)
    for r,a in [(220,.022),(150,.042),(90,.07),(50,.058),(28,.048)]:
        c.setFillColorRGB(.35,.28,.82,alpha=a); c.circle(W/2,H/2,r,fill=1,stroke=0)

    c.setStrokeColor(HexColor(C["gold"])); c.setLineWidth(3)
    c.roundRect(14,14,W-28,H-28,18,fill=0,stroke=1)
    c.setStrokeColor(HexColor(C["purple"])); c.setLineWidth(.9)
    c.roundRect(22,22,W-44,H-44,13,fill=0,stroke=1)
    c.setStrokeColor(HexColor(C["gold"])); c.setLineWidth(.35)
    c.setDash(4,3); c.roundRect(28,28,W-56,H-56,11,fill=0,stroke=1); c.setDash()
    for ox,oy in [(24,24),(W-24,24),(24,H-24),(W-24,H-24)]:
        c.setStrokeColor(HexColor(C["gold"])); c.setLineWidth(1.4)
        c.circle(ox,oy,7,fill=0,stroke=1)
        c.setFillColor(HexColor(C["gold"])); c.circle(ox,oy,3,fill=1,stroke=0)

    c.setFillColorRGB(.04,.10,.19,alpha=.95)
    c.roundRect(30,H-112,W-60,82,8,fill=1,stroke=0)
    c.setStrokeColor(HexColor(C["gold"])); c.setLineWidth(.6)
    c.roundRect(30,H-112,W-60,82,8,fill=0,stroke=1)
    c.setFillColor(HexColor(C["gold"])); c.setFont("Helvetica-Bold",26)
    c.drawCentredString(W/2,H-64,"DELPHIA GENESIS")
    c.setFillColor(HexColor(C["teal"])); c.setFont("Helvetica",9.5)
    c.drawCentredString(W/2,H-88,"✦  CERTIFICATE OF IMAGINATION  ·  GENESIS LAYER v0.9.2.1  ✦")

    star_cy = H-192
    def draw_star(cx,cy,ro,ri,pts=5):
        path=c.beginPath()
        for i in range(pts*2):
            angle=math.pi/pts*i-math.pi/2; r=ro if i%2==0 else ri
            x,y=cx+r*math.cos(angle),cy+r*math.sin(angle)
            path.moveTo(x,y) if i==0 else path.lineTo(x,y)
        path.close(); c.drawPath(path,fill=1,stroke=1)
    for r,a in [(60,.06),(46,.10),(34,.08)]:
        c.setFillColorRGB(.95,.79,.30,alpha=a); c.circle(W/2,star_cy,r,fill=1,stroke=0)
    c.setFillColor(HexColor(C["gold"])); c.setStrokeColor(HexColor(C["purple"])); c.setLineWidth(1.2)
    draw_star(W/2,star_cy,36,15)
    c.setStrokeColor(HexColor(C["teal"])); c.setLineWidth(.7)
    c.setFillColorRGB(0,0,0,alpha=0); c.circle(W/2,star_cy,54,fill=0,stroke=1)

    ry=H-240
    c.setStrokeColor(HexColor(C["purple"])); c.setLineWidth(.7); c.line(44,ry,W-44,ry)
    c.setStrokeColor(HexColor(C["gold"]));   c.setLineWidth(.35); c.line(54,ry-5,W-54,ry-5)

    def draw_field(lbl,val,y):
        c.setFillColor(HexColor(C["teal"])); c.setFont("Helvetica",7.5)
        c.drawCentredString(W/2,y+17,lbl.upper())
        c.setStrokeColor(HexColor(C["purple"])); c.setLineWidth(.35)
        c.line(72,y+13,W-72,y+13)
        c.setFillColor(HexColor(C["white"])); c.setFont("Helvetica-Bold",13)
        disp=(val[:50]+"…") if len(val)>50 else val
        c.drawCentredString(W/2,y,disp)

    sha256 = hashlib.sha256(f"{asset_id}::{name}::{sovereign}".encode()).hexdigest().upper()
    fields=[("Creation",str(name)[:55]),("Genesis ID",str(asset_id)),
            ("Young Sovereign",str(sovereign)[:45]),
            ("Imagined Value",f"{safe_int(value):,} IMAGIX"),
            ("Date Sealed",datetime.now().strftime("%d %B %Y").upper()),
            ("Status","SACRED & IMMUTABLE")]
    fy,gap=H-282,47
    for i,(lbl,v) in enumerate(fields): draw_field(lbl,v,fy-i*gap)

    hash_y=fy-len(fields)*gap-20
    c.setFillColorRGB(.04,.10,.19,alpha=.82)
    c.roundRect(34,hash_y-30,W-68,48,6,fill=1,stroke=0)
    c.setStrokeColor(HexColor(C["purple"])); c.setLineWidth(.5)
    c.roundRect(34,hash_y-30,W-68,48,6,fill=0,stroke=1)
    c.setFillColor(HexColor(C["teal"])); c.setFont("Helvetica",7)
    c.drawCentredString(W/2,hash_y+10,"GENESIS HASH · SHA-256 INTEGRITY SEAL")
    c.setFillColor(HexColor(C["gold"])); c.setFont("Helvetica-Bold",7.5)
    c.drawCentredString(W/2,hash_y-10,sha256[:32])
    c.drawCentredString(W/2,hash_y-22,sha256[32:])

    bot_y=hash_y-46
    c.setStrokeColor(HexColor(C["gold"]));   c.setLineWidth(.7);  c.line(44,bot_y,W-44,bot_y)
    c.setStrokeColor(HexColor(C["purple"])); c.setLineWidth(.35); c.line(54,bot_y-5,W-54,bot_y-5)
    sig_y=bot_y-46
    c.setFillColor(HexColor(C["purple"])); c.setFont("Helvetica",8)
    c.drawCentredString(W/2,sig_y+16,"— Signed by the Keeper of the Genesis Layer —")
    c.setFillColor(HexColor(C["gold"])); c.setFont("Helvetica-Bold",11)
    c.drawCentredString(W/2,sig_y,"REY DELPHI  ·  REINO DE DELPHIA  ·  KARDASHEV VI")
    c.setFillColor(HexColor(C["teal"])); c.setFont("Helvetica",7)
    c.drawCentredString(W/2,28,"Delphia Genesis v0.9.2.1  ·  Where Imagination Becomes Sovereign  ·  delphia.genesis")
    c.save()
    return buf.getvalue()


# ══════════════════════════════════════════════════════════════════════
# ⑫ SESSION STATE
# ══════════════════════════════════════════════════════════════════════
_SS = {
    "authenticated":False,"user":"","imagix":0,
    "quest_completed":set(),"creations_df":None,
    "cert_bytes":{},
    "cert_ever":False,
    "split_open":{},
    "tutor_open":None,"tutor_used":False,"deep_q_used":False,
    "lore_added":False,"sold_ever":False,"bought_ever":False,"has_sponsor":False,
    SPONSOR_SESSION_KEY:False,
    "parent_mode":False,"sponsor_viewed_qs":False,"deep_q_open":None,
    "quest_banner":[],
    "buy_feedback":None,
}
for k,v in _SS.items():
    if k not in st.session_state: st.session_state[k]=v


# ══════════════════════════════════════════════════════════════════════
# ⑬ AUTH GATE
# ══════════════════════════════════════════════════════════════════════
if not st.session_state["authenticated"]:
    st.markdown("""
    <div class="g-hero" style="margin-top:40px;padding:48px 40px;">
        <div class="g-hero-title">⬟ DELPHIA GENESIS ⬟</div>
        <div class="g-hero-sub">CLARITY & CONTROL · GENESIS LAYER v0.9.2.1</div>
    </div>""", unsafe_allow_html=True)

    _, mid, _ = st.columns([1,1.6,1])
    with mid:
        a_login, a_reg = st.tabs(["🔑 LOGIN","🌟 REGISTER"])

        with a_login:
            st.markdown(f"<div style='font-family:DM Mono;color:{C['muted']};font-size:11px;margin-bottom:16px;'>Enter your Kingdom to access your Sovereign Vault.</div>", unsafe_allow_html=True)
            lk = st.text_input("Kingdom Name",key="l_k",placeholder="Astra Nova",label_visibility="collapsed")
            lp = st.text_input("Password",    key="l_p",type="password",placeholder="Your sacred password",label_visibility="collapsed")
            st.write("")
            if st.button("✦ ENTER THE IMAGINARIUM",type="primary",use_container_width=True,key="btn_login"):
                if not lk.strip() or not lp.strip():
                    st.warning("Kingdom name and password required.")
                else:
                    ok, msg = verify_user(lk.strip(), lp.strip())
                    if ok:
                        u = lk.strip()
                        st.session_state.update({
                            "authenticated":True,"user":u,
                            "quest_completed":load_quests_done(u),
                            "imagix":load_wallet(u),
                            SPONSOR_SESSION_KEY:False,
                            "sponsor_viewed_qs":False,
                            "cert_bytes":{},"split_open":{},
                            "quest_banner":[],"buy_feedback":None,
                        })
                        urow = get_user_row(u)
                        if urow and str(urow.get("sponsor_kingdom","")).strip() not in ("","nan"):
                            st.session_state["has_sponsor"] = True
                        ensure_dirs(u); log_activity(u,"LOGIN"); st.rerun()
                    else:
                        st.error(f"⚠️ {msg}")

        with a_reg:
            st.markdown(f"<div style='font-family:DM Mono;color:{C['muted']};font-size:11px;margin-bottom:16px;'>Forge your Kingdom on the Genesis Layer.</div>", unsafe_allow_html=True)
            rk  = st.text_input("Kingdom Name ✦",key="r_k",placeholder="e.g. Astra Nova",label_visibility="collapsed")
            rp  = st.text_input("Sacred Password",key="r_p",type="password",placeholder="Choose a strong password",label_visibility="collapsed")
            rp2 = st.text_input("Confirm Password",key="r_p2",type="password",placeholder="Repeat your password",label_visibility="collapsed")
            rdob = st.date_input("Date of Birth",key="r_dob",min_value=date(1980,1,1),max_value=date.today(),value=date(2010,1,1))
            st.caption("Used to match you with your Genesis Tutors.")
            with st.expander("👁 Add a Sponsor / Parent (optional)"):
                sp_k = st.text_input("Sponsor Kingdom Name",key="sp_k",placeholder="Parent's Kingdom")
                sp_p = st.text_input("Sponsor Password",    key="sp_p",type="password",placeholder="Sponsor's password")
                st.caption("Your sponsor can view your progress and help manage your account.")
            if st.button("🌟 FORGE MY KINGDOM",type="primary",use_container_width=True,key="btn_reg"):
                if not rk.strip(): st.error("Your Kingdom needs a name.")
                elif len(rp)<4:    st.error("Password must be at least 4 characters.")
                elif rp!=rp2:      st.error("Passwords do not match.")
                else:
                    ok, msg = register_user(rk.strip(),rp,rdob.isoformat(),
                                            st.session_state.get("sp_k",""),
                                            st.session_state.get("sp_p",""))
                    if ok:
                        u = rk.strip()
                        st.session_state.update({
                            "authenticated":True,"user":u,
                            "quest_completed":set(),"imagix":0,
                            "has_sponsor":bool(str(st.session_state.get("sp_k","")).strip()),
                            "quest_banner":[],"buy_feedback":None,
                        })
                        ensure_dirs(u); st.success("✦ Kingdom forged! Welcome to the Genesis Layer.")
                        st.balloons(); st.rerun()
                    else: st.error(msg)
    st.stop()


# ══════════════════════════════════════════════════════════════════════
# ⑭ MAIN APP — authenticated only beyond this point
# ══════════════════════════════════════════════════════════════════════
user: str = st.session_state["user"]
ensure_dirs(user)

if st.session_state["creations_df"] is None:
    st.session_state["creations_df"] = load_creations()

df_all: pd.DataFrame = st.session_state["creations_df"]
user_df = (df_all[df_all["sovereign"]==user].copy()
           if not df_all.empty and "sovereign" in df_all.columns
           else pd.DataFrame(columns=CREATION_COLS))

dob           = get_user_dob(user)
age           = calc_age(dob)
is_minor      = age < MINOR_AGE
active_tutors = get_active_tutors(age)

run_quests(df_all, user)

total_imagix = st.session_state["imagix"]
rank         = get_rank(total_imagix)
n_done       = len(st.session_state["quest_completed"])


# ── HEADER ─────────────────────────────────────────────────────────
h1,h2,h3,h4,h5 = st.columns([4,1,1,1,1])
h1.markdown(f"""
<div style="padding-top:8px;">
    <span style="font-family:'Cinzel',serif;font-size:17px;color:{C['gold']};font-weight:700;">🌟 {user}</span>
    &nbsp;<span style="color:{C['muted']};font-size:13px;">·</span>&nbsp;
    <span class="rank-pill" style="font-size:11px;padding:4px 14px;">{rank['name']}</span>
</div>""", unsafe_allow_html=True)
h2.metric("IMAGIX",   f"{total_imagix:,} 𝕀")
h3.metric("CREATIONS", len(user_df))
h4.metric("QUESTS",   f"{n_done}/{len(QUESTS)}")
if h5.button("✦ LOGOUT"):
    for k in list(_SS.keys()):
        if k in st.session_state: del st.session_state[k]
    st.rerun()

pb, _ = st.columns([3,1])
with pb:
    if not rank["maxed"]:
        st.progress(rank["progress"],
                    text=f"Progress to next rank · {total_imagix:,} / {rank['next']:,} IMAGIX")
    else:
        st.progress(1.0, text="👑 LEGEND — Supreme Sovereign of the Genesis Layer")

st.divider()

# ── QUEST BANNER (persistent, dismissable) ──────────────────────────
render_quest_banner()

# ── BUY FEEDBACK PANEL ──────────────────────────────────────────────
if st.session_state.get("buy_feedback"):
    bf = st.session_state["buy_feedback"]
    details_html = ""
    for k,v in bf.get("details",[]):
        details_html += f'<div class="buy-detail-row"><span class="buy-detail-key">{k}</span><span class="buy-detail-val">{v}</span></div>'
    st.markdown(f"""
    <div class="buy-success">
        <div class="buy-success-title">🎉 {bf.get('title','Purchase Complete!')}</div>
        {details_html}
    </div>""", unsafe_allow_html=True)
    if st.button("✕ Dismiss", key="dismiss_buy"):
        st.session_state["buy_feedback"] = None
        st.rerun()
    st.divider()


# ══════════════════════════════════════════════════════════════════════
# TUTOR PANEL
# ══════════════════════════════════════════════════════════════════════
def render_tutor_panel(context_tab: str):
    if not active_tutors: return

    st.markdown(f"""
    <div style="font-family:'Cinzel',serif;color:{C['teal']};font-size:9px;letter-spacing:2px;margin-bottom:8px;">
        ✦ GENESIS TUTORS — Choose your guide
    </div>""", unsafe_allow_html=True)

    t_cols = st.columns(len(active_tutors)+1)

    for i,t in enumerate(active_tutors):
        with t_cols[i]:
            if st.button(f"{t['emoji']} {t['short']}", key=f"tb_{t['id']}_{context_tab}"):
                key = f"{t['id']}_{context_tab}"
                st.session_state["tutor_open"] = (None if st.session_state.get("tutor_open")==key else key)
                if st.session_state["tutor_open"] == key:
                    with st.spinner(f"{t['emoji']} thinking…"):
                        msg = get_tutor_message(t, context_tab, user, df_all)
                    st.session_state[f"tmsg_{key}"] = msg
                    if not st.session_state["tutor_used"]:
                        st.session_state["tutor_used"] = True
                        run_quests(df_all, user)

    with t_cols[-1]:
        st.markdown('<div class="deep-q-btn">',unsafe_allow_html=True)
        if st.button("🔮 DEEP Q",key=f"deepq_{context_tab}",help="Ask your tutor a deep question"):
            current = st.session_state.get("deep_q_open")
            st.session_state["deep_q_open"] = None if current==context_tab else context_tab
        st.markdown('</div>',unsafe_allow_html=True)

    open_key = st.session_state.get("tutor_open","") or ""
    if open_key.endswith(f"_{context_tab}"):
        tid = open_key.replace(f"_{context_tab}","")
        t   = next((x for x in active_tutors if x["id"]==tid), None)
        if t and f"tmsg_{open_key}" in st.session_state:
            st.markdown(f"""
            <div class="tutor-chat">
                <div class="tutor-name" style="color:{t['color']};">{t['emoji']} {t['name']}</div>
                <div class="tutor-msg">{st.session_state[f'tmsg_{open_key}']}</div>
            </div>""", unsafe_allow_html=True)

    if st.session_state.get("deep_q_open") == context_tab:
        dq_tutor = active_tutors[0]
        with st.expander("🔮 Deep Question", expanded=True):
            dq = st.text_input("Ask anything deep…", key=f"dq_input_{context_tab}",
                               placeholder="¿Por qué la creatividad tiene valor?")
            dc1,dc2 = st.columns([1,1])
            with dc1:
                if st.button("✦ ASK", key=f"dq_ask_{context_tab}") and dq.strip():
                    with st.spinner(f"{dq_tutor['emoji']} Thinking deeply…"):
                        answer = get_deep_answer(dq_tutor, dq.strip(), user, df_all)
                    st.session_state[f"dq_ans_{context_tab}"] = answer
                    if not st.session_state["deep_q_used"]:
                        st.session_state["deep_q_used"] = True
                        run_quests(df_all, user)
            with dc2:
                if st.button("✕ Close", key=f"dq_close_{context_tab}"):
                    st.session_state["deep_q_open"] = None; st.rerun()
            if f"dq_ans_{context_tab}" in st.session_state:
                st.markdown(f"""
                <div class="tutor-chat">
                    <div class="tutor-name" style="color:{dq_tutor['color']};">{dq_tutor['emoji']} {dq_tutor['name']}</div>
                    <div class="tutor-msg">{st.session_state[f'dq_ans_{context_tab}']}</div>
                </div>""", unsafe_allow_html=True)

    st.divider()


# ══════════════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════════════
tab_vault,tab_wallet,tab_quests,tab_market,tab_upload,tab_activity = st.tabs([
    "🌌 MY VAULT","💎 WALLET","⚔️ QUESTS","🌠 MARKETPLACE","🌱 UPLOAD","📜 ACTIVITY",
])


# ────────────────────────────────────────────────────────────────────
# TAB: VAULT
# v0.9.2.1 FIX: TITLE button — store cert THEN rerun (no finally), no flash
# ────────────────────────────────────────────────────────────────────
with tab_vault:
    render_tutor_panel("vault")

    vc1,vc2 = st.columns([3,1])
    vc1.markdown("### 🌌 SOVEREIGN CREATIONS VAULT")
    with vc2:
        sort_opt = st.selectbox("Sort",["Newest","Highest Value","Alphabetical"],
                                label_visibility="collapsed")

    if user_df.empty:
        st.info("🌠 Your Vault awaits its first creation. Head to Upload to begin your Genesis journey!")
        st.markdown(f"""
        <div style="font-family:'Cinzel',serif;color:{C['gold']};font-size:13px;margin:20px 0 12px;letter-spacing:1px;">
            ✦ GENESIS SHOWCASE — Creations from the Multiverse
        </div>""", unsafe_allow_html=True)
        dc = st.columns(6)
        for i,(dn,dv,de) in enumerate(DEMO_SHOWCASE):
            with dc[i%6]:
                st.markdown(f"""
                <div class="g-card showcase-glow">
                    <div class="g-card-img"><span style="position:relative;z-index:1;">{de}</span></div>
                    <div class="g-card-body">
                        <div class="g-badge-gold">SHOWCASE</div>
                        <div class="g-card-title">{dn}</div>
                        <div class="g-card-value">{dv:,} 𝕀</div>
                        <div class="g-card-id">DEMO · GENESIS MULTIVERSE</div>
                    </div>
                </div>""", unsafe_allow_html=True)
    else:
        sdf = user_df.copy()
        if sort_opt=="Newest":       sdf=sdf.sort_values("created_at",ascending=False)
        elif sort_opt=="Highest Value":
            sdf["_v"]=pd.to_numeric(sdf["value"],errors="coerce").fillna(0)
            sdf=sdf.sort_values("_v",ascending=False)
        else: sdf=sdf.sort_values("name")

        total_val = pd.to_numeric(sdf["value"],errors="coerce").fillna(0).sum()
        n_frac    = int(sdf["is_fractional"].astype(str).str.lower().isin(["true","1"]).sum())
        n_cert    = int(sdf["cert_downloaded"].astype(str).str.lower().isin(["true","1"]).sum())
        credit    = int(total_val*0.25+total_imagix*1.5)

        pm1,pm2,pm3,pm4 = st.columns(4)
        pm1.metric("PORTFOLIO VALUE",f"{total_val:,.0f} 𝕀")
        pm2.metric("FRACTIONALISED", n_frac)
        pm3.metric("CERTS ISSUED",   n_cert)
        pm4.metric("CREDIT CAPACITY",f"~{credit:,} 𝕀")
        st.caption(f"{len(sdf)} creation(s) on the Genesis Layer")

        records = sdf.to_dict("records")
        CPR = 4

        for rs in range(0,len(records),CPR):
            cols = st.columns(CPR)
            for ci,rec in enumerate(records[rs:rs+CPR]):
                with cols[ci]:
                    aid      = str(rec.get("id") or "")
                    rn       = str(rec.get("name") or "Unknown")
                    rv       = safe_int(rec.get("value"))
                    re_      = str(rec.get("emoji") or "🌟")
                    rfp      = str(rec.get("file_path") or "")
                    is_frac  = str(rec.get("is_fractional","")).lower() in ("true","1")
                    n_f      = max(1, safe_int(rec.get("fraction_count"),100))
                    lp_raw   = str(rec.get("listed_price","")).strip()
                    is_listed= lp_raw not in ("","nan","0","None")

                    frac_badge  = '<div class="g-badge-teal">&#8530; FRACTIONAL</div>' if is_frac   else ""
                    mkt_badge   = '<div class="g-badge-purple">&#127776; LISTED</div>'  if is_listed else ""

                    b64 = img_to_b64(rfp)

                    if b64:
                        st.markdown(f"""
                        <div class="g-card">
                            <div style="position:relative;height:130px;overflow:hidden;">
                                <img src="{b64}" style="width:100%;height:130px;object-fit:cover;display:block;">
                                {frac_badge}{mkt_badge}
                            </div>
                            <div class="g-card-body">
                                <div class="g-card-title">{rn}</div>
                                <div class="g-card-value">{rv:,} &#120128;</div>
                                <div class="g-card-id">{aid}</div>
                            </div>
                        </div>""", unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div class="g-card">
                            <div class="g-card-img">
                                <span style="position:relative;z-index:1;">{re_}</span>
                                {frac_badge}{mkt_badge}
                            </div>
                            <div class="g-card-body">
                                <div class="g-card-title">{rn}</div>
                                <div class="g-card-value">{rv:,} &#120128;</div>
                                <div class="g-card-id">{aid}</div>
                            </div>
                        </div>""", unsafe_allow_html=True)

                    # ══ TITLE — v0.9.2.1 FIX ══════════════════════
                    # cert_key stored in session_state (not cert_bytes dict).
                    # On click: generate → store in session_state → st.rerun()
                    # No finally block. No intermediate "None" widget state.
                    cert_key = f"cert_{aid}"

                    if cert_key not in st.session_state:
                        if st.button("📜 TITLE", key=f"title_{aid}"):
                            with st.spinner("Generating certificate…"):
                                try:
                                    pdf_bytes = make_certificate(rn, aid, user, rv)
                                    # Write to session_state BEFORE rerun
                                    st.session_state[cert_key] = pdf_bytes
                                    fresh = load_creations().copy()
                                    fresh.loc[fresh["id"]==aid,"cert_downloaded"] = "True"
                                    save_creations(fresh)
                                    st.session_state["creations_df"] = load_creations()
                                    if not st.session_state["cert_ever"]:
                                        st.session_state["cert_ever"] = True
                                    run_quests(df_all, user)
                                    log_activity(user, "CERT_GEN", aid)
                                    # Rerun only on success — no finally
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Certificate error: {e}")
                    else:
                        # cert is ready — show only the download button
                        safe_name = rn[:24].replace(" ","_")
                        st.download_button(
                            "⬇️ Certificate",
                            data=st.session_state[cert_key],
                            file_name=f"{safe_name}_Certificate.pdf",
                            mime="application/pdf",
                            key=f"dl_{aid}",
                            use_container_width=True,
                        )
                        if st.button("↻ New cert", key=f"regen_{aid}"):
                            del st.session_state[cert_key]
                            st.rerun()

                    # ══ SPLIT ═════════════════════════════════════
                    split_lbl = "⅒ FRACS" if is_frac else "🔀 SPLIT"
                    if st.button(split_lbl, key=f"split_{aid}"):
                        st.session_state["split_open"][aid] = (
                            not st.session_state["split_open"].get(aid, False)
                        )
                        if not is_frac:
                            fresh = load_creations().copy()
                            fresh.loc[fresh["id"]==aid,"is_fractional"]  = "True"
                            fresh.loc[fresh["id"]==aid,"fraction_count"] = "100"
                            save_creations(fresh)
                            st.session_state["creations_df"] = load_creations()
                            run_quests(df_all, user)
                            log_activity(user, "SPLIT", aid)
                        st.rerun()

                    if st.session_state["split_open"].get(aid):
                        fv = rv/n_f
                        st.success(f"**{rn}** → **{n_f}** shares · **{fv:,.0f} 𝕀** each ✦")

                    # ══ LIST / DELIST ════════════════════════════
                    list_lbl = "🌠 DELIST" if is_listed else "🌠 LIST"
                    if st.button(list_lbl, key=f"list_{aid}"):
                        fresh = load_creations().copy()
                        if not is_listed:
                            fresh.loc[fresh["id"]==aid,"listed_price"] = str(rv)
                            fresh.loc[fresh["id"]==aid,"listed_at"]    = datetime.now().isoformat()
                            save_creations(fresh)
                            mdf = load_market().copy()
                            if aid not in mdf["id"].values:
                                mdf = pd.concat([mdf,pd.DataFrame([{
                                    "id":aid,"name":rn,"sovereign":user,
                                    "value":str(rv),"emoji":re_,
                                    "listed_price":str(rv),
                                    "listed_at":datetime.now().isoformat(),
                                }])],ignore_index=True)
                            save_market(mdf)
                            run_quests(df_all,user)
                            log_activity(user,"LIST",f"{aid}@{rv}")
                            st.success(f"✦ **{rn}** listed!")
                        else:
                            fresh.loc[fresh["id"]==aid,"listed_price"] = ""
                            fresh.loc[fresh["id"]==aid,"listed_at"]    = ""
                            save_creations(fresh)
                            mdf = load_market()
                            save_market(mdf[mdf["id"]!=aid].copy())
                            log_activity(user,"DELIST",aid)
                            st.info(f"✦ **{rn}** delisted.")
                        st.session_state["creations_df"] = load_creations()
                        st.rerun()


# ────────────────────────────────────────────────────────────────────
# TAB: WALLET
# ────────────────────────────────────────────────────────────────────
with tab_wallet:
    render_tutor_panel("wallet")
    st.markdown("### 💎 IMAGIX WALLET")

    _,wm,_ = st.columns([1,1.5,1])
    with wm:
        st.markdown(f"""
        <div class="wallet-card">
            <div class="wallet-label">CURRENT BALANCE</div>
            <div class="wallet-amount">{total_imagix:,} 𝕀</div>
            <div class="wallet-label" style="margin-top:8px;">IMAGIX · GENESIS LAYER v0.9.2.1</div>
        </div>""", unsafe_allow_html=True)

    if not user_df.empty:
        pv         = pd.to_numeric(user_df["value"],errors="coerce").fillna(0).sum()
        credit_est = int(pv*0.25+total_imagix*1.5)
        pc1,pc2,pc3 = st.columns(3)
        pc1.metric("VAULT VALUE",    f"{pv:,.0f} 𝕀")
        pc2.metric("IMAGIX EARNED",  f"{total_imagix:,} 𝕀")
        pc3.metric("CREDIT CAPACITY",f"~{credit_est:,} 𝕀",help="Estimated from vault + wallet")

    st.divider()
    st.markdown("#### ✦ Earnings Ledger")

    rows_html = ""
    for cat in ["Onboarding","Creation","Collection","Actions","Daily","Wealth"]:
        cat_qs = [q for q in QUESTS if q.get("cat")==cat]
        if not cat_qs: continue
        rows_html += f'<tr><td colspan="3" class="ledger-cat">{cat}</td></tr>'
        for q in cat_qs:
            done_flag = q["id"] in st.session_state["quest_completed"]
            s_col  = C["teal"] if done_flag else C["muted"]
            r_col  = C["gold"] if done_flag else C["muted"]
            status = "✅ DONE" if done_flag else "○ PENDING"
            rows_html += f"""
            <tr>
                <td style="color:#ccd6f0;">{q['icon']} {q['title']}</td>
                <td style="color:{s_col};">{status}</td>
                <td style="color:{r_col};text-align:right;font-family:'Cinzel',serif;font-weight:700;">+{q['reward']:,} 𝕀</td>
            </tr>"""

    st.markdown(f"""
    <table class="ledger-table">
        <thead><tr><th>QUEST</th><th>STATUS</th><th style="text-align:right;">REWARD</th></tr></thead>
        <tbody>{rows_html}</tbody>
    </table>""", unsafe_allow_html=True)

    st.write("")
    total_pot = sum(q["reward"] for q in QUESTS)
    earned    = sum(q["reward"] for q in QUESTS if q["id"] in st.session_state["quest_completed"])
    wc1,wc2,wc3 = st.columns(3)
    wc1.metric("EARNED",         f"{earned:,} 𝕀")
    wc2.metric("TOTAL POTENTIAL",f"{total_pot:,} 𝕀")
    wc3.metric("REMAINING",      f"{total_pot-earned:,} 𝕀")


# ────────────────────────────────────────────────────────────────────
# TAB: QUESTS
# ────────────────────────────────────────────────────────────────────
with tab_quests:
    render_tutor_panel("quests")
    st.markdown("### ⚔️ QUESTS & PROGRESS")

    qc1,qc2 = st.columns([2,1])
    with qc1:
        st.markdown(f"""
        <div style="margin-bottom:18px;">
            <div style="font-family:'DM Mono',monospace;color:{C['teal']};font-size:9px;letter-spacing:3px;margin-bottom:8px;">CURRENT RANK</div>
            <div class="rank-pill">{rank['name']}</div>
        </div>""", unsafe_allow_html=True)
        if not rank["maxed"]:
            st.progress(rank["progress"],text=f"{rank['next']-total_imagix:,} IMAGIX needed to advance")
        else:
            st.progress(1.0,text="👑 Maximum rank — you are LEGEND")
    with qc2:
        st.markdown(f"""
        <div style="background:{C['card']};border:1px solid rgba(157,78,221,.4);border-radius:12px;padding:16px 20px;text-align:center;">
            <div style="font-family:'DM Mono',monospace;color:{C['teal']};font-size:9px;letter-spacing:2px;margin-bottom:10px;">RANK TIERS</div>
            <div style="font-family:'Cinzel',serif;color:{C['muted']};font-size:9px;line-height:2.1;">
                ✦ SPARK I–III · 0–25k<br>🔥 FLAME I–III · 50k–175k<br>⭐ STAR I–III · 275k–600k<br>👑 LEGEND · 900k+
            </div>
        </div>""", unsafe_allow_html=True)

    st.divider()
    done_ids = st.session_state["quest_completed"]
    for cat in ["Onboarding","Creation","Collection","Actions","Daily","Wealth"]:
        cat_qs = [q for q in QUESTS if q.get("cat")==cat]
        if not cat_qs: continue
        st.markdown(f"""<div style="font-family:'Cinzel',serif;color:{C['purple']};font-size:10px;letter-spacing:2px;margin:16px 0 8px;text-transform:uppercase;">◈ {cat}</div>""",
                    unsafe_allow_html=True)
        for q in cat_qs:
            done = q["id"] in done_ids
            st.markdown(f"""
            <div class="q-card {'done' if done else ''}">
                <div class="q-icon">{q['icon']}</div>
                <div class="q-info">
                    <div class="q-title">{'✅ ' if done else '○ '}{q['title']}</div>
                    <div class="q-desc">{q['desc']}</div>
                </div>
                <div class="q-reward">+{q['reward']:,} 𝕀</div>
            </div>""", unsafe_allow_html=True)

    st.divider()
    rem = sum(q["reward"] for q in QUESTS if q["id"] not in done_ids)
    st.markdown(f"**Completed:** `{len(done_ids)}/{len(QUESTS)}`  ·  **Earned:** `{total_imagix:,} 𝕀`  ·  **Remaining:** `{rem:,} 𝕀`")


# ────────────────────────────────────────────────────────────────────
# TAB: MARKETPLACE
# ────────────────────────────────────────────────────────────────────
with tab_market:
    render_tutor_panel("market")
    st.markdown("### 🌠 GENESIS MARKETPLACE")

    mdf = load_market()

    if mdf.empty or "id" not in mdf.columns or len(mdf)==0:
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,{C['card']},{C['card2']});border:1px solid rgba(242,201,76,.35);border-radius:16px;padding:40px 32px;text-align:center;overflow:hidden;">
            <div style="font-size:50px;margin-bottom:14px;">🌠</div>
            <div style="font-family:'Cinzel',serif;color:{C['gold']};font-size:18px;font-weight:700;letter-spacing:2px;">GENESIS MARKETPLACE</div>
            <div style="font-family:'DM Mono',monospace;color:{C['teal']};font-size:11px;margin-top:10px;">No creations listed yet — be the first Sovereign to open trade!</div>
            <div style="font-family:'DM Mono',monospace;color:{C['muted']};font-size:10px;margin-top:18px;line-height:2;">
                ✦ Go to MY VAULT and click 🌠 LIST<br>✦ Fractional trading · v1.0<br>✦ IMAGIX escrow · v1.0
            </div>
        </div>""", unsafe_allow_html=True)
    else:
        mc1,mc2,mc3 = st.columns([2,1,1])
        mc1.markdown(f"**{len(mdf)} listing(s)** on the Genesis Layer")
        with mc2:
            mkt_sort = st.selectbox("Sort",["Recent","Highest Price","Lowest Price"],label_visibility="collapsed")
        with mc3:
            show_own = st.checkbox("Show my listings",value=True)

        mdf2 = mdf.copy()
        if mkt_sort=="Highest Price":
            mdf2["_lp"]=pd.to_numeric(mdf2["listed_price"],errors="coerce").fillna(0)
            mdf2=mdf2.sort_values("_lp",ascending=False)
        elif mkt_sort=="Lowest Price":
            mdf2["_lp"]=pd.to_numeric(mdf2["listed_price"],errors="coerce").fillna(0)
            mdf2=mdf2.sort_values("_lp",ascending=True)
        else: mdf2=mdf2.sort_values("listed_at",ascending=False)

        if not show_own: mdf2=mdf2[mdf2["sovereign"]!=user]
        if mdf2.empty:   st.info("No listings match your filter.")

        for _,mrow in mdf2.iterrows():
            mid  = str(mrow.get("id",""))
            mn   = str(mrow.get("name",""))
            ms   = str(mrow.get("sovereign",""))
            me   = str(mrow.get("emoji","🌟"))
            mp   = safe_int(mrow.get("listed_price"))
            is_own   = (ms==user)
            can_buy  = (not is_own and total_imagix>=mp and mp>0)
            need_more = max(0, mp-total_imagix)

            owner_tag = f" · <span style='color:{C['teal']};'>YOUR LISTING</span>" if is_own else ""
            st.markdown(f"""
            <div class="mkt-row">
                <div class="mkt-emoji">{me}</div>
                <div style="flex:1;"><div class="mkt-name">{mn}</div><div class="mkt-seller">by {ms}{owner_tag}</div></div>
                <div class="mkt-price">{mp:,} 𝕀</div>
            </div>""", unsafe_allow_html=True)

            if not is_own:
                bc1,bc2 = st.columns([2,1])
                with bc1:
                    if st.button(f"💰 BUY  {mp:,} 𝕀",key=f"buy_{mid}",disabled=not can_buy):
                        try:
                            new_bal = total_imagix-mp
                            st.session_state["imagix"] = new_bal
                            save_wallet(user, new_bal)
                            save_wallet(ms, load_wallet(ms)+mp)
                            cdf = load_creations().copy()
                            cdf.loc[cdf["id"]==mid,"sovereign"]    = user
                            cdf.loc[cdf["id"]==mid,"listed_price"] = ""
                            cdf.loc[cdf["id"]==mid,"listed_at"]    = ""
                            save_creations(cdf)
                            mdf_u = load_market()
                            save_market(mdf_u[mdf_u["id"]!=mid].copy())
                            st.session_state["creations_df"] = load_creations()
                            st.session_state["bought_ever"]  = True
                            run_quests(load_creations(), user)
                            log_activity(user,"BUY",f"{mid} from {ms} @ {mp}")
                            st.session_state["buy_feedback"] = {
                                "title": f"You acquired '{mn}'! 🎉",
                                "details": [
                                    ("Creation",    mn),
                                    ("Seller",      ms),
                                    ("Price Paid",  f"{mp:,} 𝕀"),
                                    ("New Balance", f"{new_bal:,} 𝕀"),
                                    ("Status",      "OWNERSHIP TRANSFERRED"),
                                ],
                            }
                            st.rerun()
                        except Exception as e: st.error(f"Purchase failed: {e}")
                with bc2:
                    if not can_buy and mp>0: st.caption(f"Need {need_more:,} more 𝕀")


# ────────────────────────────────────────────────────────────────────
# TAB: UPLOAD
# ────────────────────────────────────────────────────────────────────
with tab_upload:
    render_tutor_panel("upload")
    st.markdown("### 🌱 REGISTER YOUR CREATION")
    st.caption("Inscribe your art, story, or craft onto the Genesis Layer — permanently and immutably.")

    with st.form("genesis_upload",clear_on_submit=True):
        cn  = st.text_input("Creation Name ✦",placeholder="e.g. The Adventures of Luna the Fox")
        uc1,uc2 = st.columns(2)
        with uc1: ep = st.selectbox("Creation Emblem",EMOJI_PICKS)
        with uc2: iv = st.number_input("Imagined Value (IMAGIX)",min_value=100,max_value=10_000_000,value=10_000,step=500)
        uf   = st.file_uploader("Upload your creation (image or PDF — optional)",type=["jpg","jpeg","png","pdf"],
                                help="Images appear as card thumbnails in your Vault.")
        lore = st.text_area("Creation Lore (optional)",placeholder="Describe the legend behind your creation…",
                            max_chars=280,height=80)
        ok_sub = st.form_submit_button("🌟 INSCRIBE ON THE GENESIS LAYER",type="primary",use_container_width=True)

    if ok_sub:
        if not cn.strip():
            st.error("Every great creation must bear a name, Young Sovereign.")
        else:
            with st.spinner("Inscribing your creation on the Genesis Layer…"):
                try:
                    aid = generate_id(cn,user); fp=""
                    if uf is not None:
                        sfn  = uf.name.encode("ascii","ignore").decode("ascii").replace(" ","_")
                        dest = f"{F['dir']}/{user}/{aid}_{sfn}"
                        with open(dest,"wb") as fh: fh.write(uf.getbuffer())
                        fp=dest
                    new_rec = {
                        "id":aid,"name":cn.strip(),"sovereign":user,
                        "value":str(int(iv)),"emoji":ep,"file_path":fp,
                        "created_at":datetime.now().isoformat(),
                        "is_fractional":"False","cert_downloaded":"False",
                        "fraction_count":"100","listed_price":"","listed_at":"",
                        "lore":lore.strip()[:280],
                    }
                    fresh = pd.concat([load_creations(),pd.DataFrame([new_rec])],ignore_index=True)
                    save_creations(fresh)
                    st.session_state["creations_df"] = fresh
                    if lore.strip(): st.session_state["lore_added"] = True
                    run_quests(fresh,user)
                    log_activity(user,"UPLOAD",f"'{cn.strip()}'")
                    st.balloons()
                    st.success(f"✦ **{cn.strip()}** inscribed! Genesis ID: `{aid}` · **{int(iv):,} IMAGIX**")
                    if lore.strip(): st.info(f"📜 Lore sealed: *\"{lore.strip()[:100]}\"*")
                    st.rerun()
                except Exception as e:
                    st.error(f"Inscription failed: {e} — Contact the Keeper of the Genesis Layer.")


# ────────────────────────────────────────────────────────────────────
# TAB: ACTIVITY
# ────────────────────────────────────────────────────────────────────
with tab_activity:
    render_tutor_panel("activity")
    st.markdown("### 📜 ACTIVITY LOG")
    st.caption("A record of every sovereign action on the Genesis Layer.")

    events = load_activity(user, n=20)

    if not events:
        st.info("📜 No activity recorded yet. Upload a creation or complete a quest to begin your log!")
    else:
        for ev in events:
            action = str(ev.get("action",""))
            detail = str(ev.get("detail",""))
            ts_raw = str(ev.get("ts",""))

            try:
                dt     = datetime.fromisoformat(ts_raw)
                ts_fmt = dt.strftime("%H:%M · %b %d")
            except Exception:
                ts_fmt = ts_raw[:16]

            meta      = ACT_META.get(action, ("◈", "muted", action))
            act_emoji, act_color, act_label = meta
            color_val = C.get(act_color, C["muted"])

            st.markdown(f"""
            <div class="act-item">
                <div class="act-icon">{act_emoji}</div>
                <div class="act-info">
                    <div class="act-action" style="color:{color_val};">{act_label}</div>
                    <div class="act-detail">{detail if detail else '—'}</div>
                </div>
                <div class="act-time">{ts_fmt}</div>
            </div>""", unsafe_allow_html=True)

        st.write("")
        st.caption(f"Showing last {len(events)} events · Sorted newest first")

        with st.expander("⚙️ Log Options"):
            if st.button("🗑️ Clear my activity log", key="clear_log"):
                df_act = _read(F["activity"], ACTIVITY_COLS)
                df_act = df_act[df_act["sovereign"] != user].copy()
                _write(df_act.tail(500), F["activity"])
                st.success("Activity log cleared.")
                st.rerun()


# ══════════════════════════════════════════════════════════════════════
# SIDEBAR — GENESIS TERMINAL v0.9.2.1
# ══════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(f"""
    <div style="text-align:center;padding:16px 0 8px;">
        <div style="font-family:'Cinzel',serif;color:{C['gold']};font-size:14px;font-weight:900;letter-spacing:3px;">◈ GENESIS TERMINAL</div>
        <div style="font-family:'DM Mono',monospace;color:{C['teal']};font-size:8px;letter-spacing:2px;margin-top:4px;opacity:.8;">v0.9.2.1 · CLARITY & CONTROL</div>
    </div>""", unsafe_allow_html=True)
    st.divider()

    total_val_s = pd.to_numeric(user_df["value"],errors="coerce").fillna(0).sum() if not user_df.empty else 0
    for lbl,val in [
        ("YOUNG SOVEREIGN",  user),
        ("AGE",              f"{age} yrs" if dob else "Unknown"),
        ("RANK",             rank["name"]),
        ("IMAGIX BALANCE",   f"{total_imagix:,} 𝕀"),
        ("VAULT VALUE",      f"{total_val_s:,.0f} 𝕀"),
        ("CREATIONS",        str(len(user_df))),
        ("QUESTS DONE",      f"{n_done} / {len(QUESTS)}"),
        ("TUTORS",           f"{len(active_tutors)} available"),
        ("SESSION",          datetime.now().strftime("%H:%M · %b %d")),
    ]:
        st.markdown(f"""
        <div class="term-block">
            <div class="term-key">{lbl}</div>
            <div class="term-val">{val}</div>
        </div>""", unsafe_allow_html=True)

    st.divider()
    if not rank["maxed"]:
        st.progress(rank["progress"])
        st.caption(f"{rank['next']-total_imagix:,} 𝕀 to next rank")
    else:
        st.progress(1.0); st.caption("👑 LEGEND — Maximum rank achieved")

    st.divider()

    st.markdown(f"""<div style="font-family:'Cinzel',serif;color:{C['muted']};font-size:9px;letter-spacing:2px;margin-bottom:6px;">PARENTAL / SPONSOR MODE</div>""",
                unsafe_allow_html=True)

    parent_on = st.toggle("Enable Sponsor View",value=st.session_state["parent_mode"],
                          key="parent_toggle",help="A sponsor/parent can view progress here.")
    st.session_state["parent_mode"] = parent_on

    if parent_on:
        if not st.session_state.get("sponsor_viewed_qs"):
            st.session_state["sponsor_viewed_qs"] = True
            run_quests(df_all, user)

        urow        = get_user_row(user)
        has_sponsor = (urow is not None and str(urow.get("sponsor_kingdom","")).strip() not in ("","nan"))

        if not st.session_state.get(SPONSOR_SESSION_KEY, False):
            if has_sponsor:
                sp_pw_h  = str(urow.get("sponsor_pw_hash",""))
                sp_input = st.text_input("Sponsor Password",type="password",
                                         key="sp_pw_input",label_visibility="collapsed",
                                         placeholder="Sponsor password")
                if st.button("🔓 VERIFY SPONSOR",key="verify_sp",use_container_width=True):
                    if hash_pw(sp_input)==sp_pw_h:
                        st.session_state[SPONSOR_SESSION_KEY]=True
                        st.success(f"✦ Sponsor verified: {urow['sponsor_kingdom']}")
                        st.rerun()
                    else: st.error("Wrong sponsor password.")
            else:
                st.session_state[SPONSOR_SESSION_KEY] = True

        if st.session_state.get(SPONSOR_SESSION_KEY, False):
            n_cert_s = int(user_df["cert_downloaded"].astype(str).str.lower().isin(["true","1"]).sum()) if not user_df.empty else 0
            n_frac_s = int(user_df["is_fractional"].astype(str).str.lower().isin(["true","1"]).sum()) if not user_df.empty else 0
            n_listed = int((user_df["listed_price"].astype(str).str.strip().isin(["","nan"])==False).sum()) if not user_df.empty else 0

            for lbl,val in [
                ("Kingdom",     user),("Age",f"{age} yrs"),("Rank",rank["name"]),
                ("Creations",   str(len(user_df))),("Portfolio",f"{total_val_s:,.0f} 𝕀"),
                ("Certs Issued",str(n_cert_s)),("Fractional",str(n_frac_s)),
                ("Listed",      str(n_listed)),("IMAGIX",f"{total_imagix:,} 𝕀"),
                ("Quests Done", f"{n_done}/{len(QUESTS)}"),
            ]:
                st.markdown(f"""<div class="sp-row"><span class="sp-key">{lbl}</span><span class="sp-val">{val}</span></div>""",
                            unsafe_allow_html=True)
            st.write("")
            st.markdown(f"""<div style="font-family:'DM Mono',monospace;color:{C['teal']};font-size:9px;margin-top:8px;line-height:1.8;opacity:.8;">✦ Read-only Sponsor view<br>✦ Trade approval gates · v1.0<br>✦ Activity log · v1.0</div>""",
                        unsafe_allow_html=True)

            if not is_minor:
                st.write("")
                with st.expander("🔑 Reset Kingdom Password"):
                    new_pw  = st.text_input("New Password",type="password",key="reset_pw1")
                    new_pw2 = st.text_input("Confirm",     type="password",key="reset_pw2")
                    if st.button("🔄 RESET",key="btn_reset_pw"):
                        if len(new_pw)<4:     st.error("Password too short.")
                        elif new_pw!=new_pw2: st.error("Passwords don't match.")
                        else:
                            df_u=load_users()
                            df_u.loc[df_u.kingdom==user,"pw_hash"]=hash_pw(new_pw)
                            save_users(df_u); log_activity(user,"PWD_RESET","by sponsor")
                            st.success("✦ Password reset by Sponsor.")
            else:
                st.markdown(f"""
                <div style="font-family:'DM Mono',monospace;color:{C['orange']};font-size:9px;
                     margin-top:10px;padding:8px 10px;background:rgba(243,156,18,.08);
                     border:1px solid rgba(243,156,18,.3);border-radius:8px;">
                    🛡️ Account management is handled by your Sponsor. Parental controls active.
                </div>""", unsafe_allow_html=True)

    st.divider()
    st.caption("Delphia Genesis v0.9.2.1\nWhere Imagination Becomes Sovereign\n© Rey Delphi · Kardashev VI")


# ══════════════════════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════════════════════
st.divider()
st.caption("⬟ Delphia Genesis v0.9.2.1 — Clarity & Control · Micro Patch  ·  The Sovereign Awakening  ·  Genesis Layer  ·  Kardashev Type VI ⬟")