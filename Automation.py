import streamlit as st
import pandas as pd
from collections import Counter

# === 1. Konfiguration & Minimalist White Styling ===
st.set_page_config(page_title="Paletten-Assistent PRO", page_icon="📦", layout="wide")

st.markdown("""
    <style>
    /* Haupt-Hintergrund auf Weiß */
    .stApp { background-color: #FFFFFF; }
    
    /* Header-Bereich Styling */
    .header-box {
        display: flex;
        align-items: center;
        gap: 20px;
        padding-bottom: 20px;
    }

    /* Buttons: Weißer Hintergrund, schwarze Schrift, grauer Rahmen */
    div.stButton > button {
        background-color: #FFFFFF !important;
        color: #333333 !important;
        border: 1px solid #CCCCCC !important;
        border-radius: 4px !important;
        height: 3em;
        width: 100%;
        transition: all 0.2s;
    }
    
    div.stButton > button:hover {
        border-color: #000000 !important;
        background-color: #F9F9F9 !important;
    }

    /* Primärer Button (Hinzufügen & Abschließen) */
    div[data-testid="stBaseButton-primary"] {
        font-weight: bold !important;
        border: 2px solid #333333 !important;
    }

    /* Tabellen Styling */
    .stTable { background-color: white; }
    </style>
""", unsafe_allow_html=True)

# === 2. Daten laden ===
EXCEL_PATH = "Expert Automation.xlsx"

@st.cache_data
def load_data(file_path):
    try:
        models = pd.read_excel(file_path, sheet_name="Models")
    except Exception:
        # Dummy Daten falls Excel nicht da
        data = {
            "Product code": ["SKU-01", "SKU-02", "SKU-03"],
            "Category code": ["A", "B", "K6"],
            "Product name": ["Produkt Alpha", "Steuerung Beta", "Kabel K6"],
            "Product price": [450.0, 120.0, 45.0],
            "Sub-Categories": ["A-Klasse", "B-Klasse", "Zubehör"]
        }
        models = pd.DataFrame(data)
    
    p_to_cat = dict(zip(models["Product code"], models["Category code"]))
    p_to_name = dict(zip(models["Product code"], models["Product name"]))
    p_to_price = dict(zip(models["Product code"], models["Product price"]))
    all_prods = list(p_to_cat.keys())
    return p_to_cat, p_to_name, p_to_price, all_prods

product_to_category, product_to_name, product_to_price, ALL_PRODUCTS = load_data(EXCEL_PATH)

# Regelwerk (Beispielhaft)
PALLET_RULES = [{"K1": 1}, {"K2": 2}, {"KB": 2}, {"B": 6}, {"K6": 24}, {"K8": 6}, {"S": 4}, {"A": 4}]

def check_rules(cat_counts):
    for rule in PALLET_RULES:
        is_rule_ok = True
        for cat, qty in cat_counts.items():
            if rule.get(cat, 0) < qty:
                is_rule_ok = False
                break
        if is_rule_ok: return True
    return False

# === 3. Session State ===
if "pallet_number" not in st.session_state: st.session_state["pallet_number"] = 1
if "pallet_items" not in st.session_state: st.session_state["pallet_items"] = {}
if "pallet_history" not in st.session_state: st.session_state["pallet_history"] = []

# === 4. UI Header (Logo + Titel kombiniert) ===
col_logo, col_title = st.columns([1, 3])
with col_logo:
    try:
        st.image("Logo.png", width=200) # Angemessene Größe
    except:
        st.write("### [LOGO]")

with col_title:
    # Der Titel bleibt erhalten und ist vertikal etwas versetzt für die Optik
    st.markdown("<br>", unsafe_allow_html=True)
    st.title("Play with the number ones")

st.divider()

# Aktuelle Logik
current_counts = Counter()
for p, q in st.session_state["pallet_items"].items():
    current_counts[product_to_category[p]] += q

allowed_products = [p for p in ALL_PRODUCTS if check_rules({**current_counts, product_to_category[p]: current_counts[product_to_category[p]] + 1})]

# === 5. Haupt-Layout ===
col1, col2 = st.columns([2, 3], gap="large")

with col1:
    st.subheader(f"📍 Aktuelle Palette #{st.session_state['pallet_number']}")
    
    with st.container():
        if not allowed_products:
            st.success("Diese Palette ist optimal ausgelastet.")
        else:
            selected_sku = st.selectbox("Produkt wählen", options=allowed_products, format_func=lambda x: f"{x} – {product_to_name.get(x, '')}")
            qty = st.number_input("Menge", min_value=1, max_value=24, step=1)
            
            if st.button("➕ Zum Auftrag hinzufügen", type="primary"):
                st.session_state["pallet_items"][selected_sku] = st.session_state["pallet_items"].get(selected_sku, 0) + qty
                st.rerun()

    if st.button("🗑️ Palette leeren"):
        st.session_state["pallet_items"] = {}
        st.rerun()

with col2:
    st.subheader("📝 Ladungsübersicht")
    if st.session_state["pallet_items"]:
        table_data = [{"SKU": p, "Name": product_to_name[p], "Menge": q, "Einzelpreis": f"{product_to_price[p]:,.2f} €", "Summe": f"{product_to_price[p]*q:,.2f} €"} 
                      for p, q in st.session_state["pallet_items"].items()]
        st.table(pd.DataFrame(table_data))
        
        total_price = sum(product_to_price[p] * q for p, q in st.session_state["pallet_items"].items())
        st.markdown(f"### **Gesamtwert: {total_price:,.2f} €**")
        
        if st.button("💾 Palette abschließen & Speichern", type="primary"):
            st.session_state["pallet_history"].append({
                "id": st.session_state["pallet_number"], 
                "items": st.session_state["pallet_items"].copy(), 
                "total": total_price
            })
            st.session_state["pallet_items"], st.session_state["pallet_number"] = {}, st.session_state["pallet_number"] + 1
            st.rerun()
    else:
        st.info("Die Palette ist aktuell leer.")

# Historie
st.divider()
st.subheader("📋 Historie abgeschlossener Paletten")
if not st.session_state["pallet_history"]:
    st.caption("Noch keine Paletten gespeichert.")
else:
    for pallet in reversed(st.session_state["pallet_history"]):
        with st.expander(f"Palette #{pallet['id']} — Gesamtwert: {pallet['total']:,.2f} €"):
            st.write(pallet["items"])
