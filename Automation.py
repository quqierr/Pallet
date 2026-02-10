import streamlit as st
import pandas as pd
from collections import Counter

# === 1. Konfiguration & Custom Styling ===
st.set_page_config(page_title="Paletten-Assistent", page_icon="📦", layout="wide")

# Custom CSS für professionelle Farben und Buttons
st.markdown("""
    <style>
    /* Hintergrund und Schrift */
    .stApp { background-color: #f8f9fa; }
    
    /* Buttons anpassen */
    div.stButton > button:first-child {
        border-radius: 5px;
        height: 3em;
        transition: all 0.3s;
    }
    
    /* Primärer Button (Hinzufügen / Speichern) */
    div[data-testid="stBaseButton-primary"] {
        background-color: #1a4a73 !important;
        border: none !important;
        color: white !important;
    }
    
    /* Roter Button (Leeren/Löschen) */
    div.stButton > button:contains("Leeren") {
        color: white !important;
        border: 1px solid #d9534f !important;
    }

    /* Karten-Look für Container */
    div[data-testid="stVerticalBlock"] > div[style*="border"] {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

# === 2. Daten laden ===
EXCEL_PATH = "Expert Automation.xlsx"

@st.cache_data
def load_data(file_path):
    try:
        models = pd.read_excel(file_path, sheet_name="Models")
    except Exception:
        # Fallback für Testzwecke
        data = {
            "Product code": ["SKU-01", "SKU-02", "SKU-03"],
            "Category code": ["A", "B", "K6"],
            "Product name": ["Hochleistungsmotor A", "Steuergerät B", "Kabeltrommel K6"],
            "Product price": [450.00, 120.50, 45.00],
            "Sub-Categories": ["Motoren", "Elektronik", "Zubehör"]
        }
        models = pd.DataFrame(data)

    p_to_cat = dict(zip(models["Product code"], models["Category code"]))
    p_to_name = dict(zip(models["Product code"], models["Product name"]))
    p_to_price = dict(zip(models["Product code"], models["Product price"]))
    p_to_cat_fullname = dict(zip(models["Product code"], models["Sub-Categories"]))
    all_prods = list(p_to_cat.keys())
    return p_to_cat, p_to_name, p_to_price, p_to_cat_fullname, all_prods

product_to_category, product_to_name, product_to_price, product_to_cat_fullname, ALL_PRODUCTS = load_data(EXCEL_PATH)

# === 3. Regel-Logik ===
PALLET_RULES = [
    {"K1": 1}, {"K2": 2}, {"KB": 2}, {"B": 6}, {"K6": 24}, {"K8": 6}, {"S": 4}, {"A": 4},
    {"T4": 4}, {"T2": 2}, {"8888": 2}, {"A": 3, "S": 1}, {"A": 2, "S": 2}, {"A": 1, "S": 3},
    {"A": 2, "B": 2, "K6": 2}, {"A": 1, "S": 1, "B": 2, "K6": 2}, {"S": 2, "B": 2, "K6": 2},
    {"A": 3, "B": 1}, {"A": 2, "S": 1, "B": 1}, {"A": 1, "S": 2, "B": 1}, {"S": 3, "B": 1},
    {"KB": 1, "B": 1, "A": 1, "K6": 1}, {"KB": 1, "B": 1, "S": 1, "K6": 1}, {"A": 2, "K8": 2},
]

def check_rules(cat_counts):
    for rule in PALLET_RULES:
        is_rule_ok = True
        for cat, qty in cat_counts.items():
            if rule.get(cat, 0) < qty:
                is_rule_ok = False
                break
        if is_rule_ok: return True
    return False

# === 4. Session State ===
if "pallet_number" not in st.session_state: st.session_state["pallet_number"] = 1
if "pallet_items" not in st.session_state: st.session_state["pallet_items"] = {}
if "pallet_history" not in st.session_state: st.session_state["pallet_history"] = []

# === 5. UI Layout ===

# Header
col_logo, col_text = st.columns([1, 3])
with col_logo:
    try: st.image("Logo.png", width=150)
    except: st.title("📦")
with col_text:
    st.write(f"### Pallet Management")
    st.caption("Play with the number ones")

st.divider()

# Aktuelle Berechnungen
current_counts = Counter()
for p, q in st.session_state["pallet_items"].items():
    current_counts[product_to_category[p]] += q

# Dynamische Filterung: Welche Produkte dürfen noch hinzugefügt werden?
allowed_products = []
for p in ALL_PRODUCTS:
    test_counts = current_counts.copy()
    test_counts[product_to_category[p]] += 1
    if check_rules(test_counts):
        allowed_products.append(p)

# --- Hauptbereich in zwei Spalten (wie gewünscht) ---
col1, col2 = st.columns([2, 3], gap="large")

with col1:
    st.subheader(f"Aktuelle Palette #{st.session_state['pallet_number']}")
    
    with st.container(border=True):
        if not allowed_products:
            st.success("✅ Diese Palette hat ihre maximale Kapazität erreicht.")
        else:
            selected_sku = st.selectbox(
                "Produkt auswählen",
                options=allowed_products,
                format_func=lambda x: f"{x} – {product_to_name.get(x, 'Unknown')}"
            )
            qty = st.number_input("Menge", min_value=1, max_value=24, step=1)
            
            if st.button("➕ Artikel hinzufügen", type="primary", use_container_width=True):
                # Validierung der Menge
                test_counts = current_counts.copy()
                test_counts[product_to_category[selected_sku]] += qty
                if check_rules(test_counts):
                    st.session_state["pallet_items"][selected_sku] = st.session_state["pallet_items"].get(selected_sku, 0) + qty
                    st.rerun()
                else:
                    st.error("Diese Menge überschreitet das Limit der Palette!")

    # Status-Box
    st.write("#### Status-Monitor")
    if not st.session_state["pallet_items"]:
        st.info("Palette ist leer. Bitte Produkte hinzufügen.")
    elif allowed_products:
        st.info(f"Platz vorhanden. {len(allowed_products)} verschiedene Produkte passen noch.")
    else:
        st.success("Palette ist voll (Regelkonform).")

with col2:
    st.subheader("Ladungsübersicht")
    
    if st.session_state["pallet_items"]:
        # Daten für Tabelle aufbereiten
        table_data = []
        total_price = 0
        for p, q in st.session_state["pallet_items"].items():
            price = product_to_price[p] * q
            total_price += price
            table_data.append({
                "SKU": p,
                "Name": product_to_name[p],
                "Menge": q,
                "Preis (€)": f"{price:,.2f}"
            })
        
        st.table(pd.DataFrame(table_data))
        
        st.write(f"### **Gesamtwert: {total_price:,.2f} €**")
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🗑️ Palette leeren", use_container_width=True):
                st.session_state["pallet_items"] = {}
                st.rerun()
        with c2:
            if st.button("💾 Palette abschließen", type="primary", use_container_width=True):
                st.session_state["pallet_history"].append({
                    "id": st.session_state["pallet_number"],
                    "items": st.session_state["pallet_items"].copy(),
                    "total": total_price
                })
                st.session_state["pallet_items"] = {}
                st.session_state["pallet_number"] += 1
                st.rerun()
    else:
        st.write("Keine Artikel auf der aktuellen Palette.")

# --- Historie am Ende der Seite ---
st.divider()
st.subheader("📦 Abgeschlossene Paletten (Verlauf)")

if not st.session_state["pallet_history"]:
    st.caption("Noch keine abgeschlossenen Paletten in dieser Sitzung.")
else:
    for pallet in reversed(st.session_state["pallet_history"]):
        with st.expander(f"Palette #{pallet['id']} — Gesamt: {pallet['total']:,.2f} €"):
            hist_data = []
            for p, q in pallet["items"].items():
                hist_data.append({"SKU": p, "Name": product_to_name[p], "Menge": q})
            st.table(pd.DataFrame(hist_data))
