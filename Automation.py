import streamlit as st
import pandas as pd
from collections import Counter

# === 1. Konfiguration & Minimalist White Styling ===
st.set_page_config(page_title="Paletten-Assistent PRO", page_icon="📦", layout="wide")

st.markdown("""
    <style>
    /* Haupt-Hintergrund auf Weiß */
    .stApp { background-color: #FFFFFF; }
    
    /* Alle Container/Karten auf Weiß ohne Schatten für flaches Design */
    div[data-testid="stVerticalBlock"] > div[style*="border"] {
        background-color: #FFFFFF !important;
        border: 1px solid #EEEEEE !important;
        border-radius: 8px;
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
    
    /* Hover-Effekt für Buttons */
    div.stButton > button:hover {
        border-color: #000000 !important;
        background-color: #F9F9F9 !important;
    }

    /* Primärer Button (Hinzufügen) etwas fetter markieren */
    div[data-testid="stBaseButton-primary"] {
        font-weight: bold !important;
        border: 2px solid #333333 !important;
    }

    /* Tabellen-Design clean */
    .stTable {
        background-color: white;
    }
    </style>
""", unsafe_allow_html=True)

# === 2. Daten laden (identisch) ===
EXCEL_PATH = "Expert Automation.xlsx"

@st.cache_data
def load_data(file_path):
    try:
        models = pd.read_excel(file_path, sheet_name="Models")
    except Exception:
        data = {
            "Product code": ["SKU-01", "SKU-02", "SKU-03"],
            "Category code": ["A", "B", "K6"],
            "Product name": ["Hochleistungsmotor A", "Steuergerät B", "Kabeltrommel K6"],
            "Product price": [450.00, 120.50, 45.00],
            "Sub-Categories": ["Motoren", "Elektronik", "Zubehör"]
        }
        models = pd.DataFrame(data)
    return dict(zip(models["Product code"], models["Category code"])), \
           dict(zip(models["Product code"], models["Product name"])), \
           dict(zip(models["Product code"], models["Product price"])), \
           list(models["Product code"])

product_to_category, product_to_name, product_to_price, ALL_PRODUCTS = load_data(EXCEL_PATH)

# Regel-Logik (gekürzt für Übersicht)
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

# === 4. UI Header (Logo vergrößert) ===
# Wir nutzen Columns, um das Logo groß in die Mitte oder links zu setzen
header_col1, header_col2 = st.columns([1, 2])
with header_col1:
    try:
        # Breite von 120 auf 300 erhöht für mehr Sichtbarkeit
        st.image("Logo.png", width=300) 
    except:
        st.title("📦 LOGO")

st.divider()

# Logik für erlaubte Produkte
current_counts = Counter()
for p, q in st.session_state["pallet_items"].items():
    current_counts[product_to_category[p]] += q

allowed_products = [p for p in ALL_PRODUCTS if check_rules({**current_counts, product_to_category[p]: current_counts[product_to_category[p]] + 1})]

# === 5. Haupt-Layout (Zwei Spalten) ===
col1, col2 = st.columns([2, 3], gap="large")

with col1:
    st.subheader(f"📍 Palette #{st.session_state['pallet_number']}")
    
    with st.container():
        if not allowed_products:
            st.success("Palette voll.")
        else:
            selected_sku = st.selectbox("Produkt", options=allowed_products, format_func=lambda x: f"{x} – {product_to_name.get(x, '')}")
            qty = st.number_input("Menge", min_value=1, max_value=24, step=1)
            
            if st.button("➕ Hinzufügen", type="primary"):
                st.session_state["pallet_items"][selected_sku] = st.session_state["pallet_items"].get(selected_sku, 0) + qty
                st.rerun()

    if st.button("🗑️ Palette leeren"):
        st.session_state["pallet_items"] = {}
        st.rerun()

with col2:
    st.subheader("📝 Aktuelle Ladung")
    if st.session_state["pallet_items"]:
        table_data = [{"SKU": p, "Name": product_to_name[p], "Menge": q, "Preis": f"{product_to_price[p]*q:,.2f} €"} 
                      for p, q in st.session_state["pallet_items"].items()]
        st.table(pd.DataFrame(table_data))
        
        total_price = sum(product_to_price[p] * q for p, q in st.session_state["pallet_items"].items())
        st.markdown(f"### **Gesamt: {total_price:,.2f} €**")
        
        if st.button("💾 Palette abschließen", type="primary"):
            st.session_state["pallet_history"].append({"id": st.session_state["pallet_number"], "items": st.session_state["pallet_items"].copy(), "total": total_price})
            st.session_state["pallet_items"], st.session_state["pallet_number"] = {}, st.session_state["pallet_number"] + 1
            st.rerun()
    else:
        st.info("Keine Artikel vorhanden.")

# Historie
st.divider()
st.subheader("📋 Historie")
for pallet in reversed(st.session_state["pallet_history"]):
    with st.expander(f"Palette #{pallet['id']} — {pallet['total']:,.2f} €"):
        st.write(pallet["items"])
