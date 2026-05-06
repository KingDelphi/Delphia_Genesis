import streamlit as st
import pandas as pd
import os
import hashlib
import tempfile
from fpdf import FPDF
from PIL import Image
import io

# =============================================
# TEMA VISUAL GENESIS v0.4
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
            background: linear-gradient(180deg, #0A2540 0%, #05121f 100%);
        }

        .card-shell {
            background-color: #112B4D;
            border: 1px solid #00E5C0;
            border-radius: 12px;
            overflow: hidden;
            height: 325px;
            display: flex;
            flex-direction: column;
            transition: all 0.3s ease;
            position: relative;
        }
        .card-shell:hover {
            border-color: #F2C94C;
            box-shadow: 0 0 30px rgba(242, 201, 76, 0.4);
            transform: translateY(-6px);
        }
        .card-img-zone {
            height: 170px;
            background: linear-gradient(135deg, #0A2540, #1E3A6B);
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
        }
        .card-title {
            font-family: 'Playfair Display', serif;
            color: white;
            font-size: 13.5px;
            text-align: center;
            padding: 8px 6px 4px;
            font-weight: 700;
            line-height: 1.2;
        }
        .card-price {
            font-family: 'Cinzel', serif;
            color: #F2C94C;
            font-size: 16px;
            text-align: center;
            font-weight: 700;
        }
        .stButton > button {
            background-color: #112B4D !important;
            color: #F2C94C !important;
            border: 1px solid #00E5C0 !important;
            font-family: 'Space Grotesk', sans-serif !important;
            text-transform: uppercase;
            letter-spacing: 1.2px;
            transition: all 0.25s ease;
        }
        .stButton > button:hover {
            background-color: #1E3A6B !important;
            border-color: #F2C94C !important;
            color: white !important;
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
def clean_value(val):
    """Limpia strings con comas para convertir a float"""
    if isinstance(val, str):
        return float(val.replace(',', '').replace(' ', ''))
    return float(val)

def generate_asset_id(name, sovereign):
    raw = f"{name}-{sovereign}-{pd.Timestamp.now().isoformat()}"
    return "GEN-" + hashlib.sha256(raw.encode()).hexdigest()[:8].upper()

def create_genesis_certificate(asset_name, asset_id, sovereign, value):
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_auto_page_break(False)
    
    pdf.set_fill_color(10, 37, 64)
    pdf.rect(0, 0, 210, 297, 'F')
    pdf.set_draw_color(157, 78, 221)
    pdf.set_line_width(2.5)
    pdf.rect(12, 12, 186, 273)
    
    pdf.set_text_color(242, 201, 76)
    pdf.set_font("Courier", "B", 20)
    pdf.cell(0, 25, "DELPHIA GENESIS", ln=1, align="C")
    pdf.set_font("Courier", "", 13)
    pdf.cell(0, 12, "CERTIFICATE OF IMAGINATION", ln=1, align="C")
    
    pdf.set_font("Courier", "B", 32)
    pdf.cell(0, 35, "★", ln=1, align="C")
    
    fields = [
        ("CREATION", str(asset_name).upper()),
        ("GENESIS ID", str(asset_id)),
        ("YOUNG SOVEREIGN", str(sovereign).upper()),
        ("IMAGINED VALUE", f"{int(clean_value(value)):,} IMAGIX"),
        ("DATE", "MAY 2026"),
        ("STATUS", "SACRED & IMMUTABLE"),
    ]
    
    y = 95
    for label, val in fields:
        pdf.set_xy(30, y)
        pdf.set_font("Courier", "", 10)
        pdf.set_text_color(157, 78, 221)
        pdf.cell(150, 8, label)
        pdf.set_xy(30, y + 9)
        pdf.set_font("Courier", "B", 12)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(150, 12, val)
        y += 32
    
    pdf.output("genesis_certificate.pdf")
    with open("genesis_certificate.pdf", "rb") as f:
        return f.read()

# =============================================
# SESIÓN
# =============================================
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("🌌 DELPHIA GENESIS | IMAGINARIUM")
    st.markdown("### Welcome, Young Sovereign")
    u = st.text_input("Kingdom Name", value="Astra Nova")
    if st.button("ENTER THE IMAGINARIUM", type="primary"):
        st.session_state["authenticated"] = True
        st.session_state["user"] = u
        st.rerun()
    st.stop()

user = st.session_state["user"]

# Header
c = st.columns([3,1,1,1,1])
c[0].markdown(f"### 🌟 {user} | SPARK OF GENESIS")
c[1].metric("IMAGIX", "248,750 𝕀")
c[2].metric("CREATIONS", "27")
c[3].metric("RANK", "FLAME III")
if c[4].button("✦ LOGOUT"):
    st.session_state["authenticated"] = False
    st.rerun()

st.divider()

tab_vault, tab_quests, tab_market, tab_upload = st.tabs([
    "🌌 MY CREATIONS VAULT",
    "⚔️ QUESTS & PROGRESS",
    "🌠 MARKETPLACE",
    "🌱 UPLOAD CREATION"
])

# Vault v0.4
with tab_vault:
    st.markdown("### 🌌 SOVEREIGN CREATIONS VAULT")
    cols = st.columns(5)
    
    examples = [
        ("Star Dragon Awakening", "48200", "🐉"),
        ("Kingdom of Eternal Clouds", "125000", "☁️"),
        ("The Brave Robot Friend", "32800", "🤖"),
        ("Legendary Enchanted Sword", "67500", "⚔️"),
        ("My Family's Floating Castle", "89000", "🏰"),
    ]
    
    for i, (name, value_str, emoji) in enumerate(examples):
        value = int(value_str)
        with cols[i % 5]:
            st.markdown(f"""
            <div class="card-shell">
                <div class="card-img-zone"><span style="font-size:78px;">{emoji}</span></div>
                <div class="card-title">{name}</div>
                <div class="card-price">{value:,} 𝕀</div>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            if col1.button("📜 TITLE", key=f"title_{i}"):
                pdf_bytes = create_genesis_certificate(name, generate_asset_id(name, user), user, value)
                st.download_button(
                    label="⬇️ Download Certificate",
                    data=pdf_bytes,
                    file_name=f"{name.replace(' ', '_')}_Certificate.pdf",
                    mime="application/pdf",
                    key=f"dl_{i}"
                )
            if col2.button("🔀 SPLIT", key=f"split_{i}"):
                st.success(f"Split activated for {name} (Demo)")

# Quests
with tab_quests:
    st.markdown("### ⚔️ QUESTS & PROGRESS")
    st.success("**Main Quest:** Design your Personal Kingdom Crest — **Reward: 15,000 𝕀**")
    st.info("**Daily Quest:** Create one new piece — **Reward: 2,500 𝕀**")
    st.progress(65, text="Progress to next rank: STAR I")

# Marketplace & Upload
with tab_market:
    st.info("🌠 Genesis Marketplace — Safe trading for Young Sovereigns (v0.5)")

with tab_upload:
    st.markdown("### 🌱 UPLOAD YOUR CREATION")
    name = st.text_input("Creation Name", placeholder="The Adventures of Luna the Fox")
    file = st.file_uploader("Upload your art / story / craft", type=["jpg","png","pdf"])
    if st.button("🌟 REGISTER IN GENESIS", type="primary") and name and file:
        st.balloons()
        st.success(f"**{name}** has been successfully registered on the Genesis Layer!")

# Sidebar
with st.sidebar:
    st.markdown("### 🌟 GENESIS TERMINAL")
    st.write(f"**Young Sovereign:** {user}")
    st.write("**Current Rank:** Flame III")
    st.write("**IMAGIX:** 248,750 𝕀")
    st.caption("Delphia Genesis v0.4")

st.caption("Delphia Genesis v0.4 — Where Imagination Becomes Sovereign")