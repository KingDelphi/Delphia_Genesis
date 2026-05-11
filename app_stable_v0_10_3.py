"""
╔══════════════════════════════════════════════════════════════════════╗
║       DELPHIA GENESIS v0.10.3 — CREATOR ECONOMY POLISH              ║
║                                                                      ║
║  New:  🔔 Notifications — disk-persisted, unread badge, full panel  ║
║        🔒 Loans — polished countdown, UX improvements               ║
║        ✨ General polish — premium feel, consistent feedback         ║
║  Fix:  Notification panel now survives page refresh                  ║
║        Loan countdown urgency colors + progress bar                  ║
║        push_notification() now writes to genesis_notifications.csv   ║
║                   Rey Delphi · Kardashev VI                          ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import pandas as pd
import os, hashlib, io, math, base64, json, random, urllib.request, uuid
from datetime import datetime, date, timedelta
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
    "creations":     "genesis_creations.csv",
    "quests":        "genesis_quests.csv",
    "wallets":       "genesis_wallets.csv",
    "users":         "genesis_users.csv",
    "market":        "genesis_market.csv",
    "activity":      "genesis_activity.csv",
    "loans":         "genesis_loans.csv",
    "auctions":      "genesis_auctions.csv",
    "notifications": "genesis_notifications.csv",   # v0.10.3 NEW — disk-backed
    "dir":           "creations",
}

MINOR_AGE           = 18
SPONSOR_SESSION_KEY = "sponsor_verified_session"
DEFAULT_ROYALTY_PCT = 5
LOAN_LTV_PCT        = 60
LOAN_TERM_DAYS      = 30
GENESIS_TREASURY    = "GENESIS_TREASURY"

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

ACT_META = {
    "UPLOAD":       ("📤", "teal",   "New Creation"),
    "CERT_GEN":     ("📜", "gold",   "Certificate"),
    "SPLIT":        ("🔀", "purple", "Fractionalised"),
    "LIST":         ("🌠", "purple", "Listed"),
    "DELIST":       ("✕",  "muted",  "Delisted"),
    "BUY":          ("💰", "green",  "Purchased"),
    "SOLD":         ("🤝", "teal",   "Sale Made"),
    "ROYALTY":      ("👑", "gold",   "Royalty Earned"),
    "QUESTS_DONE":  ("⚡", "gold",   "Quest Done"),
    "LOGIN":        ("🔑", "teal",   "Login"),
    "REGISTER":     ("🌟", "gold",   "Registered"),
    "PWD_RESET":    ("🔑", "orange", "Password Reset"),
    "LOCK":         ("🔒", "orange", "Asset Locked"),
    "UNLOCK":       ("🔓", "teal",   "Asset Unlocked"),
    "LOAN_OPEN":    ("🏦", "orange", "Loan Opened"),
    "LOAN_REPAY":   ("✅", "green",  "Loan Repaid"),
    "LOAN_DEFAULT": ("⚠️", "danger", "Loan Defaulted"),
    "AUCTION_LIST": ("🏛",  "purple", "Auction Listed"),
}

# Notification type → (icon, CSS color key, label)
NOTIF_TYPES = {
    "ROYALTY":      ("👑", "gold",   "Royalty Received"),
    "SOLD":         ("🤝", "teal",   "Sale Completed"),
    "BUY":          ("💰", "green",  "Purchase Confirmed"),
    "LOAN_OPEN":    ("🏦", "orange", "Loan Opened"),
    "LOAN_REPAY":   ("✅", "green",  "Loan Repaid"),
    "LOAN_DEFAULT": ("⚠️", "danger", "Loan Defaulted"),
    "LOAN_DUE":     ("⏰", "danger", "Loan Due Soon"),
    "QUEST":        ("⚡", "gold",   "Quest Completed"),
    "SYSTEM":       ("🌟", "purple", "System"),
}


# ══════════════════════════════════════════════════════════════════════
# ② TUTORS v2 (unchanged from v0.10.2)
# ══════════════════════════════════════════════════════════════════════
TUTORS = [
    {
        "id":"delphito_bebito","name":"Delphito el Bebito","emoji":"🍼",
        "age_min":6,"age_max":9,"color":"#FFD1DC","short":"Bebito",
        "persona":(
            "Eres Delphito el Bebito, el amigo mas alegre de los ninos de 6-8 anos en Delphia Genesis. "
            "Hablas de forma MUY simple. Usas emojis y frases cortisimas. NUNCA uses palabras dificiles. Maximo 2-3 oraciones."
        ),
        "fallbacks":{
            "vault":"Wooow! Tienes cosas super bonitas aqui! Sigue guardando mas! ✨",
            "upload":"Yay! Vas a poner algo nuevo! Eso es lo mejor! Hazlo ya! 🌈",
            "quests":"Mira cuantas medallas puedes ganar! Tu puedes atrapar todas! 🏆",
            "wallet":"Tienes muchos IMAGIX! Eres muy rico! Sigue asi! 🌟",
            "market":"Aqui puedes ver cosas de otros amigos! Que emocionante! 🎪",
            "activity":"Mira todo lo que has hecho! Eres muy activo! Sigue asi! ⭐",
            "loans":"Aqui guardas tus cosas especiales! Son muy importantes! ✨",
            "default":"Hola! Estas en el lugar mas magico del universo! Juega y crea! ✨",
        },
    },
    {
        "id":"chispitas_junior","name":"Chispitas Jr.","emoji":"⚡",
        "age_min":7,"age_max":10,"color":"#FFF3CD","short":"Chispitas Jr.",
        "persona":(
            "Eres Chispitas Jr., tutora curiosa para ninos de 7-10 anos. "
            "Explicas con ejemplos de juguetes y superheroes. Dices Sabias que...?. Maximo 3 oraciones."
        ),
        "fallbacks":{
            "vault":"Sabias que tu Vault es como un cofre del tesoro magico? Cada creacion que guardas brilla mas! ⚡",
            "upload":"Es como ser un inventor! Cuando subes una creacion, queda guardada para SIEMPRE. ⚡",
            "quests":"Las Quests son como misiones de superheroe! Completa cada una y ganaras IMAGIX. ⚡",
            "wallet":"Tu Wallet es como una alcanicia magica. Cada quest le mete mas brillo! ⚡",
            "market":"El Marketplace es como una feria magica! Fascinante! ⚡",
            "activity":"Tu historial de actividad es como el diario de un explorador! ⚡",
            "loans":"Los Loans son como pedir prestado tu juguete favorito a cambio de otro! Muy responsable! ⚡",
            "default":"Bienvenido al Genesis Layer! Es como un videojuego donde TU eres el heroe. ⚡",
        },
    },
    {
        "id":"delphita_pinga","name":"Delphita la Pinga","emoji":"🏃‍♀️",
        "age_min":9,"age_max":13,"color":"#C8F7C5","short":"Delphita",
        "persona":(
            "Eres Delphita la Pinga, tutora traviesa y energetica para ninos de 9-12 anos. "
            "Usas Boom!, Epico!, Sin limites!. Lanzas mini-retos. Maximo 4 oraciones."
        ),
        "fallbacks":{
            "vault":"BOOM! Tu vault esta tomando forma epica. A que puedes anadir 2 mas esta semana? 💥",
            "upload":"Este es el momento! Sube tu creacion AHORA! Epico! 🏃‍♀️",
            "quests":"Tienes quests sin completar! Vas a dejar pasar IMAGIX gratis? Imposible! 👀",
            "wallet":"Mira ese saldo! Podria ser el doble! Completa las quests y BOOM! 💰",
            "market":"El Marketplace es un campo de batalla economica! Lista y conquista! 🏃‍♀️",
            "activity":"Mira tu historial de batallas epicas! Cada accion cuenta, Soberano! 🏃‍♀️",
            "loans":"Los Loans son poder real! Colateraliza y consigue IMAGIX para tu proximo move epico! 🏃‍♀️",
            "default":"Oye, Soberano! Que estas esperando? Boom! 🏃‍♀️",
        },
    },
    {
        "id":"chispitas","name":"Chispitas","emoji":"🔬",
        "age_min":11,"age_max":14,"color":"#E8F4FD","short":"Chispitas",
        "persona":(
            "Eres Chispitas, tutora cientifica para jovenes de 11-14 anos. "
            "Conectas Delphia con economia y propiedad intelectual. Maximo 4 oraciones."
        ),
        "fallbacks":{
            "vault":"Tu Vault es un portafolio de activos creativos. Los artistas exitosos documentan cada obra. 🔬",
            "upload":"Registrar una creacion es como patentar una idea. La documentacion temprana es crucial. 🔬",
            "quests":"Las Quests son gamificacion basada en hitos reales. Cada una desarrolla un habito valioso. 🔬",
            "wallet":"El IMAGIX es moneda de merito basada en acciones reales. 🔬",
            "market":"El Marketplace simula un mercado de activos creativos. Que precio refleja el valor real? 🔬",
            "activity":"Tu Activity Log es un registro de tus decisiones como creador. Que patron ves? 🔬",
            "loans":"Un prestamo colateralizado usa tu activo como garantia. LTV 60% — estandar en DeFi real. 🔬",
            "default":"El Genesis Layer combina economia conductual y creatividad. Fascinante. 🔬",
        },
    },
    {
        "id":"delphito_bonito","name":"Delphito el Bonito","emoji":"😎",
        "age_min":13,"age_max":16,"color":"#D0E8FF","short":"El Bonito",
        "persona":(
            "Eres Delphito el Bonito, tutor cool para adolescentes de 13-15 anos. "
            "Usas no cap, real talk, main character energy. Maximo 4 oraciones."
        ),
        "fallbacks":{
            "vault":"Real talk — tu Vault es tu portafolio. 😎 Main character energy, siempre.",
            "upload":"No cap — subir una creacion es el move mas inteligente hoy. 😎 Con estilo.",
            "quests":"Las Quests son free IMAGIX esperandote. 😎 Real talk — ignorarlas es dejar valor sobre la mesa.",
            "wallet":"Tu IMAGIX es el score de tu soberania creativa. 😎 Sigue sumando.",
            "market":"El Marketplace es donde los creators serios juegan. 😎 Main character move.",
            "activity":"Tu Activity Log es el receipts de tu carrera como creator. 😎 Todo queda registrado.",
            "loans":"No cap — usar tu activo como colateral es finance level-up. 😎 LTV 60%, real talk.",
            "default":"Hey Soberano 😎 El Genesis Layer es tu canvas digital. Real talk.",
        },
    },
    {
        "id":"emperatriz_fenix","name":"Delphina la Emperatriz Fenix","emoji":"🦅",
        "age_min":15,"age_max":18,"color":"#E8D5FF","short":"Emperatriz",
        "persona":(
            "Eres Delphina la Emperatriz Fenix, mentora elegante para jovenes de 15-17 anos. "
            "Metaforas poderosas, referencias a arte y liderazgo. Maximo 5 oraciones."
        ),
        "fallbacks":{
            "vault":"Tu Vault es la primera pagina de tu legado creativo. 🦅 Cada obra inscrita es un acto de soberania.",
            "upload":"Crear y documentar una obra separa al artesano del artista. 🦅 Inscribe con intencion.",
            "quests":"Las Quests son el mapa de tu evolucion. 🦅 Los grandes imperios se construyen decision a decision.",
            "wallet":"El IMAGIX mide tu contribucion. 🦅 Que crezca es senal de que tu obra tiene impacto.",
            "market":"El Marketplace es el primer mercado de tu obra. 🦅 Establece precios que reflejen tu vision.",
            "activity":"Tu historial de actividad es el pergamino de tu soberania. 🦅 Leelo con orgullo.",
            "loans":"Un prestamo colateralizado es palanca soberana. 🦅 Usa tu activo para crecer sin venderlo.",
            "default":"Bienvenida al Genesis Layer, Joven Soberana. 🦅 Tu imaginacion tiene peso y forma.",
        },
    },
    {
        "id":"rey_delphi","name":"Delphi, Rey de Delphia","emoji":"👑",
        "age_min":17,"age_max":120,"color":"#F2C94C","short":"Rey Delphi",
        "persona":(
            "Eres Delphi, Rey de Delphia — mentor supremo para jovenes adultos de 17 anos o mas. "
            "Profundidad filosofica, sabiduria Kardashev VI. Maximo 5 oraciones con peso."
        ),
        "fallbacks":{
            "vault":"Tu Vault es el primer nodo de tu imperio creativo. 👑 En Kardashev VI, la imaginacion documentada es el activo mas escaso.",
            "upload":"Registrar una creacion es un acto de soberania digital. 👑 Actua ahora.",
            "quests":"Las Quests mapean tu evolucion. 👑 Cada hito entrena la disciplina que construye imperios.",
            "wallet":"El IMAGIX es un proxy de tu impacto. 👑 La verdadera riqueza es crear valor que otros deseen.",
            "market":"El Marketplace es donde tu vision encuentra la economia real. 👑 Actua con estrategia.",
            "activity":"Tu Activity Log es el registro de tus actos soberanos. 👑 Cada linea es historia del Genesis Layer.",
            "loans":"El prestamo colateralizado es el instrumento del soberano que no quiere vender su legado. 👑 LTV 60% — disciplina ante todo.",
            "default":"Soberano — el Genesis Layer es tu plataforma de soberania creativa. 👑 Actua con intencion.",
        },
    },
]

def get_active_tutors(age: int) -> list:
    eligible = [t for t in TUTORS if t["age_min"] <= age <= t["age_max"]]
    return eligible[:2] if len(eligible) > 2 else eligible


# ══════════════════════════════════════════════════════════════════════
# ③ QUESTS CATALOG (unchanged from v0.10.2)
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
    {"id":"q_img",     "title":"Visual Sovereign",    "desc":"Upload a creation with an image file.",             "reward":4_000,  "icon":"🖼","cat":"Creation",    "check": lambda df,u,ss: _q_has_img(df,u)},
    {"id":"q_million", "title":"Million Imaginer",    "desc":"Register a creation worth 1,000,000+ IMAGIX.",      "reward":25_000, "icon":"💎","cat":"Creation",   "check": lambda df,u,ss: _q_max_val(df,u)>=1_000_000},
    {"id":"q_lore",    "title":"Lorekeeper",          "desc":"Add a lore description to a creation.",            "reward":2_000,  "icon":"📖","cat":"Creation",   "check": lambda df,u,ss: ss.get("lore_added",False)},
    {"id":"q_three",   "title":"Trilogy of Wonders",  "desc":"Bring 3 creations to the Genesis Layer.",          "reward":12_000, "icon":"🎨","cat":"Collection", "check": lambda df,u,ss: _q_count(df,u)>=3},
    {"id":"q_five",    "title":"Hand of Wonders",     "desc":"Amass 5 creations.",                               "reward":18_000, "icon":"🖐","cat":"Collection", "check": lambda df,u,ss: _q_count(df,u)>=5},
    {"id":"q_ten",     "title":"Sovereign Gallery",   "desc":"Build a collection of 10 creations.",              "reward":30_000, "icon":"🏛","cat":"Collection", "check": lambda df,u,ss: _q_count(df,u)>=10},
    {"id":"q_cert",    "title":"Sacred Title Claimed","desc":"Download a Genesis Certificate.",                   "reward":3_000,  "icon":"📜","cat":"Actions",    "check": lambda df,u,ss: ss.get("cert_ever",False)},
    {"id":"q_split",   "title":"Fractional Sovereign","desc":"Activate fractional ownership.",                    "reward":7_500,  "icon":"🔀","cat":"Actions",    "check": lambda df,u,ss: _q_has_split(df,u)},
    {"id":"q_list",    "title":"Open for Trade",      "desc":"List a creation in the Marketplace.",              "reward":8_000,  "icon":"🌠","cat":"Actions",    "check": lambda df,u,ss: _q_has_listing(df,u)},
    {"id":"q_sold",    "title":"First Trade",         "desc":"Sell a creation in the Marketplace.",              "reward":15_000, "icon":"🤝","cat":"Actions",    "check": lambda df,u,ss: ss.get("sold_ever",False)},
    {"id":"q_daily",   "title":"Daily Genesis",       "desc":"Upload a creation today.",                         "reward":2_500,  "icon":"☀","cat":"Daily",       "check": lambda df,u,ss: _q_today_upload(df,u)},
    {"id":"q_tutor",   "title":"Wisdom Seeker",       "desc":"Consult a Genesis Tutor.",                         "reward":2_000,  "icon":"🧙","cat":"Daily",      "check": lambda df,u,ss: ss.get("tutor_used",False)},
    {"id":"q_deep_q",  "title":"Deep Thinker",        "desc":"Ask a Deep Question to a Tutor.",                  "reward":3_500,  "icon":"🔮","cat":"Daily",      "check": lambda df,u,ss: ss.get("deep_q_used",False)},
    {"id":"q_50k",     "title":"Golden Threshold",    "desc":"Accumulate 50,000 IMAGIX.",                        "reward":10_000, "icon":"💰","cat":"Wealth",     "check": lambda df,u,ss: ss.get("imagix",0)>=50_000},
    {"id":"q_bought",  "title":"First Acquisition",   "desc":"Purchase a creation from the Marketplace.",        "reward":12_000, "icon":"🛒","cat":"Wealth",     "check": lambda df,u,ss: ss.get("bought_ever",False)},
    {"id":"q_sponsor", "title":"Guardian Shield",     "desc":"A Sponsor is connected to your account.",          "reward":5_000,  "icon":"🛡","cat":"Wealth",     "check": lambda df,u,ss: ss.get("has_sponsor",False)},
    {"id":"q_royalty", "title":"Royalty Sovereign",   "desc":"Earn your first royalty from a secondary sale.",   "reward":8_000,  "icon":"👑","cat":"Wealth",     "check": lambda df,u,ss: ss.get("royalty_ever",False)},
]


# ══════════════════════════════════════════════════════════════════════
# ④ PAGE CONFIG — must be FIRST Streamlit call
# ══════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="DELPHIA GENESIS | IMAGINARIUM",
    page_icon="🌟",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ══════════════════════════════════════════════════════════════════════
# ⑤ THEME — v0.10.3 additions: richer notification panel, loan countdown
# ══════════════════════════════════════════════════════════════════════
def inject_theme():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700;900&family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=DM+Mono:wght@300;400;500&display=swap');

    :root{
        --space:#05121f;--card:#0d1f3a;--card2:#112B4D;
        --gold:#F2C94C;--gold2:#c8a000;--teal:#00E5C0;
        --purple:#9D4EDD;--purple2:#6b2fa0;
        --muted:#8899aa;--white:#FFFFFF;
        --green:#2ECC71;--orange:#F39C12;--danger:#FF6B6B;
    }
    html,body,[data-testid="stAppViewContainer"]{background:var(--space);color:var(--gold);}
    .stApp{
        background:
            radial-gradient(ellipse 80% 60% at 15% 10%,rgba(13,45,74,.9) 0%,transparent 70%),
            radial-gradient(ellipse 60% 50% at 85% 85%,rgba(10,31,53,.8) 0%,transparent 70%),
            linear-gradient(180deg,#060f1a 0%,var(--space) 100%);
    }
    h1,h2,h3{font-family:'Cinzel',serif!important;color:var(--gold)!important;letter-spacing:1px;}
    p,li,span,div{font-family:'DM Mono',monospace;}
    label{font-family:'DM Mono',monospace!important;color:var(--teal)!important;font-size:11px!important;}

    .stButton>button{background:linear-gradient(135deg,var(--purple),var(--purple2));color:var(--gold);border:1px solid rgba(242,201,76,.45);border-radius:8px;font-family:'Cinzel',serif;font-size:10px;font-weight:700;letter-spacing:1.5px;padding:8px 14px;transition:all .22s ease;width:100%;}
    .stButton>button:hover{background:linear-gradient(135deg,var(--gold),var(--gold2));color:var(--space);border-color:var(--gold);box-shadow:0 0 18px rgba(242,201,76,.45),0 4px 16px rgba(0,0,0,.4);transform:translateY(-2px);}
    .stButton>button[kind="primary"],[data-testid="stFormSubmitButton"]>button{background:linear-gradient(135deg,var(--gold),var(--gold2))!important;color:var(--space)!important;font-size:12px;padding:11px 28px;border:none!important;box-shadow:0 4px 20px rgba(242,201,76,.3);}
    [data-testid="stFormSubmitButton"]>button:hover{background:linear-gradient(135deg,#ffe080,var(--gold))!important;color:var(--space)!important;}
    .stDownloadButton>button{background:linear-gradient(135deg,rgba(0,229,192,.12),rgba(0,229,192,.24))!important;color:var(--teal)!important;border:1px solid var(--teal)!important;font-family:'Cinzel',serif;font-size:10px;letter-spacing:1px;width:100%;transition:all .2s;}
    .stDownloadButton>button:hover{background:var(--teal)!important;color:var(--space)!important;}

    .stTextInput input,.stNumberInput input,.stTextArea textarea{background-color:#0d1f3a!important;color:var(--teal)!important;border:1px solid rgba(157,78,221,.6)!important;border-radius:8px!important;font-family:'DM Mono',monospace!important;font-size:13px!important;caret-color:var(--gold);}
    .stTextInput input:focus,.stNumberInput input:focus,.stTextArea textarea:focus{border-color:var(--gold)!important;box-shadow:0 0 0 2px rgba(242,201,76,.15)!important;}
    .stTextInput input[type="password"]{color:var(--gold)!important;letter-spacing:3px;}
    .stSelectbox [data-baseweb="select"]>div{background-color:#0d1f3a!important;border:1px solid rgba(157,78,221,.6)!important;color:var(--teal)!important;font-family:'DM Mono',monospace!important;}
    [data-testid="stDateInput"]>div>div>input{background:#0d1f3a!important;color:var(--teal)!important;border:1px solid rgba(157,78,221,.6)!important;}

    .stTabs [data-baseweb="tab-list"]{background:transparent;border-bottom:1px solid rgba(157,78,221,.4);gap:2px;flex-wrap:wrap;}
    .stTabs [data-baseweb="tab"]{font-family:'Cinzel',serif;font-size:10px;letter-spacing:1px;color:var(--muted);padding:8px 13px;border-radius:8px 8px 0 0;border:1px solid transparent;border-bottom:none;transition:all .2s;}
    .stTabs [data-baseweb="tab"]:hover{color:var(--gold);background:rgba(242,201,76,.05);}
    .stTabs [aria-selected="true"]{background:#112B4D!important;color:var(--gold)!important;border-color:rgba(0,229,192,.5)!important;border-bottom:1px solid #112B4D!important;}

    [data-testid="metric-container"]{background:linear-gradient(135deg,#0d1f3a,#112B4D);border:1px solid rgba(157,78,221,.5);border-radius:12px;padding:12px 18px;transition:border-color .2s;}
    [data-testid="metric-container"]:hover{border-color:var(--gold);}
    [data-testid="metric-container"] label{color:var(--teal)!important;font-family:'Cinzel',serif!important;font-size:9px!important;letter-spacing:2px!important;text-transform:uppercase;}
    [data-testid="stMetricValue"]{color:var(--gold)!important;font-family:'Cinzel',serif!important;font-weight:700!important;}

    [data-testid="stSidebar"]{background:linear-gradient(180deg,#080f1e 0%,#0a1628 60%,#05121f 100%);border-right:1px solid rgba(157,78,221,.4);}
    [data-testid="stSidebar"] section{padding-top:0;}

    .stProgress>div>div>div>div{background:linear-gradient(90deg,#9D4EDD 0%,#4facfe 25%,#00E5C0 50%,#43e97b 75%,#F2C94C 100%);border-radius:4px;transition:width .4s ease;}
    .stProgress>div>div{background:rgba(255,255,255,.06);border-radius:4px;}

    .stSuccess>div{background:rgba(46,204,113,.1)!important;border:1px solid rgba(46,204,113,.4)!important;color:#2ECC71!important;font-family:'DM Mono',monospace!important;border-radius:10px!important;}
    .stInfo>div{background:rgba(0,229,192,.08)!important;border:1px solid rgba(0,229,192,.35)!important;color:var(--teal)!important;font-family:'DM Mono',monospace!important;border-radius:10px!important;}
    .stWarning>div{background:rgba(242,201,76,.08)!important;border:1px solid rgba(242,201,76,.35)!important;color:var(--gold)!important;border-radius:10px!important;}
    .stError>div{background:rgba(255,107,107,.1)!important;border:1px solid rgba(255,107,107,.4)!important;color:#FF6B6B!important;border-radius:10px!important;}
    [data-testid="stFileUploader"]>div{background:#0d1f3a!important;border:2px dashed rgba(157,78,221,.5)!important;border-radius:14px!important;}
    [data-testid="stFileUploader"]>div:hover{border-color:var(--gold)!important;}

    hr{border-color:rgba(157,78,221,.25)!important;margin:12px 0;}
    ::-webkit-scrollbar{width:5px;height:5px;}
    ::-webkit-scrollbar-track{background:transparent;}
    ::-webkit-scrollbar-thumb{background:rgba(157,78,221,.5);border-radius:3px;}
    .stCaption{color:#8899aa!important;font-size:10.5px!important;}
    .stMarkdown{color:#8899aa;}
    .stMarkdown strong{color:var(--gold)!important;}
    .stMarkdown code{background:rgba(0,229,192,.1)!important;color:var(--teal)!important;border:1px solid rgba(0,229,192,.2)!important;border-radius:4px;font-size:11px;}

    /* Genesis Card */
    .g-card{background:linear-gradient(145deg,#0d1f3a,#112B4D);border:1px solid rgba(0,229,192,.28);border-radius:14px;overflow:hidden;transition:all .28s cubic-bezier(.4,0,.2,1);position:relative;margin-bottom:8px;}
    .g-card:hover{border-color:var(--gold);box-shadow:0 0 0 1px rgba(242,201,76,.15),0 8px 32px rgba(0,0,0,.5),0 0 40px rgba(242,201,76,.12);transform:translateY(-4px) scale(1.01);}
    .g-card-img{height:130px;background:linear-gradient(135deg,#0A2540,#142f55);display:flex;align-items:center;justify-content:center;font-size:56px;border-bottom:1px solid rgba(0,229,192,.15);position:relative;overflow:hidden;}
    .g-card-img::after{content:'';position:absolute;inset:0;background:radial-gradient(ellipse at 50% 80%,rgba(157,78,221,.1) 0%,transparent 70%);pointer-events:none;}
    .g-card-body{padding:10px 13px 12px;}
    .g-card-title{font-family:'Playfair Display',serif;color:#dde8ff;font-size:12.5px;font-weight:700;line-height:1.35;min-height:32px;margin-bottom:4px;}
    .g-card-value{font-family:'Cinzel',serif;color:var(--gold);font-size:14px;font-weight:700;}
    .g-card-id{font-family:'DM Mono',monospace;color:var(--teal);font-size:8px;opacity:.6;margin-top:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
    .g-badge-gold{position:absolute;top:8px;right:8px;background:rgba(5,18,31,.9);border:1px solid var(--gold);border-radius:20px;padding:2px 9px;font-family:'Cinzel',serif;font-size:7.5px;color:var(--gold);letter-spacing:1px;}
    .g-badge-teal{position:absolute;bottom:8px;left:8px;background:rgba(0,229,192,.15);border:1px solid var(--teal);border-radius:20px;padding:2px 8px;font-family:'Cinzel',serif;font-size:7px;color:var(--teal);}
    .g-badge-purple{position:absolute;top:8px;left:8px;background:rgba(157,78,221,.25);border:1px solid #9D4EDD;border-radius:20px;padding:2px 8px;font-family:'Cinzel',serif;font-size:7px;color:#cc99ff;}
    .g-badge-locked{position:absolute;bottom:8px;right:8px;background:rgba(243,156,18,.2);border:1px solid #F39C12;border-radius:20px;padding:2px 8px;font-family:'Cinzel',serif;font-size:7px;color:#F39C12;}

    /* Hero */
    .g-hero{background:linear-gradient(135deg,#0b1d35 0%,#15284a 50%,#0a1827 100%);border:1px solid rgba(157,78,221,.5);border-radius:18px;padding:32px 40px;text-align:center;position:relative;overflow:hidden;margin-bottom:8px;}
    .g-hero::before{content:'';position:absolute;top:-60%;left:50%;transform:translateX(-50%);width:120%;height:120%;background:radial-gradient(ellipse,rgba(157,78,221,.1) 0%,transparent 65%);pointer-events:none;}
    .g-hero-title{font-family:'Cinzel',serif;font-size:clamp(20px,3vw,30px);font-weight:900;color:var(--gold);letter-spacing:5px;margin:0;text-shadow:0 0 30px rgba(242,201,76,.3);}
    .g-hero-sub{font-family:'DM Mono',monospace;color:var(--teal);font-size:11px;letter-spacing:3px;margin-top:8px;opacity:.9;}

    /* Quest Card */
    .q-card{background:linear-gradient(135deg,#0d1f3a,#112B4D);border:1px solid rgba(157,78,221,.4);border-radius:12px;padding:13px 16px;margin-bottom:9px;display:flex;align-items:center;gap:13px;transition:all .2s;position:relative;}
    .q-card:hover{border-color:rgba(242,201,76,.4);transform:translateX(3px);}
    .q-card.done{border-color:rgba(0,229,192,.4);background:linear-gradient(135deg,rgba(0,229,192,.04),rgba(0,229,192,.02));}
    .q-card.done::after{content:'✓';position:absolute;right:14px;top:50%;transform:translateY(-50%);color:var(--teal);font-size:18px;font-weight:700;}
    .q-icon{font-size:24px;min-width:32px;text-align:center;}
    .q-info{flex:1;}
    .q-title{font-family:'Cinzel',serif;color:var(--gold);font-size:12px;font-weight:700;margin-bottom:2px;}
    .q-desc{font-family:'DM Mono',monospace;color:#8899aa;font-size:10px;line-height:1.4;}
    .q-reward{font-family:'Cinzel',serif;color:var(--teal);font-size:12px;font-weight:700;white-space:nowrap;margin-right:26px;}

    /* Rank */
    .rank-pill{background:linear-gradient(135deg,#0d1f3a,#1c3560);border:2px solid var(--gold);border-radius:50px;padding:7px 22px;display:inline-block;font-family:'Cinzel',serif;color:var(--gold);font-size:13px;font-weight:700;letter-spacing:2px;box-shadow:0 0 20px rgba(242,201,76,.18),inset 0 0 10px rgba(242,201,76,.05);}

    /* Wallet */
    .wallet-card{background:linear-gradient(145deg,#0a1e38,#0d2540);border:2px solid rgba(242,201,76,.5);border-radius:16px;padding:24px;text-align:center;position:relative;overflow:hidden;margin-bottom:16px;}
    .wallet-card::before{content:'';position:absolute;top:-40%;left:50%;transform:translateX(-50%);width:80%;height:80%;background:radial-gradient(ellipse,rgba(242,201,76,.06) 0%,transparent 70%);}
    .wallet-amount{font-family:'Cinzel',serif;color:var(--gold);font-size:clamp(22px,4vw,36px);font-weight:900;letter-spacing:2px;text-shadow:0 0 20px rgba(242,201,76,.4);}
    .wallet-label{font-family:'DM Mono',monospace;color:var(--teal);font-size:10px;letter-spacing:3px;margin-top:4px;opacity:.85;}

    /* Royalty panel */
    .royalty-card{background:linear-gradient(145deg,rgba(242,201,76,.06),rgba(157,78,221,.06));border:1px solid rgba(242,201,76,.35);border-radius:14px;padding:18px 22px;margin:12px 0;}
    .royalty-title{font-family:'Cinzel',serif;color:var(--gold);font-size:12px;font-weight:700;letter-spacing:2px;margin-bottom:10px;}
    .royalty-row{display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid rgba(242,201,76,.08);}
    .royalty-row:last-child{border-bottom:none;}
    .royalty-key{font-family:'DM Mono',monospace;color:#8899aa;font-size:10px;}
    .royalty-val{font-family:'Cinzel',serif;color:var(--gold);font-size:11px;font-weight:700;}

    /* Tutor bubble */
    .tutor-chat{background:linear-gradient(135deg,rgba(13,30,60,.96),rgba(16,40,72,.96));border:1px solid rgba(0,229,192,.3);border-radius:16px;padding:18px 22px;margin:10px 0 4px;position:relative;}
    .tutor-chat::before{content:'';position:absolute;top:-7px;left:30px;width:13px;height:13px;background:#0d1f3a;border-left:1px solid rgba(0,229,192,.3);border-top:1px solid rgba(0,229,192,.3);transform:rotate(45deg);}
    .tutor-name{font-family:'Cinzel',serif;font-size:12px;font-weight:700;margin-bottom:8px;}
    .tutor-msg{font-family:'DM Mono',monospace;font-size:12px;color:#ccd6f0;line-height:1.75;}

    /* Marketplace */
    .mkt-row{background:linear-gradient(145deg,#0d1f3a,#112B4D);border:1px solid rgba(157,78,221,.32);border-radius:12px;padding:14px 16px;margin-bottom:10px;display:flex;align-items:center;gap:14px;transition:all .2s;}
    .mkt-row:hover{border-color:rgba(242,201,76,.4);box-shadow:0 4px 20px rgba(0,0,0,.3);}
    .mkt-emoji{font-size:30px;min-width:38px;text-align:center;}
    .mkt-name{font-family:'Playfair Display',serif;color:#dde8ff;font-size:13px;font-weight:700;}
    .mkt-seller{font-family:'DM Mono',monospace;color:#8899aa;font-size:10px;margin-top:2px;}
    .mkt-price{font-family:'Cinzel',serif;color:var(--gold);font-size:15px;font-weight:700;white-space:nowrap;}
    .mkt-royalty-note{font-family:'DM Mono',monospace;color:var(--teal);font-size:9px;opacity:.8;}

    /* Buy success */
    .buy-success{background:linear-gradient(135deg,rgba(46,204,113,.08),rgba(0,229,192,.06));border:1px solid rgba(46,204,113,.4);border-radius:14px;padding:20px 24px;margin:12px 0;}
    .buy-success-title{font-family:'Cinzel',serif;color:#2ECC71;font-size:14px;font-weight:700;margin-bottom:12px;}
    .buy-detail-row{display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid rgba(46,204,113,.1);}
    .buy-detail-key{font-family:'DM Mono',monospace;color:#8899aa;font-size:10px;}
    .buy-detail-val{font-family:'Cinzel',serif;color:#2ECC71;font-size:10px;font-weight:700;}

    /* Quest Banner */
    .quest-banner{background:linear-gradient(135deg,rgba(242,201,76,.1),rgba(157,78,221,.08));border:1px solid rgba(242,201,76,.4);border-radius:14px;padding:16px 20px;margin-bottom:16px;}
    .quest-banner-header{font-family:'Cinzel',serif;color:#F2C94C;font-size:13px;font-weight:700;margin-bottom:10px;}
    .quest-banner-total{color:#00E5C0;}
    .quest-banner-row{display:flex;align-items:center;gap:10px;padding:5px 0;border-bottom:1px solid rgba(242,201,76,.08);}
    .quest-banner-row:last-child{border-bottom:none;}
    .quest-banner-icon{font-size:16px;min-width:22px;}
    .quest-banner-name{font-family:'DM Mono',monospace;color:#ccd6f0;font-size:11px;flex:1;}
    .quest-banner-reward{font-family:'Cinzel',serif;color:#00E5C0;font-size:11px;font-weight:700;white-space:nowrap;}

    /* Activity */
    .act-item{display:flex;align-items:flex-start;gap:12px;padding:10px 0;border-bottom:1px solid rgba(157,78,221,.15);transition:background .15s;}
    .act-item:hover{background:rgba(157,78,221,.04);border-radius:8px;padding-left:6px;}
    .act-icon{font-size:18px;min-width:26px;text-align:center;margin-top:2px;}
    .act-info{flex:1;}
    .act-action{font-family:'Cinzel',serif;font-size:11px;font-weight:700;}
    .act-detail{font-family:'DM Mono',monospace;color:#8899aa;font-size:10px;margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:340px;}
    .act-time{font-family:'DM Mono',monospace;color:#8899aa;font-size:9px;white-space:nowrap;opacity:.7;text-align:right;min-width:80px;}

    /* Terminal */
    .term-block{background:rgba(0,0,0,.25);border:1px solid rgba(0,229,192,.14);border-radius:10px;padding:10px 13px;margin:5px 0;}
    .term-key{font-size:8px;color:#00E5C0;letter-spacing:1.5px;text-transform:uppercase;opacity:.8;}
    .term-val{font-family:'Cinzel',serif;color:#F2C94C;font-size:12px;font-weight:700;margin-top:1px;}

    /* Sponsor */
    .sp-row{display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid rgba(157,78,221,.15);}
    .sp-key{font-family:'DM Mono',monospace;color:#8899aa;font-size:9px;}
    .sp-val{font-family:'Cinzel',serif;color:#F2C94C;font-size:10px;font-weight:700;}

    /* Shimmer */
    @keyframes shimmer{0%{background-position:-200% center;}100%{background-position:200% center;}}
    .showcase-glow{background:linear-gradient(90deg,transparent 0%,rgba(242,201,76,.06) 30%,rgba(0,229,192,.06) 50%,rgba(242,201,76,.06) 70%,transparent 100%);background-size:200% auto;animation:shimmer 4s linear infinite;border-radius:14px;}

    /* Deep Q */
    .deep-q-btn .stButton>button{background:linear-gradient(135deg,rgba(243,156,18,.15),rgba(243,156,18,.08))!important;border:1px solid rgba(243,156,18,.6)!important;color:#F39C12!important;font-size:9px!important;}
    .deep-q-btn .stButton>button:hover{background:linear-gradient(135deg,rgba(243,156,18,.35),rgba(243,156,18,.2))!important;color:#FFFFFF!important;border-color:#F39C12!important;}

    /* Ledger */
    .ledger-table{width:100%;border-collapse:collapse;background:linear-gradient(135deg,#0d1f3a,#112B4D);border:1px solid rgba(157,78,221,.3);border-radius:12px;overflow:hidden;}
    .ledger-table th{padding:10px 14px;font-family:'Cinzel',serif;font-size:8.5px;color:#00E5C0;letter-spacing:2px;text-align:left;border-bottom:1px solid rgba(157,78,221,.4);}
    .ledger-table td{padding:9px 14px;font-family:'DM Mono',monospace;font-size:11px;border-bottom:1px solid rgba(157,78,221,.12);}
    .ledger-cat{background:rgba(157,78,221,.1);padding:6px 14px;font-family:'Cinzel',serif;font-size:8px;color:#9D4EDD;letter-spacing:2px;text-transform:uppercase;}

    /* ── LOAN CARD — v0.10.3 enhanced ── */
    .loan-card{background:linear-gradient(145deg,rgba(243,156,18,.06),rgba(157,78,221,.06));border:1px solid rgba(243,156,18,.4);border-radius:14px;padding:18px 22px;margin:10px 0;}
    .loan-card-title{font-family:'Cinzel',serif;color:#F39C12;font-size:13px;font-weight:700;letter-spacing:2px;margin-bottom:12px;}
    .loan-row{display:flex;justify-content:space-between;align-items:center;padding:6px 0;border-bottom:1px solid rgba(243,156,18,.1);}
    .loan-row:last-child{border-bottom:none;}
    .loan-key{font-family:'DM Mono',monospace;color:#8899aa;font-size:10px;}
    .loan-val{font-family:'Cinzel',serif;color:#F39C12;font-size:11px;font-weight:700;}
    .loan-danger{color:#FF6B6B!important;}
    .loan-warn{color:#F39C12!important;}
    .loan-ok{color:#2ECC71!important;}
    /* Countdown bar */
    .loan-countdown-wrap{height:6px;background:rgba(255,255,255,.08);border-radius:4px;overflow:hidden;margin-top:6px;}
    .loan-countdown-bar-ok{height:100%;border-radius:4px;background:linear-gradient(90deg,#2ECC71,#43e97b);}
    .loan-countdown-bar-warn{height:100%;border-radius:4px;background:linear-gradient(90deg,#F39C12,#f5c518);}
    .loan-countdown-bar-danger{height:100%;border-radius:4px;background:linear-gradient(90deg,#FF6B6B,#ff4444);}

    /* ── NOTIFICATION SYSTEM — v0.10.3 ── */
    .notif-panel{background:linear-gradient(145deg,#0a1628,#0d1f3a);border:1px solid rgba(0,229,192,.4);border-radius:16px;padding:0;overflow:hidden;margin-bottom:12px;box-shadow:0 8px 32px rgba(0,0,0,.5);}
    .notif-header{background:linear-gradient(135deg,rgba(0,229,192,.08),rgba(157,78,221,.06));padding:14px 20px;border-bottom:1px solid rgba(0,229,192,.2);display:flex;align-items:center;justify-content:space-between;}
    .notif-header-title{font-family:'Cinzel',serif;color:#00E5C0;font-size:12px;font-weight:700;letter-spacing:2px;}
    .notif-header-count{font-family:'DM Mono',monospace;color:#8899aa;font-size:10px;}
    .notif-list{padding:8px 0;max-height:320px;overflow-y:auto;}
    .notif-item{display:flex;align-items:flex-start;gap:12px;padding:10px 20px;border-bottom:1px solid rgba(157,78,221,.1);transition:background .15s;}
    .notif-item:last-child{border-bottom:none;}
    .notif-item:hover{background:rgba(157,78,221,.04);}
    .notif-item.unread{background:rgba(0,229,192,.03);border-left:3px solid rgba(0,229,192,.4);}
    .notif-icon{font-size:16px;min-width:20px;margin-top:2px;}
    .notif-content{flex:1;}
    .notif-title{font-family:'Cinzel',serif;font-size:11px;font-weight:700;color:#dde8ff;margin-bottom:2px;}
    .notif-body{font-family:'DM Mono',monospace;color:#8899aa;font-size:10px;line-height:1.5;}
    .notif-time{font-family:'DM Mono',monospace;color:#8899aa;font-size:8px;white-space:nowrap;opacity:.7;min-width:60px;text-align:right;}
    .notif-empty{font-family:'DM Mono',monospace;color:#8899aa;font-size:11px;padding:24px 20px;text-align:center;}
    /* Bell button override for unread badge display */
    .bell-wrapper{position:relative;display:inline-block;}

    @media(max-width:768px){.g-hero{padding:20px 16px;}.g-hero-title{font-size:18px;letter-spacing:2px;}.g-card-img{height:100px;font-size:44px;}.q-card{flex-wrap:wrap;}.q-reward{margin-right:0;}}
    </style>
    """, unsafe_allow_html=True)

