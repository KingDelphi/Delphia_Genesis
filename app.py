import streamlit as st
import pandas as pd
import os
import hashlib
import tempfile
from fpdf import FPDF

# =============================================
# 1. CONFIGURACIÓN INICIAL Y TEMA GENESIS
# =============================================
def apply_genesis_theme():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700;900&family=Playfair+Display:wght@400;700&family=Space+Grotesk:wght@400;500;600&display=swap');
        
        html, body, [data-testid="stAppViewContainer"] {
            background-color: #0A2540;
            color: #F2C94C;
        }
        .stApp {
            background-color: #0A2540;
        }

        /* Genesis Visual Identity */
        :root {
            --genesis-gold: #F2C94C;
            --celestial-blue: #0A2540;
            --stellar-purple: #9D4EDD;
            --nebula-teal: #00E5C0;
        }

        .card-shell {
            background-color: #112B4D;
            border: 1px solid #00E5C0;
            border-radius: 12px;
            overflow: hidden;
            height: 310px;
            display: flex;
            flex-direction: column;
            transition: all 0.3s ease;
            position: relative;
        }
        .card-shell:hover {
            border-color: #F2C94C;
            box-shadow: 0 0 25px rgba(242, 201, 76, 0.3);
            transform: translateY(-4px);
        }
        .card-img-zone {
            height: 160px;
            background: linear-gradient(135deg, #0A2540, #1E3A6B);
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
        }
        .card-img-zone img {
            width: 100%;
            height: 160px;
            object-fit: cover;
        }
        .card-title {
            font-family: 'Playfair Display', serif;
            color: white;
            font-size: 13px;
            text-align: center;
            padding: 6px 4px 2px;
            font-weight: 700;
            line-height: 1.2;
        }
        .card-price {
            font-family: 'Cinzel', serif;
            color: #F2C94C;
            font-size: 15px;
            text-align: center;
            font-weight: 700;
        }

        .stButton > button {
            background-color: #112B4D !important;
            color: #F2C94C !important;
            border: 1px solid #00E5C0 !important;
            font-family: 'Space Grotesk', sans-serif !important;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-size: 11px !important;
            transition: all 0.2s ease;
        }
        .stButton > button:hover {
            background-color: #1E3A6B !important;
            border-color: #F2C94C !important;
            color: white !important;
        }

        [data-testid="stMetricValue"] {
            color: #F2C94C !important;
            font-family: 'Cinzel', serif;
        }
        .terminal-box {
            background: #0A1F38;
            border: 1px solid #00E5C0;
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 10px;
        }
        </style>
    """, unsafe_allow_html=True)

st.set_page_config(
    page_title="DELPHIA GENESIS | IMAGINARIUM",
    page_icon="🌟",
    layout="wide"
)
apply_genesis_theme()

# =============================================
# HELPERS
# =============================================
def generate_asset_hash(asset_id, sovereign):
    return hashlib.sha256(f"{asset_id}-{sovereign}-GENESIS-2026".encode()).hexdigest()[:24].upper()

def generate_asset_id(name, sovereign):
    raw = f"{name}-{sovereign}-{pd.Timestamp.now().isoformat()}"
    return "GEN-" + hashlib.sha256(raw.encode()).hexdigest()[:8].upper()

def create_genesis_certificate(asset_name, asset_id, sovereign, value, a_hash):
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_auto_page_break(False)
    
    pdf.set_fill_color(10, 37, 64)
    pdf.rect(0, 0, 210, 297, 'F')
    pdf.set_draw_color(157, 78, 221)
    pdf.set_line_width(2)
    pdf.rect(10, 10, 190, 277)
    
    pdf.set_text_color(242, 201, 76)
    pdf.set_font("Courier", "B", 18)
    pdf.cell(0, 20, "DELPHIA GENESIS", ln=1, align="C")
    pdf.set_font("Courier", "", 12)
    pdf.cell(0, 10, "CERTIFICATE OF IMAGINATION", ln=1, align="C")
    
    pdf.set_font("Courier", "B", 28)
    pdf.cell(0, 30, "★", ln=1, align="C")
    
    fields = [
        ("CREATION NAME", str(asset_name).upper()),
        ("GENESIS ID", str(asset_id).upper()),
        ("YOUNG SOVEREIGN", str(sovereign).upper()),
        ("IMAGINED VALUE", f"{float(value):,.0f} IMAGIX"),
        ("CREATION EPOCH", "2026 - GENESIS LAYER"),
        ("STATUS", "IMMUTABLE • SACRED"),
    ]
    
    y = 90
    for label, val in fields:
        pdf.set_xy(25, y)
        pdf.set_font("Courier", "", 9)
        pdf.set_text_color(157, 78, 221)
        pdf.cell(160, 8, label)
        pdf.set_xy(25, y + 8)
        pdf.set_font("Courier", "B", 11)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(160, 10, val)
        y += 28
    
    pdf.output("temp_genesis_cert.pdf")
    with open("temp_genesis_cert.pdf", "rb") as f:
        return f.read()

# =============================================
# SESIÓN
# =============================================
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("🌌 DELPHIA GENESIS | IMAGINARIUM ACCESS")
    st.markdown("### Welcome, Young Sovereign")
    u = st.text_input("Your Name (Kingdom Name)", value="Astra Nova")
    if st.button("ENTER THE IMAGINARIUM", type="primary"):
        st.session_state["authenticated"] = True
        st.session_state["user"] = u
        st.rerun()
    st.stop()

user = st.session_state["user"]

# =============================================
# HEADER
# =============================================
c_head = st.columns([3, 1, 1, 1, 1])
c_head[0].markdown(f"### 🌟 {user} | SPARK OF GENESIS")
c_head[1].metric("IMAGIX BALANCE", "248,750 𝕀")
c_head[2].metric("CREATIONS", "27")
c_head[3].metric("CREATIVE LEVEL", "FLAME III")
if c_head[4].button("✦ LOGOUT"):
    st.session_state["authenticated"] = False
    st.rerun()

st.divider()

tab_vault, tab_quests, tab_market, tab_upload = st.tabs([
    "🌌 MY CREATIONS VAULT",
    "⚔️ QUESTS & PROGRESS",
    "🌠 GENESIS MARKETPLACE",
    "🌱 UPLOAD NEW CREATION"
])

# =============================================
# VAULT
# =============================================
with tab_vault:
    st.markdown("### 🌌 SOVEREIGN CREATIONS VAULT")
    cols = st.columns(5)
    
    example_assets = [
        ("Star Dragon Drawing", "48,200 𝕀", "🖼️"),
        ("The Kingdom of Clouds", "125,000 𝕀", "☁️"),
        ("Robot Friend Story", "32,800 𝕀", "🤖"),
        ("Magic Sword Design", "67,500 𝕀", "⚔️"),
        ("My Family Castle", "89,000 𝕀", "🏰"),
    ]
    
    for i, (name, value, emoji) in enumerate(example_assets):
        with cols[i % 5]:
            with st.container():
                st.markdown(f"""
                <div class="card-shell">
                    <div class="card-img-zone">
                        <span style="font-size:72px;">{emoji}</span>
                    </div>
                    <div class="card-title">{name}</div>
                    <div class="card-price">{value}</div>
                </div>
                """, unsafe_allow_html=True)
                
                b1, b2 = st.columns(2)
                if b1.button("📜 TITLE", key=f"t{i}"):
                    st.session_state['op'] = ('TITLE', {'Asset': name, 'Asset_ID': generate_asset_id(name, user), 'Value': int(value.replace(',', ''))})
                if b2.button("🔀 SPLIT", key=f"s{i}"):
                    st.info("Split functionality coming in next iteration")

# =============================================
# QUESTS
# =============================================
with tab_quests:
    st.markdown("### ⚔️ ACTIVE QUESTS & PROGRESS")
    st.success("**Main Quest:** Design your Personal Kingdom Crest — Reward: **15,000 𝕀**")
    st.info("**Daily Quest:** Create one new drawing or story — Reward: **2,500 𝕀**")

# =============================================
# MARKETPLACE
# =============================================
with tab_market:
    st.markdown("### 🌠 GENESIS MARKETPLACE")
    st.info("Safe trading space for Young Sovereigns • Coming in v0.2")

# =============================================
# UPLOAD
# =============================================
with tab_upload:
    st.markdown("### 🌱 UPLOAD YOUR CREATION")
    asset_name = st.text_input("Creation Name", placeholder="My Fire Unicorn Story")
    uploaded_file = st.file_uploader("Upload Drawing / Story / Craft", type=["jpg","png","pdf"])
    
    if st.button("🌟 REGISTER CREATION", type="primary"):
        if asset_name and uploaded_file:
            st.balloons()
            st.success(f"Creation **{asset_name}** successfully registered on the Genesis Layer!")
        else:
            st.warning("Please enter a name and upload a file.")

# =============================================
# SIDEBAR TERMINAL
# =============================================
with st.sidebar:
    st.markdown("### 🌟 GENESIS TERMINAL")
    st.markdown(f"**Young Sovereign:** {user}")
    st.markdown("**Current Rank:** Flame III")
    st.markdown("**IMAGIX Balance:** 248,750 𝕀")
    st.caption("Delphia Genesis • Layer of Imagination • Sovereign since 2026")

st.caption("Delphia Genesis v0.1 — Where Imagination Becomes Sovereign")