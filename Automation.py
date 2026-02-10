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
import base64

def get_base64(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

# Logo laden und in Base64 konvertieren (um es direkt im HTML zu nutzen)
try:
    logo_base64 = get_base64("Logo 2.png")
    logo_html = f'<img src="data:image/png;base64,{logo_base64}" width="250">'
except:
    logo_html = '<div style="font-size:30px; font-weight:bold;">[LOGO]</div>'

# Der kombinierte Flexbox-Header
st.markdown(
    f"""
    <div style="display: flex; align-items: center; gap: 30px; margin-bottom: 20px;">
        <div>
            {logo_html}
        </div>
        <div style="display: flex; flex-direction: column; justify-content: center;">
            <h1 style="margin: 0; padding: 0; line-height: 1.2; font-size: 42px;">Paletten-Management</h1>
            <p style="margin: 0; padding: 0; font-size: 20px; color: #666666;">Play with the number ones</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

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
            selected_sku = st.selectbox(
                "Produkt wählen", 
                options=allowed_products, 
                format_func=lambda x: f"{x} – {product_to_name.get(x, '')}"
            )
            qty = st.number_input("Menge", min_value=1, max_value=24, step=1)
            
            st.write("") # Kleiner Abstandshalter

            # --- Alle drei Buttons in einer Reihe ---
            btn_col1, btn_col2, btn_col3 = st.columns(3)
            
            with btn_col1:
                # Primäre Aktion: Hinzufügen
                if st.button("➕ Hinzufügen", type="primary", use_container_width=True):
                    st.session_state["pallet_items"][selected_sku] = st.session_state["pallet_items"].get(selected_sku, 0) + qty
                    st.rerun()
            
            with btn_col2:
                # Sekundäre Aktion: Abschließen/Speichern
                # Wir aktivieren den Button nur, wenn auch etwas auf der Palette liegt
                if st.button("💾 Speichern", use_container_width=True, disabled=not st.session_state["pallet_items"]):
                    total_price = sum(product_to_price[p] * q for p, q in st.session_state["pallet_items"].items())
                    st.session_state["pallet_history"].append({
                        "id": st.session_state["pallet_number"], 
                        "items": st.session_state["pallet_items"].copy(), 
                        "total": total_price
                    })
                    st.session_state["pallet_items"], st.session_state["pallet_number"] = {}, st.session_state["pallet_number"] + 1
                    st.rerun()

            with btn_col3:
                # Destruktive Aktion: Leeren
                if st.button("🗑️ Leeren", use_container_width=True):
                    st.session_state["pallet_items"] = {}
                    st.rerun()

# Historie
st.divider()
st.subheader("📋 Historie abgeschlossener Paletten")

if not st.session_state["pallet_history"]:
    st.info("Noch keine Paletten in der Historie gespeichert.")
else:
    # Wir gehen die Historie von neu nach alt durch
    for pallet in reversed(st.session_state["pallet_history"]):
        # Jede Palette bekommt einen eigenen Container (weiße Karte mit Rahmen)
        with st.container(border=True):
            # Header der Karte: Nummer und Gesamtpreis
            h_col1, h_col2 = st.columns([1, 1])
            with h_col1:
                st.markdown(f"#### 📦 Palette #{pallet['id']}")
            with h_col2:
                st.markdown(f"<h4 style='text-align: right; color: #1a4a73;'>{pallet['total']:,.2f} €</h4>", unsafe_allow_html=True)
            
            # Die Artikelliste als saubere Tabelle aufbereiten
            hist_items = []
            for sku, qty in pallet["items"].items():
                hist_items.append({
                    "Artikelnr.": sku,
                    "Bezeichnung": product_to_name.get(sku, "Unbekannt"),
                    "Menge": f"{qty} Stk.",
                    "Einzelpreis": f"{product_to_price.get(sku, 0):,.2f} €"
                })
            
            # Tabelle anzeigen ohne Index
            st.dataframe(
                pd.DataFrame(hist_items), 
                use_container_width=True, 
                hide_index=True
            )
            
            # Kleiner Abstand zwischen den Paletten
            st.write("")