inject_theme()


# ══════════════════════════════════════════════════════════════════════
# ⑥ DATA LAYER — columns + safe migration
# ══════════════════════════════════════════════════════════════════════
CREATION_COLS = [
    "id","name","sovereign","value","emoji","file_path",
    "created_at","is_fractional","cert_downloaded","fraction_count",
    "listed_price","listed_at","lore",
    "original_creator","royalty_pct","total_royalties","is_locked","lock_reason","transfer_count",
]
USER_COLS     = ["kingdom","pw_hash","dob","sponsor_kingdom","sponsor_pw_hash"]
WALLET_COLS   = ["sovereign","imagix","total_royalties_earned"]
MARKET_COLS   = ["id","name","sovereign","value","emoji","listed_price","listed_at","original_creator","royalty_pct"]
ACTIVITY_COLS = ["ts","sovereign","action","detail"]
LOAN_COLS     = ["loan_id","sovereign","asset_id","asset_name","asset_value",
                 "loan_amount","due_date","opened_at","status"]
AUCTION_COLS  = ["auction_id","sovereign","asset_id","asset_name","starting_price",
                 "current_bid","current_bidder","ends_at","status"]
# v0.10.3 NEW
NOTIF_COLS    = ["notif_id","recipient","type","title","body","icon","is_read","created_at"]

CREATION_DEFAULTS = {
    "original_creator": "",
    "royalty_pct":      str(DEFAULT_ROYALTY_PCT),
    "total_royalties":  "0",
    "is_locked":        "False",
    "lock_reason":      "",
    "transfer_count":   "0",
}
WALLET_DEFAULTS = {
    "total_royalties_earned": "0",
}

def ensure_dirs(user: str):
    Path(F["dir"]).mkdir(exist_ok=True)
    Path(f"{F['dir']}/{user}").mkdir(parents=True, exist_ok=True)

def _read(path: str, cols: list) -> pd.DataFrame:
    if os.path.exists(path):
        try:
            df = pd.read_csv(path, dtype=str).fillna("")
            for c in cols:
                if c not in df.columns: df[c] = ""
            return df[cols]
        except Exception: pass
    return pd.DataFrame(columns=cols)

def _write(df: pd.DataFrame, path: str):
    """Atomic write via temp file — prevents corruption on partial writes."""
    try:
        tmp = path + ".tmp"
        df.to_csv(tmp, index=False)
        os.replace(tmp, path)
    except Exception as e:
        st.toast(f"⚠️ Save error: {e}", icon="⚠️")

def migrate_creations():
    if not os.path.exists(F["creations"]): return
    df = _read(F["creations"], CREATION_COLS)
    changed = False
    for col, default in CREATION_DEFAULTS.items():
        if col == "original_creator":
            mask = df["original_creator"] == ""
            if mask.any():
                df.loc[mask, "original_creator"] = df.loc[mask, "sovereign"]
                changed = True
        elif col in df.columns and (df[col] == "").any():
            df.loc[df[col] == "", col] = default
            changed = True
    if changed:
        _write(df, F["creations"])

def migrate_wallets():
    if not os.path.exists(F["wallets"]): return
    df = _read(F["wallets"], WALLET_COLS)
    changed = False
    for col, default in WALLET_DEFAULTS.items():
        if col not in df.columns or (df[col] == "").all():
            df[col] = default
            changed = True
    if changed:
        _write(df, F["wallets"])

def load_creations() -> pd.DataFrame: return _read(F["creations"], CREATION_COLS)
def save_creations(df): _write(df, F["creations"])
def load_market() -> pd.DataFrame:    return _read(F["market"],    MARKET_COLS)
def save_market(df):  _write(df, F["market"])
def load_users() -> pd.DataFrame:     return _read(F["users"],     USER_COLS)
def save_users(df):   _write(df, F["users"])
def load_loans() -> pd.DataFrame:     return _read(F["loans"],     LOAN_COLS)
def save_loans(df):   _write(df, F["loans"])
def load_auctions() -> pd.DataFrame:  return _read(F["auctions"],  AUCTION_COLS)
def save_auctions(df): _write(df, F["auctions"])

def load_wallet(user: str) -> int:
    df = _read(F["wallets"], WALLET_COLS)
    row = df[df.sovereign == user]
    if not row.empty:
        try: return int(float(str(row.iloc[0]["imagix"])))
        except: pass
    return 0

def load_wallet_royalties(user: str) -> int:
    df = _read(F["wallets"], WALLET_COLS)
    row = df[df.sovereign == user]
    if not row.empty:
        raw = str(row.iloc[0]["total_royalties_earned"]).strip()
        if raw in ("", "nan", "None"): raw = "0"
        try: return int(float(raw))
        except: pass
    return 0

def save_wallet(user: str, imagix: int, royalties_delta: int = 0):
    df = _read(F["wallets"], WALLET_COLS)
    if user in df.sovereign.values:
        df.loc[df.sovereign == user, "imagix"] = str(imagix)
        if royalties_delta > 0:
            old_r = safe_int(df.loc[df.sovereign == user, "total_royalties_earned"].values[0])
            df.loc[df.sovereign == user, "total_royalties_earned"] = str(old_r + royalties_delta)
    else:
        df = pd.concat([df, pd.DataFrame([{
            "sovereign": user, "imagix": str(imagix),
            "total_royalties_earned": str(royalties_delta),
        }])], ignore_index=True)
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


# ══════════════════════════════════════════════════════════════════════
# ACTIVITY LOG — v0.10.2 hardened (unchanged)
# ══════════════════════════════════════════════════════════════════════
def log_activity(sovereign: str, action: str, detail: str = ""):
    row = {
        "ts":       datetime.now().isoformat(timespec="milliseconds"),
        "sovereign": sovereign,
        "action":   action,
        "detail":   str(detail)[:300],
    }
    df = _read(F["activity"], ACTIVITY_COLS)
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df = df.sort_values("ts", ascending=True, na_position="last").tail(500).reset_index(drop=True)
    _write(df, F["activity"])

def load_activity(user: str, n: int = 20) -> list:
    df = _read(F["activity"], ACTIVITY_COLS)
    if df.empty: return []
    udf = df[df["sovereign"] == user].copy()
    if udf.empty: return []
    udf["_ts_sort"] = pd.to_datetime(udf["ts"], errors="coerce")
    udf = udf.sort_values("_ts_sort", ascending=False, na_position="last").head(n)
    udf = udf.drop(columns=["_ts_sort"])
    return udf.to_dict("records")


# ══════════════════════════════════════════════════════════════════════
# NOTIFICATIONS — v0.10.3 DISK-BACKED (replaces session-only)
# ══════════════════════════════════════════════════════════════════════
def push_notification(recipient: str, ntype: str, title: str, body: str, icon: str = "⚡"):
    """
    v0.10.3: Write notification to genesis_notifications.csv.
    Persists across page refreshes. Unread badge reads from disk.
    """
    row = {
        "notif_id":   "NID-" + uuid.uuid4().hex[:8].upper(),
        "recipient":  recipient,
        "type":       ntype,
        "title":      str(title)[:80],
        "body":       str(body)[:240],
        "icon":       icon,
        "is_read":    "False",
        "created_at": datetime.now().isoformat(timespec="milliseconds"),
    }
    df = _read(F["notifications"], NOTIF_COLS)
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    # Keep last 200 notifications total (all users combined)
    df = df.tail(200).reset_index(drop=True)
    _write(df, F["notifications"])

def load_notifications(user: str, n: int = 20, unread_only: bool = False) -> list:
    """Load notifications for a user from disk, newest first."""
    df = _read(F["notifications"], NOTIF_COLS)
    if df.empty: return []
    udf = df[df["recipient"] == user].copy()
    if udf.empty: return []
    if unread_only:
        udf = udf[udf["is_read"] == "False"]
    udf["_ts_sort"] = pd.to_datetime(udf["created_at"], errors="coerce")
    udf = udf.sort_values("_ts_sort", ascending=False, na_position="last").head(n)
    udf = udf.drop(columns=["_ts_sort"])
    return udf.to_dict("records")

def count_unread(user: str) -> int:
    """Count unread notifications for user from disk."""
    df = _read(F["notifications"], NOTIF_COLS)
    if df.empty: return 0
    return int(((df["recipient"] == user) & (df["is_read"] == "False")).sum())

def mark_all_read(user: str):
    """Mark all user notifications as read on disk."""
    df = _read(F["notifications"], NOTIF_COLS)
    if df.empty: return
    df.loc[df["recipient"] == user, "is_read"] = "True"
    _write(df, F["notifications"])

def clear_notifications(user: str):
    """Delete all notifications for a user."""
    df = _read(F["notifications"], NOTIF_COLS)
    if df.empty: return
    df = df[df["recipient"] != user].copy()
    _write(df, F["notifications"])


def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

def register_user(kingdom, pw, dob_str, sponsor="", sponsor_pw="") -> tuple:
    df = load_users()
    if kingdom in df.kingdom.values: return False, "Kingdom name already taken."
    new = {
        "kingdom": kingdom, "pw_hash": hash_pw(pw), "dob": dob_str,
        "sponsor_kingdom": sponsor,
        "sponsor_pw_hash": hash_pw(sponsor_pw) if sponsor_pw else "",
    }
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

def get_user_row(kingdom):
    df  = load_users()
    row = df[df.kingdom == kingdom]
    return row.iloc[0].to_dict() if not row.empty else None

def get_user_dob(kingdom):
    urow = get_user_row(kingdom)
    if urow:
        try: return datetime.strptime(str(urow["dob"]), "%Y-%m-%d").date()
        except: pass
    return None

def calc_age(dob) -> int:
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

def img_to_b64(path: str):
    try:
        if not path or not os.path.exists(path): return None
        if not path.lower().endswith((".jpg",".jpeg",".png")): return None
        with open(path,"rb") as f: data = base64.b64encode(f.read()).decode()
        ext  = Path(path).suffix.lower().lstrip(".")
        mime = {"jpg":"jpeg","jpeg":"jpeg","png":"png"}.get(ext,"jpeg")
        return f"data:image/{mime};base64,{data}"
    except Exception: return None


# ══════════════════════════════════════════════════════════════════════
# ⑦ CREATOR ECONOMY — execute_sale + lock/unlock
# ══════════════════════════════════════════════════════════════════════
def execute_sale(asset_id: str, buyer: str, seller: str, price: int,
                 transaction_type: str = "MARKETPLACE") -> dict:
    """
    Central sale execution. Handles royalties automatically.
    v0.10.2 hardened: SOLD logged first, atomic wallet snapshot,
    disk notifications for all parties.
    """
    result = {
        "success": False, "buyer_paid": price, "seller_received": price,
        "royalty_amount": 0, "royalty_to": "", "message": "", "seller": seller,
    }
    try:
        cdf = load_creations()
        asset_rows = cdf[cdf["id"] == asset_id]
        if asset_rows.empty:
            result["message"] = "Asset not found."
            return result

        asset = asset_rows.iloc[0]
        if str(asset.get("is_locked","")).lower() == "true":
            result["message"] = "Asset is locked: {}".format(asset.get("lock_reason",""))
            return result

        original_creator = str(asset.get("original_creator","")).strip() or seller
        royalty_pct      = safe_int(asset.get("royalty_pct", str(DEFAULT_ROYALTY_PCT)), DEFAULT_ROYALTY_PCT)
        transfer_count   = safe_int(asset.get("transfer_count","0"), 0)
        old_total_roy    = safe_int(asset.get("total_royalties","0"), 0)
        asset_name       = str(asset.get("name",""))[:40]

        is_secondary   = (original_creator and original_creator != seller)
        royalty_amount = 0
        if is_secondary and royalty_pct > 0 and transaction_type == "MARKETPLACE":
            royalty_amount = int(price * royalty_pct / 100)

        seller_receives = price - royalty_amount

        # Atomic wallet snapshot
        buyer_current   = load_wallet(buyer)
        seller_current  = load_wallet(seller)
        creator_current = load_wallet(original_creator) if (royalty_amount > 0 and original_creator != seller) else 0

        save_wallet(buyer, buyer_current - price)
        save_wallet(seller, seller_current + seller_receives)

        if royalty_amount > 0 and original_creator and original_creator != seller:
            save_wallet(original_creator, creator_current + royalty_amount, royalties_delta=royalty_amount)
            cdf.loc[cdf["id"] == asset_id, "total_royalties"] = str(old_total_roy + royalty_amount)
            result["royalty_amount"] = royalty_amount
            result["royalty_to"]     = original_creator

        cdf.loc[cdf["id"] == asset_id, "sovereign"]      = buyer
        cdf.loc[cdf["id"] == asset_id, "listed_price"]   = ""
        cdf.loc[cdf["id"] == asset_id, "listed_at"]      = ""
        cdf.loc[cdf["id"] == asset_id, "transfer_count"] = str(transfer_count + 1)
        save_creations(cdf)

        mdf = load_market()
        save_market(mdf[mdf["id"] != asset_id].copy())

        result["success"]         = True
        result["seller_received"] = seller_receives
        result["message"]         = "Sale completed."

        # ── Activity logs: SOLD first (seller critical) ──
        log_activity(seller, "SOLD",
                     "{} to {} @ {:,} [{}]".format(asset_id, buyer, price, transaction_type))
        log_activity(buyer, "BUY",
                     "{} from {} @ {:,} [{}]".format(asset_id, seller, price, transaction_type))

        # ── Disk notifications ──
        push_notification(
            seller, "SOLD",
            "Sale Completed: {}".format(asset_name),
            "Sold to {} for {:,} I. You received {:,} I.".format(buyer, price, seller_receives),
            icon="🤝",
        )
        push_notification(
            buyer, "BUY",
            "Purchase Confirmed: {}".format(asset_name),
            "Acquired from {} for {:,} I. Check your Vault!".format(seller, price),
            icon="💰",
        )

        if result["royalty_amount"] > 0:
            log_activity(result["royalty_to"], "ROYALTY",
                         "{:,} I royalty from {} sale of {}".format(
                             result["royalty_amount"], transaction_type, asset_id))
            push_notification(
                result["royalty_to"], "ROYALTY",
                "Royalty Earned: {}".format(asset_name),
                "{:,} I royalty — {} sold your creation for {:,} I.".format(
                    result["royalty_amount"], seller, price),
                icon="👑",
            )

    except Exception as e:
        result["message"] = str(e)

    return result


def lock_asset(asset_id: str, reason: str) -> bool:
    try:
        cdf = load_creations()
        if asset_id not in cdf["id"].values: return False
        cdf.loc[cdf["id"] == asset_id, "is_locked"]   = "True"
        cdf.loc[cdf["id"] == asset_id, "lock_reason"] = reason
        save_creations(cdf)
        return True
    except Exception: return False

def unlock_asset(asset_id: str) -> bool:
    try:
        cdf = load_creations()
        if asset_id not in cdf["id"].values: return False
        cdf.loc[cdf["id"] == asset_id, "is_locked"]   = "False"
        cdf.loc[cdf["id"] == asset_id, "lock_reason"] = ""
        save_creations(cdf)
        return True
    except Exception: return False


# ══════════════════════════════════════════════════════════════════════
# LOANS ENGINE — v0.10.3 polished
# ══════════════════════════════════════════════════════════════════════
def open_loan(sovereign: str, asset_id: str, asset_name: str,
              asset_value: int, is_minor: bool) -> dict:
    result = {"success": False, "loan_amount": 0, "message": ""}

    if is_minor and not st.session_state.get(SPONSOR_SESSION_KEY, False):
        result["message"] = "Sponsor approval required. Verify your Sponsor in the sidebar first."
        return result

    cdf = load_creations()
    rows = cdf[cdf["id"] == asset_id]
    if rows.empty:
        result["message"] = "Asset not found."
        return result
    if str(rows.iloc[0].get("is_locked","")).lower() == "true":
        result["message"] = "This asset is already locked as collateral or in use."
        return result

    loans = load_loans()
    if not loans.empty:
        existing = loans[(loans["asset_id"] == asset_id) & (loans["status"] == "OPEN")]
        if not existing.empty:
            result["message"] = "An open loan already exists for this asset."
            return result

    loan_amount = int(asset_value * LOAN_LTV_PCT / 100)
    if loan_amount < 100:
        result["message"] = "Asset value too low for a loan (minimum 167 IMAGIX asset value)."
        return result

    due_date = (date.today() + timedelta(days=LOAN_TERM_DAYS)).isoformat()
    loan_id  = "LOAN-" + hashlib.sha256(
        "{}::{}::{}".format(sovereign, asset_id, datetime.now().isoformat()).encode()
    ).hexdigest()[:8].upper()

    if not lock_asset(asset_id, "Collateral · loan {}".format(loan_id)):
        result["message"] = "Failed to lock asset as collateral."
        return result

    current_bal = load_wallet(sovereign)
    save_wallet(sovereign, current_bal + loan_amount)

    new_loan = {
        "loan_id":     loan_id,
        "sovereign":   sovereign,
        "asset_id":    asset_id,
        "asset_name":  asset_name,
        "asset_value": str(asset_value),
        "loan_amount": str(loan_amount),
        "due_date":    due_date,
        "opened_at":   date.today().isoformat(),
        "status":      "OPEN",
    }
    loans = pd.concat([loans, pd.DataFrame([new_loan])], ignore_index=True)
    save_loans(loans)

    log_activity(sovereign, "LOAN_OPEN",
                 "{} · {:,} I · due {}".format(loan_id, loan_amount, due_date))
    push_notification(
        sovereign, "LOAN_OPEN",
        "Loan Opened: {}".format(loan_id),
        "{:,} I credited. Repay {:,} I by {} or asset transfers to Genesis Treasury.".format(
            loan_amount, loan_amount, due_date),
        icon="🏦",
    )

    st.session_state["imagix"] = load_wallet(sovereign)

    result["success"]     = True
    result["loan_amount"] = loan_amount
    result["loan_id"]     = loan_id
    result["due_date"]    = due_date
    result["message"]     = "Loan opened successfully."
    return result


def repay_loan(loan_id: str, sovereign: str) -> dict:
    result = {"success": False, "message": ""}

    loans     = load_loans()
    loan_rows = loans[(loans["loan_id"] == loan_id) & (loans["sovereign"] == sovereign)]
    if loan_rows.empty:
        result["message"] = "Loan not found."
        return result

    loan = loan_rows.iloc[0]
    if str(loan["status"]) != "OPEN":
        result["message"] = "Loan is not active."
        return result

    loan_amount = safe_int(loan["loan_amount"])
    current_bal = load_wallet(sovereign)
    if current_bal < loan_amount:
        result["message"] = "Insufficient IMAGIX. Need {:,} I, have {:,} I.".format(
            loan_amount, current_bal)
        return result

    save_wallet(sovereign, current_bal - loan_amount)
    unlock_asset(str(loan["asset_id"]))
    loans.loc[loans["loan_id"] == loan_id, "status"] = "REPAID"
    save_loans(loans)

    st.session_state["imagix"] = load_wallet(sovereign)
    st.session_state["creations_df"] = load_creations()

    log_activity(sovereign, "LOAN_REPAY",
                 "{} · {:,} I repaid · asset unlocked".format(loan_id, loan_amount))
    push_notification(
        sovereign, "LOAN_REPAY",
        "Loan Repaid: {}".format(loan_id),
        "{:,} I repaid. Asset '{}' is unlocked and back in your Vault.".format(
            loan_amount, str(loan.get("asset_name",""))[:30]),
        icon="✅",
    )

    result["success"] = True
    result["message"] = "Loan repaid. Asset unlocked and returned to Vault."
    return result


def process_loan_defaults(sovereign: str):
    """
    Idempotent check for overdue loans. Called every page load.
    Friendly default message — no punishment language.
    """
    loans = load_loans()
    if loans.empty: return
    today = date.today().isoformat()
    open_loans = loans[(loans["sovereign"] == sovereign) & (loans["status"] == "OPEN")]
    if open_loans.empty: return

    changed = False
    for _, loan in open_loans.iterrows():
        due = str(loan["due_date"])
        if due and due < today:
            cdf = load_creations()
            aid = str(loan["asset_id"])
            cdf.loc[cdf["id"] == aid, "sovereign"]    = GENESIS_TREASURY
            cdf.loc[cdf["id"] == aid, "is_locked"]    = "False"
            cdf.loc[cdf["id"] == aid, "lock_reason"]  = ""
            cdf.loc[cdf["id"] == aid, "listed_price"] = ""
            save_creations(cdf)

            loans.loc[loans["loan_id"] == loan["loan_id"], "status"] = "DEFAULTED"
            changed = True

            aname = str(loan.get("asset_name","your creation"))[:30]
            log_activity(sovereign, "LOAN_DEFAULT",
                         "{} · asset {} to Genesis Treasury".format(loan["loan_id"], aid))
            push_notification(
                sovereign, "LOAN_DEFAULT",
                "Loan Ended: {}".format(loan["loan_id"]),
                "Your creation '{}' went to the Genesis Treasury to help other Sovereigns. You can always create more!".format(aname),
                icon="⚠️",
            )

    if changed:
        save_loans(loans)
        st.session_state["creations_df"] = load_creations()


def get_loan_urgency(due_date_str: str) -> tuple:
    """
    Returns (days_left, urgency_class, pct_remaining, label).
    urgency_class: 'ok' | 'warn' | 'danger'
    """
    try:
        days_left = (date.fromisoformat(due_date_str) - date.today()).days
    except Exception:
        days_left = 0

    total = LOAN_TERM_DAYS
    pct   = max(0.0, min(1.0, days_left / total)) if total > 0 else 0.0

    if days_left < 0:
        return days_left, "danger", 0.0, "OVERDUE"
    elif days_left <= 5:
        return days_left, "danger", pct, f"{days_left}d left — URGENT"
    elif days_left <= 10:
        return days_left, "warn",   pct, f"{days_left} days left"
    else:
        return days_left, "ok",     pct, f"{days_left} days remaining"


# ══════════════════════════════════════════════════════════════════════
# ⑧ RANK ENGINE
# ══════════════════════════════════════════════════════════════════════
def get_rank(imagix: int) -> dict:
    name, curr = RANK_TIERS[0][1], 0
    nxt = RANK_TIERS[1][0]
    for i,(t,n,_) in enumerate(RANK_TIERS):
        if imagix >= t:
            name, curr = n, t
            nxt = RANK_TIERS[i+1][0] if i+1 < len(RANK_TIERS) else t
    span = nxt - curr
    prog = min((imagix - curr) / span, 1.0) if span > 0 else 1.0
    return {"name":name,"progress":prog,"curr":curr,"next":nxt,"maxed":nxt==curr}


# ══════════════════════════════════════════════════════════════════════
# ⑨ QUEST ENGINE
# ══════════════════════════════════════════════════════════════════════
def run_quests(df: pd.DataFrame, user: str) -> int:
    ss_extra = {
        "imagix":       st.session_state.get("imagix",0),
        "cert_ever":    st.session_state.get("cert_ever",False),
        "tutor_used":   st.session_state.get("tutor_used",False),
        "deep_q_used":  st.session_state.get("deep_q_used",False),
        "sold_ever":    st.session_state.get("sold_ever",False),
        "bought_ever":  st.session_state.get("bought_ever",False),
        "lore_added":   st.session_state.get("lore_added",False),
        "has_sponsor":  st.session_state.get("has_sponsor",False),
        "royalty_ever": st.session_state.get("royalty_ever",False),
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
        log_activity(user, "QUESTS_DONE", ",".join(q["id"] for q in newly))
        # Push disk notification for quest completions
        total_reward = sum(q["reward"] for q in newly)
        titles = ", ".join(q["title"] for q in newly)
        push_notification(
            user, "QUEST",
            "{} {} Completed!".format(len(newly), "Quest" if len(newly)==1 else "Quests"),
            "{} · +{:,} IMAGIX earned".format(titles, total_reward),
            icon="⚡",
        )

    return delta


# ══════════════════════════════════════════════════════════════════════
# ⑩ QUEST BANNER
# ══════════════════════════════════════════════════════════════════════
def render_quest_banner():
    banner_quests = st.session_state.get("quest_banner", [])
    if not banner_quests: return

    count        = len(banner_quests)
    total_reward = sum(q.get("reward", 0) for q in banner_quests)
    header_text  = "Quest Completed!" if count == 1 else "{} Quests Completed!".format(count)

    rows = []
    for q in banner_quests:
        rows.append(
            '<div class="quest-banner-row">'
            '<span class="quest-banner-icon">{}</span>'
            '<span class="quest-banner-name">{}</span>'
            '<span class="quest-banner-reward">+{:,} IMAGIX</span>'
            '</div>'.format(q.get("icon",""), q.get("title",""), q.get("reward",0))
        )

    parts = [
        '<div class="quest-banner">',
        '<div class="quest-banner-header">&#9889; ',
        header_text,
        ' &nbsp;&middot;&nbsp; <span class="quest-banner-total">+{:,} IMAGIX earned</span>'.format(total_reward),
        '</div>',
        "\n".join(rows),
        "</div>",
    ]
    st.markdown("".join(parts), unsafe_allow_html=True)

    if st.button("✕ Dismiss", key="dismiss_banner"):
        st.session_state["quest_banner"] = []
        st.rerun()


# ══════════════════════════════════════════════════════════════════════
# ⑪ NOTIFICATION BELL RENDERER — v0.10.3
# ══════════════════════════════════════════════════════════════════════
def render_notification_panel(user: str):
    """
    Renders the full notification panel when bell is toggled.
    Reads from disk — persists across refreshes.
    """
    notifs = load_notifications(user, n=20)
    unread = sum(1 for n in notifs if str(n.get("is_read","False")) == "False")

    # Panel header
    parts = [
        '<div class="notif-panel">',
        '<div class="notif-header">',
        '<span class="notif-header-title">🔔 NOTIFICATIONS</span>',
        '<span class="notif-header-count">{} unread · {} total</span>'.format(unread, len(notifs)),
        '</div>',
        '<div class="notif-list">',
    ]

    if not notifs:
        parts.append('<div class="notif-empty">No notifications yet. Your activity will appear here.</div>')
    else:
        for n in notifs:
            ntype    = str(n.get("type","SYSTEM"))
            meta     = NOTIF_TYPES.get(ntype, ("⚡","purple","Notification"))
            icon     = str(n.get("icon","")) or meta[0]
            title    = str(n.get("title",""))
            body     = str(n.get("body",""))
            is_read  = str(n.get("is_read","False")) == "True"
            ts_raw   = str(n.get("created_at",""))

            try:
                dt     = datetime.fromisoformat(ts_raw)
                ts_fmt = dt.strftime("%H:%M · %b %d")
            except Exception:
                ts_fmt = ts_raw[:10]

            color_key = meta[1]
            color_val = C.get(color_key, C["muted"])
            item_cls  = "notif-item" if is_read else "notif-item unread"

            parts.append(
                '<div class="{}">'
                '<div class="notif-icon" style="color:{};">{}</div>'
                '<div class="notif-content">'
                '<div class="notif-title" style="color:{};">{}</div>'
                '<div class="notif-body">{}</div>'
                '</div>'
                '<div class="notif-time">{}</div>'
                '</div>'.format(item_cls, color_val, icon, color_val, title, body, ts_fmt)
            )

    parts += ['</div></div>']
    st.markdown("".join(parts), unsafe_allow_html=True)

    # Action buttons
    nc1, nc2, nc3 = st.columns([1.5, 1, 1])
    with nc1:
        if st.button("✕ Close panel", key="notif_close"):
            st.session_state["notif_panel_open"] = False
            st.rerun()
    with nc2:
        if unread > 0 and st.button("✓ Mark all read", key="notif_mark_read"):
            mark_all_read(user)
            st.rerun()
    with nc3:
        if notifs and st.button("🗑 Clear all", key="notif_clear"):
            clear_notifications(user)
            st.session_state["notif_panel_open"] = False
            st.rerun()


# ══════════════════════════════════════════════════════════════════════
# ⑫ TUTORS — API + rich fallbacks
# ══════════════════════════════════════════════════════════════════════
def call_claude(prompt: str, max_tokens: int = 300):
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
        "vault":    "El usuario ve su Vault con {} creaciones.".format(n_c),
        "upload":   "El usuario esta en la pantalla de subir una nueva creacion.",
        "quests":   "El usuario ve sus Quests. Lleva {} completadas.".format(n_q),
        "wallet":   "El usuario ve su Wallet con {:,} IMAGIX.".format(imagix),
        "market":   "El usuario explora el Marketplace.",
        "activity": "El usuario ve su historial de actividad en Delphia Genesis.",
        "loans":    "El usuario esta explorando el sistema de Loans colateralizados. LTV 60%.",
        "default":  "El usuario {} explora Delphia Genesis.".format(user),
    }
    prompt = (
        "{}\n\nCONTEXTO: {}\nUSUARIO: '{}' · {} creaciones · {:,} IMAGIX · {} quests.\n"
        "Da UN mensaje corto en tu voz. Especifico al contexto. Sin asteriscos. Solo el mensaje."
    ).format(
        tutor["persona"], ctx_map.get(context_tab, ctx_map["default"]),
        user, n_c, imagix, n_q
    )
    return call_claude(prompt) or tutor["fallbacks"].get(context_tab, tutor["fallbacks"]["default"])

def get_deep_answer(tutor: dict, question: str, user: str, df: pd.DataFrame) -> str:
    n_c    = _q_count(df, user)
    imagix = st.session_state.get("imagix", 0)
    prompt = (
        "{}\n\nEl usuario {} ({} creaciones, {:,} IMAGIX) pregunta:\n'{}'\n\n"
        "Responde en tu voz. Maximo 6 oraciones. Sin asteriscos. Solo la respuesta."
    ).format(tutor["persona"], user, n_c, imagix, question)
    return (
        call_claude(prompt, max_tokens=500)
        or "Esa es una pregunta fascinante, Soberano {}. En el Genesis Layer, "
           "cada creacion lleva el peso de la imaginacion que la origino. "
           "Reflexiona, esa es la verdadera sabiduria.".format(user)
    )


# ══════════════════════════════════════════════════════════════════════
# ⑬ PDF CERTIFICATE (unchanged, version bumped)
# ══════════════════════════════════════════════════════════════════════
def make_certificate(name: str, asset_id: str, sovereign: str, value: int) -> bytes:
    buf  = io.BytesIO()
    W, H = A4
    c    = rl_canvas.Canvas(buf, pagesize=A4)
    c.setTitle("Genesis Certificate - {}".format(name))

    c.setFillColor(HexColor("#04101e")); c.rect(0,0,W,H,fill=1,stroke=0)
    rng = random.Random(42)
    for _ in range(120):
        sx, sy = rng.uniform(22,W-22), rng.uniform(55,H-55)
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
    c.drawCentredString(W/2,H-88,"  CERTIFICATE OF IMAGINATION  *  GENESIS LAYER v0.10.3  ")

    star_cy = H-192
    def draw_star(cx,cy,ro,ri,pts=5):
        path = c.beginPath()
        for i in range(pts*2):
            angle = math.pi/pts*i - math.pi/2
            r_    = ro if i%2==0 else ri
            x,y   = cx+r_*math.cos(angle), cy+r_*math.sin(angle)
            path.moveTo(x,y) if i==0 else path.lineTo(x,y)
        path.close(); c.drawPath(path,fill=1,stroke=1)
    for r,a in [(60,.06),(46,.10),(34,.08)]:
        c.setFillColorRGB(.95,.79,.30,alpha=a); c.circle(W/2,star_cy,r,fill=1,stroke=0)
    c.setFillColor(HexColor(C["gold"])); c.setStrokeColor(HexColor(C["purple"])); c.setLineWidth(1.2)
    draw_star(W/2,star_cy,36,15)
    c.setStrokeColor(HexColor(C["teal"])); c.setLineWidth(.7)
    c.setFillColorRGB(0,0,0,alpha=0); c.circle(W/2,star_cy,54,fill=0,stroke=1)

    ry = H-240
    c.setStrokeColor(HexColor(C["purple"])); c.setLineWidth(.7); c.line(44,ry,W-44,ry)
    c.setStrokeColor(HexColor(C["gold"]));   c.setLineWidth(.35); c.line(54,ry-5,W-54,ry-5)

    def draw_field(lbl,val,y):
        c.setFillColor(HexColor(C["teal"])); c.setFont("Helvetica",7.5)
        c.drawCentredString(W/2,y+17,lbl.upper())
        c.setStrokeColor(HexColor(C["purple"])); c.setLineWidth(.35)
        c.line(72,y+13,W-72,y+13)
        c.setFillColor(HexColor(C["white"])); c.setFont("Helvetica-Bold",13)
        disp = (val[:50]+"...") if len(val)>50 else val
        c.drawCentredString(W/2,y,disp)

    sha256 = hashlib.sha256("{}::{}::{}".format(asset_id,name,sovereign).encode()).hexdigest().upper()
    fields = [
        ("Creation",        str(name)[:55]),
        ("Genesis ID",      str(asset_id)),
        ("Young Sovereign", str(sovereign)[:45]),
        ("Imagined Value",  "{:,} IMAGIX".format(safe_int(value))),
        ("Date Sealed",     datetime.now().strftime("%d %B %Y").upper()),
        ("Status",          "SACRED & IMMUTABLE"),
    ]
    fy, gap = H-282, 47
    for i,(lbl,v) in enumerate(fields): draw_field(lbl,v,fy-i*gap)

    hash_y = fy-len(fields)*gap-20
    c.setFillColorRGB(.04,.10,.19,alpha=.82)
    c.roundRect(34,hash_y-30,W-68,48,6,fill=1,stroke=0)
    c.setStrokeColor(HexColor(C["purple"])); c.setLineWidth(.5)
    c.roundRect(34,hash_y-30,W-68,48,6,fill=0,stroke=1)
    c.setFillColor(HexColor(C["teal"])); c.setFont("Helvetica",7)
    c.drawCentredString(W/2,hash_y+10,"GENESIS HASH  SHA-256 INTEGRITY SEAL")
    c.setFillColor(HexColor(C["gold"])); c.setFont("Helvetica-Bold",7.5)
    c.drawCentredString(W/2,hash_y-10,sha256[:32])
    c.drawCentredString(W/2,hash_y-22,sha256[32:])

    bot_y = hash_y-46
    c.setStrokeColor(HexColor(C["gold"]));   c.setLineWidth(.7);  c.line(44,bot_y,W-44,bot_y)
    c.setStrokeColor(HexColor(C["purple"])); c.setLineWidth(.35); c.line(54,bot_y-5,W-54,bot_y-5)
    sig_y = bot_y-46
    c.setFillColor(HexColor(C["purple"])); c.setFont("Helvetica",8)
    c.drawCentredString(W/2,sig_y+16,"Signed by the Keeper of the Genesis Layer")
    c.setFillColor(HexColor(C["gold"])); c.setFont("Helvetica-Bold",11)
    c.drawCentredString(W/2,sig_y,"REY DELPHI  *  REINO DE DELPHIA  *  KARDASHEV VI")
    c.setFillColor(HexColor(C["teal"])); c.setFont("Helvetica",7)
    c.drawCentredString(W/2,28,"Delphia Genesis v0.10.3  *  Where Imagination Becomes Sovereign  *  delphia.genesis")
    c.save()
    return buf.getvalue()


# ══════════════════════════════════════════════════════════════════════
# ⑭ SESSION STATE
# ══════════════════════════════════════════════════════════════════════
_SS = {
    "authenticated": False, "user": "", "imagix": 0,
    "quest_completed": set(), "creations_df": None,
    "cert_ever": False,
    "split_open": {},
    "tutor_open": None, "tutor_used": False, "deep_q_used": False,
    "lore_added": False, "sold_ever": False, "bought_ever": False,
    "has_sponsor": False, "royalty_ever": False,
    SPONSOR_SESSION_KEY: False,
    "parent_mode": False, "sponsor_viewed_qs": False, "deep_q_open": None,
    "quest_banner": [],
    "buy_feedback": None,
    # v0.10.3: notifications panel toggle (notifications themselves are on disk)
    "notif_panel_open": False,
}
for k, v in _SS.items():
    if k not in st.session_state: st.session_state[k] = v

if "migrations_done" not in st.session_state:
    migrate_creations()
    migrate_wallets()
    st.session_state["migrations_done"] = True


# ══════════════════════════════════════════════════════════════════════
# ⑮ AUTH GATE
# ══════════════════════════════════════════════════════════════════════
if not st.session_state["authenticated"]:
    st.markdown(
        '<div class="g-hero" style="margin-top:40px;padding:48px 40px;">'
        '<div class="g-hero-title">&#11039; DELPHIA GENESIS &#11039;</div>'
        '<div class="g-hero-sub">CREATOR ECONOMY &middot; GENESIS LAYER v0.10.3</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    _, mid, _ = st.columns([1,1.6,1])
    with mid:
        a_login, a_reg = st.tabs(["🔑 LOGIN","🌟 REGISTER"])

        with a_login:
            st.markdown(
                "<div style='font-family:DM Mono;color:#8899aa;font-size:11px;margin-bottom:16px;'>"
                "Enter your Kingdom to access your Sovereign Vault.</div>",
                unsafe_allow_html=True,
            )
            lk = st.text_input("Kingdom Name", key="l_k", placeholder="Astra Nova", label_visibility="collapsed")
            lp = st.text_input("Password", key="l_p", type="password", placeholder="Your sacred password", label_visibility="collapsed")
            st.write("")
            if st.button("✦ ENTER THE IMAGINARIUM", type="primary", use_container_width=True, key="btn_login"):
                if not lk.strip() or not lp.strip():
                    st.warning("Kingdom name and password required.")
                else:
                    ok, msg = verify_user(lk.strip(), lp.strip())
                    if ok:
                        u = lk.strip()
                        st.session_state.update({
                            "authenticated": True, "user": u,
                            "quest_completed": load_quests_done(u),
                            "imagix": load_wallet(u),
                            SPONSOR_SESSION_KEY: False,
                            "sponsor_viewed_qs": False,
                            "split_open": {},
                            "quest_banner": [], "buy_feedback": None,
                            "notif_panel_open": False,
                        })
                        urow = get_user_row(u)
                        if urow and str(urow.get("sponsor_kingdom","")).strip() not in ("","nan"):
                            st.session_state["has_sponsor"] = True
                        ensure_dirs(u); log_activity(u, "LOGIN"); st.rerun()
                    else:
                        st.error("⚠️ {}".format(msg))

        with a_reg:
            st.markdown(
                "<div style='font-family:DM Mono;color:#8899aa;font-size:11px;margin-bottom:16px;'>"
                "Forge your Kingdom on the Genesis Layer.</div>",
                unsafe_allow_html=True,
            )
            rk   = st.text_input("Kingdom Name", key="r_k", placeholder="e.g. Astra Nova", label_visibility="collapsed")
            rp   = st.text_input("Sacred Password", key="r_p", type="password", placeholder="Choose a strong password", label_visibility="collapsed")
            rp2  = st.text_input("Confirm Password", key="r_p2", type="password", placeholder="Repeat your password", label_visibility="collapsed")
            rdob = st.date_input("Date of Birth", key="r_dob", min_value=date(1980,1,1), max_value=date.today(), value=date(2010,1,1))
            st.caption("Used to match you with your Genesis Tutors.")
            with st.expander("👁 Add a Sponsor / Parent (optional)"):
                sp_k = st.text_input("Sponsor Kingdom Name", key="sp_k", placeholder="Parent's Kingdom")
                sp_p = st.text_input("Sponsor Password", key="sp_p", type="password", placeholder="Sponsor's password")
                st.caption("Your sponsor can view your progress and help manage your account.")
            if st.button("🌟 FORGE MY KINGDOM", type="primary", use_container_width=True, key="btn_reg"):
                if not rk.strip():   st.error("Your Kingdom needs a name.")
                elif len(rp) < 4:    st.error("Password must be at least 4 characters.")
                elif rp != rp2:      st.error("Passwords do not match.")
                else:
                    ok, msg = register_user(
                        rk.strip(), rp, rdob.isoformat(),
                        st.session_state.get("sp_k",""),
                        st.session_state.get("sp_p",""),
                    )
                    if ok:
                        u = rk.strip()
                        st.session_state.update({
                            "authenticated": True, "user": u,
                            "quest_completed": set(), "imagix": 0,
                            "has_sponsor": bool(str(st.session_state.get("sp_k","")).strip()),
                            "quest_banner": [], "buy_feedback": None,
                            "notif_panel_open": False,
                        })
                        ensure_dirs(u)
                        st.success("✦ Kingdom forged! Welcome to the Genesis Layer.")
                        st.balloons(); st.rerun()
                    else:
                        st.error(msg)
    st.stop()


# ══════════════════════════════════════════════════════════════════════
# ⑯ MAIN APP — authenticated only beyond this point
# ══════════════════════════════════════════════════════════════════════
user: str = st.session_state["user"]
ensure_dirs(user)

if st.session_state["creations_df"] is None:
    st.session_state["creations_df"] = load_creations()

df_all: pd.DataFrame = st.session_state["creations_df"]
user_df = (
    df_all[df_all["sovereign"] == user].copy()
    if not df_all.empty and "sovereign" in df_all.columns
    else pd.DataFrame(columns=CREATION_COLS)
)

dob           = get_user_dob(user)
age           = calc_age(dob)
is_minor      = age < MINOR_AGE
active_tutors = get_active_tutors(age)

# Process loan defaults on every page load
process_loan_defaults(user)

run_quests(df_all, user)

total_imagix    = st.session_state["imagix"]
total_royalties = load_wallet_royalties(user)
rank            = get_rank(total_imagix)
n_done          = len(st.session_state["quest_completed"])

# Robust royalty_ever detection (carried forward from v0.10.1.2)
def _check_royalty_ever_from_disk(u: str) -> bool:
    if load_wallet_royalties(u) > 0: return True
    try:
        cdf_r = load_creations()
        if cdf_r.empty or "original_creator" not in cdf_r.columns: return False
        user_creates = cdf_r[cdf_r["original_creator"] == u]
        if user_creates.empty: return False
        return bool(
            pd.to_numeric(user_creates["total_royalties"], errors="coerce").fillna(0).gt(0).any()
        )
    except Exception: return False

if not st.session_state.get("royalty_ever"):
    if _check_royalty_ever_from_disk(user):
        st.session_state["royalty_ever"] = True
        run_quests(df_all, user)

# ── HEADER — v0.10.3: disk-backed notification bell ─────────────────
unread_count = count_unread(user)   # reads from disk each render

h1, h2, h3, h4, h5_bell, h6_logout = st.columns([3.5, 1, 1, 1, 0.55, 0.8])

h1.markdown(
    '<div style="padding-top:8px;">'
    '<span style="font-family:Cinzel,serif;font-size:17px;color:#F2C94C;font-weight:700;">🌟 {}</span>'
    '&nbsp;<span style="color:#8899aa;font-size:13px;">·</span>&nbsp;'
    '<span class="rank-pill" style="font-size:11px;padding:4px 14px;">{}</span>'
    '</div>'.format(user, rank["name"]),
    unsafe_allow_html=True,
)
h2.metric("IMAGIX",    "{:,} I".format(total_imagix))
h3.metric("CREATIONS", len(user_df))
h4.metric("QUESTS",    "{}/{}".format(n_done, len(QUESTS)))

with h5_bell:
    st.write("")
    # Bell label shows count only when > 0
    bell_lbl = "🔔 {}".format(unread_count) if unread_count > 0 else "🔔"
    bell_help = "{} unread notification{}".format(
        unread_count, "s" if unread_count != 1 else ""
    ) if unread_count > 0 else "No new notifications"
    if st.button(bell_lbl, key="notif_bell_btn", help=bell_help):
        st.session_state["notif_panel_open"] = not st.session_state.get("notif_panel_open", False)

if h6_logout.button("✦ LOGOUT", key="logout_btn"):
    for k in list(_SS.keys()):
        if k in st.session_state: del st.session_state[k]
    st.rerun()

# ── NOTIFICATION PANEL (shown below header when bell toggled) ────────
if st.session_state.get("notif_panel_open", False):
    render_notification_panel(user)

# ── PROGRESS BAR ─────────────────────────────────────────────────────
pb, _ = st.columns([3,1])
with pb:
    if not rank["maxed"]:
        st.progress(rank["progress"],
                    text="Progress to next rank · {:,} / {:,} IMAGIX".format(total_imagix, rank["next"]))
    else:
        st.progress(1.0, text="👑 LEGEND — Supreme Sovereign of the Genesis Layer")

st.divider()

# ── QUEST BANNER ────────────────────────────────────────────────────
render_quest_banner()

# ── BUY FEEDBACK PANEL ──────────────────────────────────────────────
if st.session_state.get("buy_feedback"):
    bf = st.session_state["buy_feedback"]
    details_html = ""
    for k, v in bf.get("details", []):
        details_html += (
            '<div class="buy-detail-row">'
            '<span class="buy-detail-key">{}</span>'
            '<span class="buy-detail-val">{}</span>'
            '</div>'.format(k, v)
        )
    st.markdown(
        '<div class="buy-success">'
        '<div class="buy-success-title">🎉 {}</div>{}</div>'.format(
            bf.get("title","Purchase Complete!"), details_html),
        unsafe_allow_html=True,
    )
    if st.button("✕ Dismiss", key="dismiss_buy"):
        st.session_state["buy_feedback"] = None
        st.rerun()
    st.divider()


# ══════════════════════════════════════════════════════════════════════
# TUTOR PANEL
# ══════════════════════════════════════════════════════════════════════
def render_tutor_panel(context_tab: str):
    if not active_tutors: return

    st.markdown(
        '<div style="font-family:Cinzel,serif;color:#00E5C0;font-size:9px;'
        'letter-spacing:2px;margin-bottom:8px;">✦ GENESIS TUTORS — Choose your guide</div>',
        unsafe_allow_html=True,
    )

    t_cols = st.columns(len(active_tutors) + 1)

    for i, t in enumerate(active_tutors):
        with t_cols[i]:
            if st.button("{} {}".format(t["emoji"], t["short"]),
                         key="tb_{}_{}".format(t["id"], context_tab)):
                key = "{}_{}".format(t["id"], context_tab)
                st.session_state["tutor_open"] = (
                    None if st.session_state.get("tutor_open") == key else key
                )
                if st.session_state["tutor_open"] == key:
                    with st.spinner("{} thinking…".format(t["emoji"])):
                        msg = get_tutor_message(t, context_tab, user, df_all)
                    st.session_state["tmsg_{}".format(key)] = msg
                    if not st.session_state["tutor_used"]:
                        st.session_state["tutor_used"] = True
                        run_quests(df_all, user)

    with t_cols[-1]:
        st.markdown('<div class="deep-q-btn">', unsafe_allow_html=True)
        if st.button("🔮 DEEP Q", key="deepq_{}".format(context_tab),
                     help="Ask your tutor a deep question"):
            current = st.session_state.get("deep_q_open")
            st.session_state["deep_q_open"] = None if current == context_tab else context_tab
        st.markdown("</div>", unsafe_allow_html=True)

    open_key = st.session_state.get("tutor_open","") or ""
    if open_key.endswith("_{}".format(context_tab)):
        tid = open_key[: -(len(context_tab) + 1)]
        t   = next((x for x in active_tutors if x["id"] == tid), None)
        msg_key = "tmsg_{}".format(open_key)
        if t and msg_key in st.session_state:
            st.markdown(
                '<div class="tutor-chat">'
                '<div class="tutor-name" style="color:{};">{} {}</div>'
                '<div class="tutor-msg">{}</div>'
                '</div>'.format(t["color"], t["emoji"], t["name"], st.session_state[msg_key]),
                unsafe_allow_html=True,
            )

    if st.session_state.get("deep_q_open") == context_tab:
        dq_tutor = active_tutors[0]
        with st.expander("🔮 Deep Question", expanded=True):
            dq = st.text_input(
                "Ask anything deep…", key="dq_input_{}".format(context_tab),
                placeholder="Por que la creatividad tiene valor?",
            )
            dc1, dc2 = st.columns([1,1])
            with dc1:
                if st.button("✦ ASK", key="dq_ask_{}".format(context_tab)) and dq.strip():
                    with st.spinner("{} Thinking deeply…".format(dq_tutor["emoji"])):
                        answer = get_deep_answer(dq_tutor, dq.strip(), user, df_all)
                    st.session_state["dq_ans_{}".format(context_tab)] = answer
                    if not st.session_state["deep_q_used"]:
                        st.session_state["deep_q_used"] = True
                        run_quests(df_all, user)
            with dc2:
                if st.button("✕ Close", key="dq_close_{}".format(context_tab)):
                    st.session_state["deep_q_open"] = None; st.rerun()
            ans_key = "dq_ans_{}".format(context_tab)
            if ans_key in st.session_state:
                st.markdown(
                    '<div class="tutor-chat">'
                    '<div class="tutor-name" style="color:{};">{} {}</div>'
                    '<div class="tutor-msg">{}</div>'
                    '</div>'.format(
                        dq_tutor["color"], dq_tutor["emoji"],
                        dq_tutor["name"], st.session_state[ans_key],
                    ),
                    unsafe_allow_html=True,
                )
    st.divider()


# ══════════════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════════════
tab_vault, tab_wallet, tab_quests, tab_market, tab_upload, tab_activity, tab_loans = st.tabs([
    "🌌 MY VAULT", "💎 WALLET", "⚔️ QUESTS", "🌠 MARKETPLACE",
    "🌱 UPLOAD", "📜 ACTIVITY", "🔒 LOANS",
])


# ────────────────────────────────────────────────────────────────────
# TAB: VAULT
# ────────────────────────────────────────────────────────────────────
with tab_vault:
    render_tutor_panel("vault")

    vc1, vc2 = st.columns([3,1])
    vc1.markdown("### 🌌 SOVEREIGN CREATIONS VAULT")
    with vc2:
        sort_opt = st.selectbox("Sort", ["Newest","Highest Value","Alphabetical"],
                                label_visibility="collapsed")

    if user_df.empty:
        st.info("🌠 Your Vault awaits its first creation. Head to Upload to begin your Genesis journey!")
        st.markdown(
            '<div style="font-family:Cinzel,serif;color:#F2C94C;font-size:13px;'
            'margin:20px 0 12px;letter-spacing:1px;">✦ GENESIS SHOWCASE — Creations from the Multiverse</div>',
            unsafe_allow_html=True,
        )
        dc = st.columns(6)
        for i, (dn, dv, de) in enumerate(DEMO_SHOWCASE):
            with dc[i % 6]:
                st.markdown(
                    '<div class="g-card showcase-glow">'
                    '<div class="g-card-img"><span style="position:relative;z-index:1;">{}</span></div>'
                    '<div class="g-card-body">'
                    '<div class="g-badge-gold">SHOWCASE</div>'
                    '<div class="g-card-title">{}</div>'
                    '<div class="g-card-value">{:,} I</div>'
                    '<div class="g-card-id">DEMO · GENESIS MULTIVERSE</div>'
                    '</div></div>'.format(de, dn, dv),
                    unsafe_allow_html=True,
                )
    else:
        sdf = user_df.copy()
        if sort_opt == "Newest":
            sdf = sdf.sort_values("created_at", ascending=False)
        elif sort_opt == "Highest Value":
            sdf["_v"] = pd.to_numeric(sdf["value"], errors="coerce").fillna(0)
            sdf = sdf.sort_values("_v", ascending=False)
        else:
            sdf = sdf.sort_values("name")

        total_val = pd.to_numeric(sdf["value"], errors="coerce").fillna(0).sum()
        n_frac    = int(sdf["is_fractional"].astype(str).str.lower().isin(["true","1"]).sum())
        n_cert    = int(sdf["cert_downloaded"].astype(str).str.lower().isin(["true","1"]).sum())
        credit    = int(total_val * 0.25 + total_imagix * 1.5)

        pm1, pm2, pm3, pm4 = st.columns(4)
        pm1.metric("PORTFOLIO VALUE",  "{:,.0f} I".format(total_val))
        pm2.metric("FRACTIONALISED",   n_frac)
        pm3.metric("CERTS ISSUED",     n_cert)
        pm4.metric("CREDIT CAPACITY",  "~{:,} I".format(credit))
        st.caption("{} creation(s) on the Genesis Layer".format(len(sdf)))

        records = sdf.to_dict("records")
        CPR = 4

        for rs in range(0, len(records), CPR):
            cols = st.columns(CPR)
            for ci, rec in enumerate(records[rs:rs+CPR]):
                with cols[ci]:
                    aid       = str(rec.get("id") or "")
                    rn        = str(rec.get("name") or "Unknown")
                    rv        = safe_int(rec.get("value"))
                    re_       = str(rec.get("emoji") or "🌟")
                    rfp       = str(rec.get("file_path") or "")
                    is_frac   = str(rec.get("is_fractional","")).lower() in ("true","1")
                    is_locked = str(rec.get("is_locked","")).lower() == "true"
                    n_f       = max(1, safe_int(rec.get("fraction_count"), 100))
                    lp_raw    = str(rec.get("listed_price","")).strip()
                    is_listed = lp_raw not in ("","nan","0","None")
                    orig_cr   = str(rec.get("original_creator","")).strip()
                    r_pct     = safe_int(rec.get("royalty_pct", str(DEFAULT_ROYALTY_PCT)), DEFAULT_ROYALTY_PCT)
                    tot_roy   = safe_int(rec.get("total_royalties","0"))

                    frac_badge   = '<div class="g-badge-teal">FRACTIONAL</div>' if is_frac   else ""
                    mkt_badge    = '<div class="g-badge-purple">LISTED</div>'   if is_listed else ""
                    locked_badge = '<div class="g-badge-locked">LOCKED</div>'   if is_locked else ""

                    b64 = img_to_b64(rfp)

                    if b64:
                        st.markdown(
                            '<div class="g-card">'
                            '<div style="position:relative;height:130px;overflow:hidden;">'
                            '<img src="{}" style="width:100%;height:130px;object-fit:cover;display:block;">'
                            '{}{}{}'
                            '</div>'
                            '<div class="g-card-body">'
                            '<div class="g-card-title">{}</div>'
                            '<div class="g-card-value">{:,} I</div>'
                            '<div class="g-card-id">{}</div>'
                            '</div></div>'.format(b64, frac_badge, mkt_badge, locked_badge, rn, rv, aid),
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            '<div class="g-card">'
                            '<div class="g-card-img">'
                            '<span style="position:relative;z-index:1;">{}</span>'
                            '{}{}{}'
                            '</div>'
                            '<div class="g-card-body">'
                            '<div class="g-card-title">{}</div>'
                            '<div class="g-card-value">{:,} I</div>'
                            '<div class="g-card-id">{}</div>'
                            '</div></div>'.format(re_, frac_badge, mkt_badge, locked_badge, rn, rv, aid),
                            unsafe_allow_html=True,
                        )

                    # Royalty context
                    if orig_cr and orig_cr != user:
                        st.caption("Creator: {} · {}% royalty".format(orig_cr, r_pct))
                    elif orig_cr == user and tot_roy > 0:
                        st.caption("Royalties earned: {:,} I".format(tot_roy))

                    # ── TITLE button — atomic, no flash ──────────
                    cert_key     = "cert_{}".format(aid)
                    cert_gen_key = "cert_generating_{}".format(aid)

                    if cert_key not in st.session_state:
                        cert_slot = st.empty()
                        if not st.session_state.get(cert_gen_key, False):
                            with cert_slot:
                                clicked = st.button("📜 TITLE", key="title_{}".format(aid))
                            if clicked:
                                st.session_state[cert_gen_key] = True
                                with cert_slot:
                                    with st.spinner("Generating certificate…"):
                                        try:
                                            pdf_bytes = make_certificate(rn, aid, user, rv)
                                            st.session_state[cert_key] = pdf_bytes
                                            fresh = load_creations().copy()
                                            fresh.loc[fresh["id"] == aid, "cert_downloaded"] = "True"
                                            save_creations(fresh)
                                            st.session_state["creations_df"] = load_creations()
                                            if not st.session_state["cert_ever"]:
                                                st.session_state["cert_ever"] = True
                                            run_quests(df_all, user)
                                            log_activity(user, "CERT_GEN", aid)
                                        except Exception as e:
                                            st.session_state[cert_gen_key] = False
                                            st.error("Certificate error: {}".format(e))
                                st.session_state[cert_gen_key] = False
                                st.rerun()
                        else:
                            with cert_slot:
                                st.info("Generating certificate…")
                    else:
                        safe_name = rn[:24].replace(" ","_")
                        st.download_button(
                            "⬇️ Certificate",
                            data=st.session_state[cert_key],
                            file_name="{}_Certificate.pdf".format(safe_name),
                            mime="application/pdf",
                            key="dl_{}".format(aid),
                            use_container_width=True,
                        )
                        if st.button("↻ New cert", key="regen_{}".format(aid)):
                            del st.session_state[cert_key]
                            st.rerun()

                    # ── SPLIT ────────────────────────────────────
                    split_lbl = "⅒ FRACS" if is_frac else "🔀 SPLIT"
                    if st.button(split_lbl, key="split_{}".format(aid), disabled=is_locked):
                        st.session_state["split_open"][aid] = (
                            not st.session_state["split_open"].get(aid, False)
                        )
                        if not is_frac:
                            fresh = load_creations().copy()
                            fresh.loc[fresh["id"] == aid, "is_fractional"]  = "True"
                            fresh.loc[fresh["id"] == aid, "fraction_count"] = "100"
                            save_creations(fresh)
                            st.session_state["creations_df"] = load_creations()
                            run_quests(df_all, user)
                            log_activity(user, "SPLIT", aid)
                        st.rerun()

                    if st.session_state["split_open"].get(aid):
                        fv = rv / n_f
                        st.success("**{}** → **{}** shares · **{:,.0f} I** each ✦".format(rn, n_f, fv))

                    # ── LIST / DELIST ────────────────────────────
                    list_lbl = "🌠 DELIST" if is_listed else "🌠 LIST"
                    if st.button(list_lbl, key="list_{}".format(aid), disabled=is_locked):
                        fresh = load_creations().copy()
                        if not is_listed:
                            fresh.loc[fresh["id"] == aid, "listed_price"] = str(rv)
                            fresh.loc[fresh["id"] == aid, "listed_at"]    = datetime.now().isoformat()
                            save_creations(fresh)
                            mdf = load_market().copy()
                            if aid not in mdf["id"].values:
                                mdf = pd.concat([mdf, pd.DataFrame([{
                                    "id": aid, "name": rn, "sovereign": user,
                                    "value": str(rv), "emoji": re_,
                                    "listed_price": str(rv),
                                    "listed_at": datetime.now().isoformat(),
                                    "original_creator": orig_cr or user,
                                    "royalty_pct": str(r_pct),
                                }])], ignore_index=True)
                            save_market(mdf)
                            run_quests(df_all, user)
                            log_activity(user, "LIST", "{}@{}".format(aid, rv))
                            st.success("✦ **{}** listed in the Marketplace!".format(rn))
                        else:
                            fresh.loc[fresh["id"] == aid, "listed_price"] = ""
                            fresh.loc[fresh["id"] == aid, "listed_at"]    = ""
                            save_creations(fresh)
                            mdf = load_market()
                            save_market(mdf[mdf["id"] != aid].copy())
                            log_activity(user, "DELIST", aid)
                            st.info("✦ **{}** delisted.".format(rn))
                        st.session_state["creations_df"] = load_creations()
                        st.rerun()


# ────────────────────────────────────────────────────────────────────
# TAB: WALLET
# ────────────────────────────────────────────────────────────────────
with tab_wallet:
    render_tutor_panel("wallet")
    st.markdown("### 💎 IMAGIX WALLET")

    _, wm, _ = st.columns([1,1.5,1])
    with wm:
        st.markdown(
            '<div class="wallet-card">'
            '<div class="wallet-label">CURRENT BALANCE</div>'
            '<div class="wallet-amount">{:,} I</div>'
            '<div class="wallet-label" style="margin-top:8px;">IMAGIX · GENESIS LAYER v0.10.3</div>'
            '</div>'.format(total_imagix),
            unsafe_allow_html=True,
        )

    if not user_df.empty:
        pv         = pd.to_numeric(user_df["value"], errors="coerce").fillna(0).sum()
        credit_est = int(pv * 0.25 + total_imagix * 1.5)
        pc1, pc2, pc3, pc4 = st.columns(4)
        pc1.metric("VAULT VALUE",    "{:,.0f} I".format(pv))
        pc2.metric("IMAGIX EARNED",  "{:,} I".format(total_imagix))
        pc3.metric("ROYALTIES",      "{:,} I".format(total_royalties))
        pc4.metric("CREDIT CAPACITY","{:,} I".format(credit_est))

    st.divider()
    st.markdown("#### 👑 Creator Royalties")

    wallet_royalties_fresh = load_wallet_royalties(user)
    all_cdf_w = load_creations()

    if not all_cdf_w.empty and "original_creator" in all_cdf_w.columns:
        creator_works = all_cdf_w[all_cdf_w["original_creator"] == user].copy()
    else:
        creator_works = pd.DataFrame()

    if not creator_works.empty:
        creator_works["_roy"] = pd.to_numeric(creator_works["total_royalties"], errors="coerce").fillna(0)
        creator_works_with_roy = creator_works[creator_works["_roy"] > 0]
    else:
        creator_works_with_roy = pd.DataFrame()

    if wallet_royalties_fresh == 0 and creator_works_with_roy.empty:
        st.markdown(
            '<div class="royalty-card">'
            '<div class="royalty-title">&#128081; CREATOR ROYALTIES</div>'
            '<div style="font-family:DM Mono,monospace;color:#8899aa;font-size:11px;line-height:1.8;">'
            'No royalties yet. When a creation you made is resold by another Sovereign,<br>'
            'you automatically earn {}% of the sale price — forever.<br>'
            '<span style="color:#F2C94C;">Upload and list a creation to start earning.</span>'
            '</div></div>'.format(DEFAULT_ROYALTY_PCT),
            unsafe_allow_html=True,
        )
    else:
        rows_html = ""
        if not creator_works_with_roy.empty:
            for _, crow in creator_works_with_roy.iterrows():
                roy_amt  = safe_int(crow.get("total_royalties","0"))
                is_owned = str(crow.get("sovereign","")) == user
                note     = " (yours)" if is_owned else " (resold)"
                rows_html += (
                    '<div class="royalty-row">'
                    '<span class="royalty-key">{}{}</span>'
                    '<span class="royalty-val">+{:,} I</span>'
                    '</div>'.format(str(crow.get("name",""))[:30], note, roy_amt)
                )
        pending = creator_works[
            (creator_works["_roy"] == 0) &
            (pd.to_numeric(creator_works.get("royalty_pct", pd.Series()), errors="coerce").fillna(0) > 0)
        ] if not creator_works.empty else pd.DataFrame()
        pending_html = ""
        if not pending.empty:
            for _, pr in pending.iterrows():
                r_p = safe_int(pr.get("royalty_pct", str(DEFAULT_ROYALTY_PCT)), DEFAULT_ROYALTY_PCT)
                pending_html += (
                    '<div class="royalty-row" style="opacity:.6;">'
                    '<span class="royalty-key">{} ({}% · awaiting first sale)</span>'
                    '<span class="royalty-val">—</span>'
                    '</div>'.format(str(pr.get("name",""))[:30], r_p)
                )

        st.markdown(
            '<div class="royalty-card">'
            '<div class="royalty-title">&#128081; CREATOR ROYALTIES</div>'
            '<div class="royalty-row">'
            '<span class="royalty-key">TOTAL RECEIVED</span>'
            '<span class="royalty-val">{:,} IMAGIX</span>'
            '</div>'
            '{}{}'
            '<div style="font-family:DM Mono,monospace;color:#8899aa;font-size:9px;margin-top:10px;">'
            '&#10003; Automatic · Permanent · {}% default on every secondary sale'
            '</div></div>'.format(wallet_royalties_fresh, rows_html, pending_html, DEFAULT_ROYALTY_PCT),
            unsafe_allow_html=True,
        )

    st.divider()
    st.markdown("#### ✦ Earnings Ledger")

    rows_html = ""
    for cat in ["Onboarding","Creation","Collection","Actions","Daily","Wealth"]:
        cat_qs = [q for q in QUESTS if q.get("cat") == cat]
        if not cat_qs: continue
        rows_html += '<tr><td colspan="3" class="ledger-cat">{}</td></tr>'.format(cat)
        for q in cat_qs:
            done_flag = q["id"] in st.session_state["quest_completed"]
            s_col  = "#00E5C0" if done_flag else "#8899aa"
            r_col  = "#F2C94C" if done_flag else "#8899aa"
            status = "DONE" if done_flag else "PENDING"
            rows_html += (
                '<tr>'
                '<td style="color:#ccd6f0;">{} {}</td>'
                '<td style="color:{};">{}</td>'
                '<td style="color:{};text-align:right;font-family:Cinzel,serif;font-weight:700;">+{:,} I</td>'
                '</tr>'
            ).format(q["icon"], q["title"], s_col, status, r_col, q["reward"])

    st.markdown(
        '<table class="ledger-table">'
        '<thead><tr><th>QUEST</th><th>STATUS</th><th style="text-align:right;">REWARD</th></tr></thead>'
        '<tbody>{}</tbody>'
        '</table>'.format(rows_html),
        unsafe_allow_html=True,
    )
    st.write("")
    total_pot = sum(q["reward"] for q in QUESTS)
    earned    = sum(q["reward"] for q in QUESTS if q["id"] in st.session_state["quest_completed"])
    wc1, wc2, wc3 = st.columns(3)
    wc1.metric("EARNED",          "{:,} I".format(earned))
    wc2.metric("TOTAL POTENTIAL", "{:,} I".format(total_pot))
    wc3.metric("REMAINING",       "{:,} I".format(total_pot - earned))


# ────────────────────────────────────────────────────────────────────
# TAB: QUESTS
# ────────────────────────────────────────────────────────────────────
with tab_quests:
    render_tutor_panel("quests")
    st.markdown("### ⚔️ QUESTS & PROGRESS")

    qc1, qc2 = st.columns([2,1])
    with qc1:
        st.markdown(
            '<div style="margin-bottom:18px;">'
            '<div style="font-family:DM Mono,monospace;color:#00E5C0;font-size:9px;'
            'letter-spacing:3px;margin-bottom:8px;">CURRENT RANK</div>'
            '<div class="rank-pill">{}</div>'
            '</div>'.format(rank["name"]),
            unsafe_allow_html=True,
        )
        if not rank["maxed"]:
            st.progress(rank["progress"],
                        text="{:,} IMAGIX needed to advance".format(rank["next"] - total_imagix))
        else:
            st.progress(1.0, text="👑 Maximum rank — you are LEGEND")
    with qc2:
        st.markdown(
            '<div style="background:#0d1f3a;border:1px solid rgba(157,78,221,.4);'
            'border-radius:12px;padding:16px 20px;text-align:center;">'
            '<div style="font-family:DM Mono,monospace;color:#00E5C0;font-size:9px;'
            'letter-spacing:2px;margin-bottom:10px;">RANK TIERS</div>'
            '<div style="font-family:Cinzel,serif;color:#8899aa;font-size:9px;line-height:2.1;">'
            '✦ SPARK I-III · 0-25k<br>🔥 FLAME I-III · 50k-175k<br>'
            '⭐ STAR I-III · 275k-600k<br>👑 LEGEND · 900k+'
            '</div></div>',
            unsafe_allow_html=True,
        )

    st.divider()
    done_ids = st.session_state["quest_completed"]
    for cat in ["Onboarding","Creation","Collection","Actions","Daily","Wealth"]:
        cat_qs = [q for q in QUESTS if q.get("cat") == cat]
        if not cat_qs: continue
        st.markdown(
            '<div style="font-family:Cinzel,serif;color:#9D4EDD;font-size:10px;'
            'letter-spacing:2px;margin:16px 0 8px;text-transform:uppercase;">&#9672; {}</div>'.format(cat),
            unsafe_allow_html=True,
        )
        for q in cat_qs:
            done = q["id"] in done_ids
            st.markdown(
                '<div class="q-card {}">'
                '<div class="q-icon">{}</div>'
                '<div class="q-info">'
                '<div class="q-title">{}{}</div>'
                '<div class="q-desc">{}</div>'
                '</div>'
                '<div class="q-reward">+{:,} I</div>'
                '</div>'.format(
                    "done" if done else "", q["icon"],
                    "✅ " if done else "○ ", q["title"],
                    q["desc"], q["reward"],
                ),
                unsafe_allow_html=True,
            )

    st.divider()
    rem = sum(q["reward"] for q in QUESTS if q["id"] not in done_ids)
    st.markdown(
        "**Completed:** `{}/{}` · **Earned:** `{:,} I` · **Remaining:** `{:,} I`".format(
            len(done_ids), len(QUESTS), total_imagix, rem
        )
    )


# ────────────────────────────────────────────────────────────────────
# TAB: MARKETPLACE
# ────────────────────────────────────────────────────────────────────
with tab_market:
    render_tutor_panel("market")
    st.markdown("### 🌠 GENESIS MARKETPLACE")

    mdf = load_market()

    if mdf.empty or "id" not in mdf.columns or len(mdf) == 0:
        st.markdown(
            '<div style="background:linear-gradient(135deg,#0d1f3a,#112B4D);'
            'border:1px solid rgba(242,201,76,.35);border-radius:16px;'
            'padding:40px 32px;text-align:center;overflow:hidden;">'
            '<div style="font-size:50px;margin-bottom:14px;">🌠</div>'
            '<div style="font-family:Cinzel,serif;color:#F2C94C;font-size:18px;font-weight:700;letter-spacing:2px;">GENESIS MARKETPLACE</div>'
            '<div style="font-family:DM Mono,monospace;color:#00E5C0;font-size:11px;margin-top:10px;">No creations listed yet — be the first Sovereign to open trade!</div>'
            '<div style="font-family:DM Mono,monospace;color:#8899aa;font-size:10px;margin-top:18px;line-height:2;">'
            '✦ Go to MY VAULT and click 🌠 LIST<br>'
            '✦ Royalties paid to original creator automatically<br>'
            '✦ Auctions coming in the next update'
            '</div></div>',
            unsafe_allow_html=True,
        )
    else:
        mc1, mc2, mc3 = st.columns([2,1,1])
        mc1.markdown("**{} listing(s)** on the Genesis Layer".format(len(mdf)))
        with mc2:
            mkt_sort = st.selectbox("Sort",["Recent","Highest Price","Lowest Price"],
                                    label_visibility="collapsed")
        with mc3:
            show_own = st.checkbox("Show my listings", value=True)

        mdf2 = mdf.copy()
        if mkt_sort == "Highest Price":
            mdf2["_lp"] = pd.to_numeric(mdf2["listed_price"], errors="coerce").fillna(0)
            mdf2 = mdf2.sort_values("_lp", ascending=False)
        elif mkt_sort == "Lowest Price":
            mdf2["_lp"] = pd.to_numeric(mdf2["listed_price"], errors="coerce").fillna(0)
            mdf2 = mdf2.sort_values("_lp", ascending=True)
        else:
            mdf2 = mdf2.sort_values("listed_at", ascending=False)

        if not show_own: mdf2 = mdf2[mdf2["sovereign"] != user]
        if mdf2.empty:   st.info("No listings match your filter.")

        for _, mrow in mdf2.iterrows():
            mid      = str(mrow.get("id",""))
            mn       = str(mrow.get("name",""))
            ms       = str(mrow.get("sovereign",""))
            me       = str(mrow.get("emoji","🌟"))
            mp       = safe_int(mrow.get("listed_price"))
            orig_cr  = str(mrow.get("original_creator","")).strip()
            r_pct    = safe_int(mrow.get("royalty_pct", str(DEFAULT_ROYALTY_PCT)), DEFAULT_ROYALTY_PCT)
            is_own   = (ms == user)
            can_buy  = (not is_own and total_imagix >= mp and mp > 0)
            need_more = max(0, mp - total_imagix)

            is_secondary = (orig_cr and orig_cr != ms)
            royalty_amt  = int(mp * r_pct / 100) if is_secondary and r_pct > 0 else 0
            seller_gets  = mp - royalty_amt

            owner_tag = (
                ' · <span style="color:#00E5C0;">YOUR LISTING</span>' if is_own else ""
            )
            if is_secondary and royalty_amt > 0:
                royalty_note = (
                    '<div class="mkt-royalty-note">'
                    '&#128081; {:,} I to creator ({}) &nbsp;·&nbsp; seller receives {:,} I'
                    '</div>'.format(royalty_amt, orig_cr, seller_gets)
                )
            else:
                royalty_note = (
                    '<div class="mkt-royalty-note" style="color:#8899aa;">'
                    '&#127807; Primary sale &nbsp;·&nbsp; full price to seller</div>'
                )

            st.markdown(
                '<div class="mkt-row">'
                '<div class="mkt-emoji">{}</div>'
                '<div style="flex:1;">'
                '<div class="mkt-name">{}</div>'
                '<div class="mkt-seller">by {}{}</div>'
                '{}'
                '</div>'
                '<div class="mkt-price">{:,} I</div>'
                '</div>'.format(me, mn, ms, owner_tag, royalty_note, mp),
                unsafe_allow_html=True,
            )

            if not is_own:
                bc1, bc2 = st.columns([2,1])
                with bc1:
                    if st.button("💰 BUY  {:,} I".format(mp), key="buy_{}".format(mid), disabled=not can_buy):
                        result = execute_sale(mid, user, ms, mp, "MARKETPLACE")
                        if result["success"]:
                            st.session_state["imagix"] = load_wallet(user)
                            st.session_state["creations_df"] = load_creations()
                            st.session_state["bought_ever"] = True
                            if result["royalty_amount"] > 0 and result["royalty_to"] == user:
                                st.session_state["royalty_ever"] = True
                            if load_wallet_royalties(user) > 0:
                                st.session_state["royalty_ever"] = True
                            run_quests(load_creations(), user)

                            details = [
                                ("Creation",    mn),
                                ("Seller",      ms),
                                ("Price Paid",  "{:,} I".format(mp)),
                                ("New Balance", "{:,} I".format(st.session_state["imagix"])),
                            ]
                            if result["royalty_amount"] > 0:
                                details.append(("Royalty to {}".format(result["royalty_to"]),
                                                "{:,} I".format(result["royalty_amount"])))
                            details.append(("Status", "OWNERSHIP TRANSFERRED"))

                            st.session_state["buy_feedback"] = {
                                "title": "You acquired '{}'! 🎉".format(mn),
                                "details": details,
                            }
                            st.rerun()
                        else:
                            st.error("Purchase failed: {}".format(result["message"]))
                with bc2:
                    if not can_buy and mp > 0:
                        st.caption("Need {:,} more I".format(need_more))


# ────────────────────────────────────────────────────────────────────
# TAB: UPLOAD
# ────────────────────────────────────────────────────────────────────
with tab_upload:
    render_tutor_panel("upload")
    st.markdown("### 🌱 REGISTER YOUR CREATION")
    st.caption("Inscribe your art, story, or craft onto the Genesis Layer — permanently and immutably.")

    with st.form("genesis_upload", clear_on_submit=True):
        cn = st.text_input("Creation Name ✦", placeholder="e.g. The Adventures of Luna the Fox")
        uc1, uc2, uc3 = st.columns([2,2,1])
        with uc1: ep = st.selectbox("Creation Emblem", EMOJI_PICKS)
        with uc2: iv = st.number_input("Imagined Value (IMAGIX)",
                                        min_value=100, max_value=10_000_000, value=10_000, step=500)
        with uc3: r_pct_input = st.number_input("Royalty %", min_value=0, max_value=25,
                                                  value=DEFAULT_ROYALTY_PCT, step=1,
                                                  help="% royalty you earn on every secondary sale.")
        uf   = st.file_uploader("Upload your creation (image or PDF — optional)",
                                 type=["jpg","jpeg","png","pdf"],
                                 help="Images appear as card thumbnails in your Vault.")
        lore = st.text_area("Creation Lore (optional)",
                             placeholder="Describe the legend behind your creation…",
                             max_chars=280, height=80)
        ok_sub = st.form_submit_button("🌟 INSCRIBE ON THE GENESIS LAYER",
                                        type="primary", use_container_width=True)

    if ok_sub:
        if not cn.strip():
            st.error("Every great creation must bear a name, Young Sovereign.")
        else:
            with st.spinner("Inscribing your creation on the Genesis Layer…"):
                try:
                    aid = generate_id(cn, user)
                    fp  = ""
                    if uf is not None:
                        sfn  = uf.name.encode("ascii","ignore").decode("ascii").replace(" ","_")
                        dest = "{}/{}/{}_{}" .format(F["dir"], user, aid, sfn)
                        with open(dest,"wb") as fh: fh.write(uf.getbuffer())
                        fp = dest
                    new_rec = {
                        "id": aid, "name": cn.strip(), "sovereign": user,
                        "value": str(int(iv)), "emoji": ep, "file_path": fp,
                        "created_at": datetime.now().isoformat(),
                        "is_fractional": "False", "cert_downloaded": "False",
                        "fraction_count": "100", "listed_price": "", "listed_at": "",
                        "lore": lore.strip()[:280],
                        "original_creator": user,
                        "royalty_pct": str(int(r_pct_input)),
                        "total_royalties": "0",
                        "is_locked": "False",
                        "lock_reason": "",
                        "transfer_count": "0",
                    }
                    fresh = pd.concat([load_creations(), pd.DataFrame([new_rec])], ignore_index=True)
                    save_creations(fresh)
                    st.session_state["creations_df"] = fresh
                    if lore.strip(): st.session_state["lore_added"] = True
                    run_quests(fresh, user)
                    log_activity(user, "UPLOAD", "'{}'".format(cn.strip()))
                    st.balloons()
                    st.success(
                        "✦ **{}** inscribed! Genesis ID: `{}` · **{:,} IMAGIX** · **{}% royalty**".format(
                            cn.strip(), aid, int(iv), int(r_pct_input)
                        )
                    )
                    if lore.strip():
                        st.info("📜 Lore sealed: \"{}\"".format(lore.strip()[:100]))
                    st.rerun()
                except Exception as e:
                    st.error("Inscription failed: {} — Contact the Keeper of the Genesis Layer.".format(e))


# ────────────────────────────────────────────────────────────────────
# TAB: ACTIVITY
# ────────────────────────────────────────────────────────────────────
with tab_activity:
    render_tutor_panel("activity")
    st.markdown("### 📜 ACTIVITY LOG")
    st.caption("A record of every sovereign action on the Genesis Layer.")

    events = load_activity(user, n=30)

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

            meta                      = ACT_META.get(action, ("◈","muted",action))
            act_emoji, act_color, act_label = meta
            color_val                 = C.get(act_color, C["muted"])

            st.markdown(
                '<div class="act-item">'
                '<div class="act-icon">{}</div>'
                '<div class="act-info">'
                '<div class="act-action" style="color:{};">{}</div>'
                '<div class="act-detail">{}</div>'
                '</div>'
                '<div class="act-time">{}</div>'
                '</div>'.format(act_emoji, color_val, act_label, detail or "—", ts_fmt),
                unsafe_allow_html=True,
            )

        st.write("")
        st.caption("Showing last {} events · Sorted newest first".format(len(events)))

        with st.expander("⚙️ Log Options"):
            if st.button("🗑️ Clear my activity log", key="clear_log"):
                df_act = _read(F["activity"], ACTIVITY_COLS)
                df_act = df_act[df_act["sovereign"] != user].copy()
                _write(df_act.tail(500), F["activity"])
                st.success("Activity log cleared.")
                st.rerun()


# ────────────────────────────────────────────────────────────────────
# TAB: LOANS — v0.10.3 POLISHED
# ────────────────────────────────────────────────────────────────────
with tab_loans:
    render_tutor_panel("loans")
    st.markdown("### 🔒 COLLATERALIZED LOANS")
    st.caption(
        "Lock a creation as collateral and receive **{:d}% of its value** in IMAGIX immediately. "
        "Repay within **{} days** or the asset transfers to Genesis Treasury.".format(
            LOAN_LTV_PCT, LOAN_TERM_DAYS
        )
    )

    # ── Sponsor gate notice ───────────────────────────────────────
    if is_minor and not st.session_state.get(SPONSOR_SESSION_KEY, False):
        st.warning(
            "🛡️ **Sponsor approval required for loans.** "
            "Enable Sponsor Mode in the sidebar and verify the sponsor password first. "
            "This protects your creations from accidental collateralization."
        )

    # ── Active loans ──────────────────────────────────────────────
    st.markdown("#### 🏦 Your Active Loans")

    all_loans = load_loans()
    my_loans  = all_loans[all_loans["sovereign"] == user].copy() if not all_loans.empty else pd.DataFrame(columns=LOAN_COLS)
    open_loans = my_loans[my_loans["status"] == "OPEN"] if not my_loans.empty else pd.DataFrame()

    if open_loans.empty:
        st.info("No active loans. Use the form below to open one.")
    else:
        for _, loan in open_loans.iterrows():
            loan_id     = str(loan["loan_id"])
            asset_name  = str(loan["asset_name"])
            loan_amount = safe_int(loan["loan_amount"])
            due_date    = str(loan["due_date"])
            opened_at   = str(loan["opened_at"])

            days_left, urgency, pct_remaining, urgency_label = get_loan_urgency(due_date)

            urgency_color = {
                "ok":     C["green"],
                "warn":   C["orange"],
                "danger": C["danger"],
            }.get(urgency, C["danger"])

            bar_class = "loan-countdown-bar-{}".format(urgency)
            bar_width = max(0, min(100, int(pct_remaining * 100)))

            can_repay  = total_imagix >= loan_amount
            repay_note = "" if can_repay else " (need {:,} more I)".format(loan_amount - total_imagix)

            st.markdown(
                '<div class="loan-card">'
                '<div class="loan-card-title">🏦 {}</div>'
                '<div class="loan-row">'
                '<span class="loan-key">Collateral Asset</span>'
                '<span class="loan-val">{}</span>'
                '</div>'
                '<div class="loan-row">'
                '<span class="loan-key">Loan Amount</span>'
                '<span class="loan-val">{:,} IMAGIX</span>'
                '</div>'
                '<div class="loan-row">'
                '<span class="loan-key">Opened</span>'
                '<span class="loan-val">{}</span>'
                '</div>'
                '<div class="loan-row">'
                '<span class="loan-key">Due Date</span>'
                '<span class="loan-val">{}</span>'
                '</div>'
                '<div class="loan-row">'
                '<span class="loan-key">Time Remaining</span>'
                '<span class="loan-val loan-{}" style="color:{};">{}</span>'
                '</div>'
                '<div class="loan-countdown-wrap">'
                '<div class="{}" style="width:{}%;"></div>'
                '</div>'
                '</div>'.format(
                    loan_id, asset_name, loan_amount, opened_at, due_date,
                    urgency, urgency_color, urgency_label,
                    bar_class, bar_width,
                ),
                unsafe_allow_html=True,
            )

            rc1, rc2, rc3 = st.columns([2, 1, 1])
            with rc1:
                if st.button(
                    "✅ REPAY {:,} I{}".format(loan_amount, repay_note),
                    key="repay_{}".format(loan_id),
                    disabled=not can_repay,
                ):
                    with st.spinner("Processing repayment…"):
                        res = repay_loan(loan_id, user)
                    if res["success"]:
                        st.success("✦ Loan repaid! **{}** is back in your Vault.".format(asset_name))
                        st.balloons()
                        st.session_state["creations_df"] = load_creations()
                        st.rerun()
                    else:
                        st.error("Repayment failed: {}".format(res["message"]))
            with rc2:
                st.caption("Your balance: {:,} I".format(total_imagix))
            with rc3:
                if urgency == "danger" and days_left < 0:
                    st.markdown(
                        '<div style="font-family:DM Mono,monospace;color:#FF6B6B;font-size:9px;padding-top:8px;">'
                        '⚠️ Overdue — asset at risk</div>',
                        unsafe_allow_html=True,
                    )

    # ── Loan history ──────────────────────────────────────────────
    closed_loans = my_loans[my_loans["status"].isin(["REPAID","DEFAULTED"])] if not my_loans.empty else pd.DataFrame()
    if not closed_loans.empty:
        with st.expander("📋 Loan History ({} records)".format(len(closed_loans))):
            for _, loan in closed_loans.sort_values("opened_at", ascending=False).iterrows():
                status   = str(loan["status"])
                s_col    = "#2ECC71" if status == "REPAID" else "#FF6B6B"
                s_icon   = "✅" if status == "REPAID" else "⚠️"
                lamt     = safe_int(loan["loan_amount"])
                st.markdown(
                    '<div style="display:flex;justify-content:space-between;'
                    'align-items:center;padding:8px 4px;'
                    'border-bottom:1px solid rgba(157,78,221,.1);">'
                    '<div>'
                    '<div style="font-family:Cinzel,serif;color:#dde8ff;font-size:10px;">'
                    '{} {}</div>'
                    '<div style="font-family:DM Mono,monospace;color:#8899aa;font-size:9px;">'
                    '{} · {:,} I · due {}</div>'
                    '</div>'
                    '<span style="font-family:Cinzel,serif;font-size:10px;'
                    'color:{};font-weight:700;">{} {}</span>'
                    '</div>'.format(
                        s_icon, str(loan["asset_name"])[:28],
                        str(loan["loan_id"]), lamt, str(loan["due_date"]),
                        s_col, status,
                    ),
                    unsafe_allow_html=True,
                )

    # ── Open new loan ─────────────────────────────────────────────
    st.divider()
    st.markdown("#### 🔒 Open a New Loan")

    eligible_assets = user_df[user_df["is_locked"].astype(str).str.lower() != "true"].copy() if not user_df.empty else pd.DataFrame()

    # Filter out assets already in active loan
    if not eligible_assets.empty and not open_loans.empty:
        loaned_ids = set(open_loans["asset_id"].tolist())
        eligible_assets = eligible_assets[~eligible_assets["id"].isin(loaned_ids)]

    if eligible_assets.empty:
        st.info("No eligible assets available. Upload a creation or unlock an existing one first.")
    else:
        eligible_assets = eligible_assets.copy()
        eligible_assets["_v"] = pd.to_numeric(eligible_assets["value"], errors="coerce").fillna(0)
        eligible_assets = eligible_assets.sort_values("_v", ascending=False)

        asset_options = [
            "{} · {:,} I value → {:,} I loan ({:d}% LTV)".format(
                str(r["name"])[:28],
                safe_int(r["value"]),
                int(safe_int(r["value"]) * LOAN_LTV_PCT / 100),
                LOAN_LTV_PCT,
            )
            for _, r in eligible_assets.iterrows()
        ]

        selected_idx   = st.selectbox(
            "Select Creation to Collateralize",
            range(len(asset_options)),
            format_func=lambda i: asset_options[i],
        )
        selected_row   = eligible_assets.iloc[selected_idx]
        selected_id    = str(selected_row["id"])
        selected_name  = str(selected_row["name"])
        selected_value = safe_int(selected_row["value"])
        loan_preview   = int(selected_value * LOAN_LTV_PCT / 100)

        # Preview card
        st.markdown(
            '<div class="loan-card">'
            '<div class="loan-card-title">🔍 Loan Preview</div>'
            '<div class="loan-row">'
            '<span class="loan-key">Asset</span>'
            '<span class="loan-val">{}</span>'
            '</div>'
            '<div class="loan-row">'
            '<span class="loan-key">Asset Value</span>'
            '<span class="loan-val">{:,} IMAGIX</span>'
            '</div>'
            '<div class="loan-row">'
            '<span class="loan-key">You Receive (LTV {:d}%)</span>'
            '<span class="loan-ok loan-val">{:,} IMAGIX immediately</span>'
            '</div>'
            '<div class="loan-row">'
            '<span class="loan-key">Repay Amount</span>'
            '<span class="loan-val">{:,} IMAGIX (same — no interest!)</span>'
            '</div>'
            '<div class="loan-row">'
            '<span class="loan-key">Term</span>'
            '<span class="loan-val">{} days · due {}</span>'
            '</div>'
            '<div class="loan-row">'
            '<span class="loan-key">If you don\'t repay</span>'
            '<span class="loan-danger loan-val">Asset goes to Genesis Treasury</span>'
            '</div>'
            '</div>'.format(
                selected_name, selected_value,
                LOAN_LTV_PCT, loan_preview,
                loan_preview,
                LOAN_TERM_DAYS,
                (date.today() + timedelta(days=LOAN_TERM_DAYS)).isoformat(),
            ),
            unsafe_allow_html=True,
        )

        # Sponsor status inline
        if is_minor:
            if st.session_state.get(SPONSOR_SESSION_KEY, False):
                st.success("🛡️ Sponsor verified — loan authorized.")
            else:
                st.error("🛡️ Verify your Sponsor in the sidebar to enable loans.")

        open_disabled = is_minor and not st.session_state.get(SPONSOR_SESSION_KEY, False)

        if st.button(
            "🔒 OPEN LOAN — Receive {:,} I NOW".format(loan_preview),
            key="open_loan_btn",
            disabled=open_disabled,
            type="primary" if not open_disabled else "secondary",
        ):
            with st.spinner("Opening loan and locking collateral…"):
                res = open_loan(user, selected_id, selected_name, selected_value, is_minor)
            if res["success"]:
                st.balloons()
                st.success(
                    "✦ Loan **{}** opened! **{:,} I** added to your Wallet. "
                    "Repay by **{}** to get your creation back.".format(
                        res["loan_id"], res["loan_amount"], res["due_date"]
                    )
                )
                st.session_state["creations_df"] = load_creations()
                st.rerun()
            else:
                st.error("Could not open loan: {}".format(res["message"]))

    # ── Auctions scaffold ─────────────────────────────────────────
    st.divider()
    st.markdown("#### 🏛 Auctions — Coming Next Iteration")
    st.markdown(
        '<div style="background:linear-gradient(135deg,rgba(157,78,221,.06),rgba(0,229,192,.04));'
        'border:1px solid rgba(157,78,221,.3);border-radius:14px;padding:20px 24px;">'
        '<div style="font-family:Cinzel,serif;color:#9D4EDD;font-size:13px;font-weight:700;margin-bottom:10px;">'
        '🏛 GENESIS AUCTIONS · v1.0</div>'
        '<div style="font-family:DM Mono,monospace;color:#8899aa;font-size:11px;line-height:2;">'
        '✦ Timed English-style auctions for rare creations<br>'
        '✦ Starting price · reserve price · bid increments<br>'
        '✦ Royalties paid automatically on every auction sale<br>'
        '✦ Sponsor approval for minors (large transactions)<br>'
        '✦ Auto-settlement with countdown timers<br>'
        '<span style="color:#F2C94C;">Data layer scaffolded · UI launching next sprint.</span>'
        '</div></div>',
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════════
# SIDEBAR — GENESIS TERMINAL v0.10.3
# ══════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(
        '<div style="text-align:center;padding:16px 0 8px;">'
        '<div style="font-family:Cinzel,serif;color:#F2C94C;font-size:14px;'
        'font-weight:900;letter-spacing:3px;">◈ GENESIS TERMINAL</div>'
        '<div style="font-family:DM Mono,monospace;color:#00E5C0;font-size:8px;'
        'letter-spacing:2px;margin-top:4px;opacity:.8;">v0.10.3 · CREATOR ECONOMY POLISH</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.divider()

    sidebar_open_loans = 0
    if not all_loans.empty:
        sidebar_open_loans = int(
            ((all_loans["sovereign"] == user) & (all_loans["status"] == "OPEN")).sum()
        )

    total_val_s = pd.to_numeric(user_df["value"], errors="coerce").fillna(0).sum() if not user_df.empty else 0

    for lbl, val in [
        ("YOUNG SOVEREIGN",  user),
        ("AGE",              "{} yrs".format(age) if dob else "Unknown"),
        ("RANK",             rank["name"]),
        ("IMAGIX BALANCE",   "{:,} I".format(total_imagix)),
        ("ROYALTIES EARNED", "{:,} I".format(total_royalties)),
        ("VAULT VALUE",      "{:,.0f} I".format(total_val_s)),
        ("CREATIONS",        str(len(user_df))),
        ("ACTIVE LOANS",     str(sidebar_open_loans)),
        ("NOTIFICATIONS",    "{} unread".format(unread_count) if unread_count > 0 else "None"),
        ("QUESTS DONE",      "{} / {}".format(n_done, len(QUESTS))),
        ("TUTORS",           "{} available".format(len(active_tutors))),
        ("SESSION",          datetime.now().strftime("%H:%M · %b %d")),
    ]:
        st.markdown(
            '<div class="term-block">'
            '<div class="term-key">{}</div>'
            '<div class="term-val">{}</div>'
            '</div>'.format(lbl, val),
            unsafe_allow_html=True,
        )

    st.divider()
    if not rank["maxed"]:
        st.progress(rank["progress"])
        st.caption("{:,} I to next rank".format(rank["next"] - total_imagix))
    else:
        st.progress(1.0); st.caption("👑 LEGEND — Maximum rank achieved")

    st.divider()

    # ── SPONSOR MODE ──────────────────────────────────────────────
    st.markdown(
        '<div style="font-family:Cinzel,serif;color:#8899aa;font-size:9px;'
        'letter-spacing:2px;margin-bottom:6px;">PARENTAL / SPONSOR MODE</div>',
        unsafe_allow_html=True,
    )

    parent_on = st.toggle("Enable Sponsor View", value=st.session_state["parent_mode"],
                           key="parent_toggle", help="A sponsor/parent can view progress here.")
    st.session_state["parent_mode"] = parent_on

    if parent_on:
        if not st.session_state.get("sponsor_viewed_qs"):
            st.session_state["sponsor_viewed_qs"] = True
            run_quests(df_all, user)

        urow        = get_user_row(user)
        has_sponsor = (urow is not None and
                       str(urow.get("sponsor_kingdom","")).strip() not in ("","nan"))

        if not st.session_state.get(SPONSOR_SESSION_KEY, False):
            if has_sponsor:
                sp_pw_h  = str(urow.get("sponsor_pw_hash",""))
                sp_input = st.text_input("Sponsor Password", type="password",
                                          key="sp_pw_input", label_visibility="collapsed",
                                          placeholder="Sponsor password")
                if st.button("🔓 VERIFY SPONSOR", key="verify_sp", use_container_width=True):
                    if hash_pw(sp_input) == sp_pw_h:
                        st.session_state[SPONSOR_SESSION_KEY] = True
                        st.success("✦ Sponsor verified: {}".format(urow["sponsor_kingdom"]))
                        st.rerun()
                    else:
                        st.error("Wrong sponsor password.")
            else:
                st.session_state[SPONSOR_SESSION_KEY] = True

        if st.session_state.get(SPONSOR_SESSION_KEY, False):
            n_cert_s = int(user_df["cert_downloaded"].astype(str).str.lower().isin(["true","1"]).sum()) if not user_df.empty else 0
            n_frac_s = int(user_df["is_fractional"].astype(str).str.lower().isin(["true","1"]).sum()) if not user_df.empty else 0
            n_listed = int((user_df["listed_price"].astype(str).str.strip().isin(["","nan"]) == False).sum()) if not user_df.empty else 0

            for lbl, val in [
                ("Kingdom",      user),
                ("Age",          "{} yrs".format(age)),
                ("Rank",         rank["name"]),
                ("Creations",    str(len(user_df))),
                ("Portfolio",    "{:,.0f} I".format(total_val_s)),
                ("Royalties",    "{:,} I".format(total_royalties)),
                ("Active Loans", str(sidebar_open_loans)),
                ("Certs Issued", str(n_cert_s)),
                ("Fractional",   str(n_frac_s)),
                ("Listed",       str(n_listed)),
                ("IMAGIX",       "{:,} I".format(total_imagix)),
                ("Quests Done",  "{}/{}".format(n_done, len(QUESTS))),
            ]:
                st.markdown(
                    '<div class="sp-row">'
                    '<span class="sp-key">{}</span>'
                    '<span class="sp-val">{}</span>'
                    '</div>'.format(lbl, val),
                    unsafe_allow_html=True,
                )
            st.write("")
            st.markdown(
                '<div style="font-family:DM Mono,monospace;color:#00E5C0;font-size:9px;'
                'margin-top:8px;line-height:1.8;opacity:.8;">'
                '✦ Read-only Sponsor view<br>'
                '✦ Loan approval gate active<br>'
                '✦ Notification bell visible<br>'
                '✦ Auction oversight · v1.0</div>',
                unsafe_allow_html=True,
            )

            if not is_minor:
                st.write("")
                with st.expander("🔑 Reset Kingdom Password"):
                    new_pw  = st.text_input("New Password",  type="password", key="reset_pw1")
                    new_pw2 = st.text_input("Confirm",       type="password", key="reset_pw2")
                    if st.button("🔄 RESET", key="btn_reset_pw"):
                        if len(new_pw) < 4:     st.error("Password too short.")
                        elif new_pw != new_pw2: st.error("Passwords don't match.")
                        else:
                            df_u = load_users()
                            df_u.loc[df_u.kingdom == user, "pw_hash"] = hash_pw(new_pw)
                            save_users(df_u)
                            log_activity(user, "PWD_RESET", "by sponsor")
                            st.success("✦ Password reset by Sponsor.")
            else:
                st.markdown(
                    '<div style="font-family:DM Mono,monospace;color:#F39C12;font-size:9px;'
                    'margin-top:10px;padding:8px 10px;background:rgba(243,156,18,.08);'
                    'border:1px solid rgba(243,156,18,.3);border-radius:8px;">'
                    '🛡️ Account management is handled by your Sponsor. Parental controls active.'
                    '</div>',
                    unsafe_allow_html=True,
                )

    st.divider()
    st.caption("Delphia Genesis v0.10.3\nCreator Economy Polish & Notifications\n© Rey Delphi · Kardashev VI")


# ══════════════════════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════════════════════
st.divider()
st.caption(
    "⬟ Delphia Genesis v0.10.3 — Creator Economy Polish & Notifications  ·  "
    "The Sovereign Awakening  ·  Genesis Layer  ·  Kardashev Type VI ⬟"
)