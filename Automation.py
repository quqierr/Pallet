import streamlit as st
import pandas as pd
from collections import Counter

# === 1. Grundeinstellungen & Design ===
st.set_page_config(
    page_title="Palettierung",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Kleines CSS für professionelleren Look (Tabellen und Abstände)
st.markdown("""
    <style>
    .block-container {padding-top: 2rem; padding-bottom: 2rem;}
    div[data-testid="stMetricValue"] {font-size: 1.8rem;}
    </style>
""", unsafe_allow_html=True)

# === 2. Daten & Logik ===
EXCEL_PATH = "Expert Automation.xlsx"

@st.cache_data
def load_data(file_path):
    try:
        models = pd.read_excel(file_path, sheet_name="Models")
    except FileNotFoundError:
        # Dummy-Daten für Demo, falls Datei fehlt
        data = {
            "Product code": ["P1", "P2", "P3", "P4"],
            "Category code": ["A", "B", "K6", "S"],
            "Product name": ["Produkt Alpha", "Produkt Beta", "Karton 6er", "Spezial"],
            "Product price": [100, 50, 20, 200],
            "Sub-Categories": ["Cat A", "Cat B", "Karton", "Special"]
        }
        models = pd.DataFrame(data)

    p_to_cat = dict(zip(models["Product code"], models["Category code"]))
    p_to_name = dict(zip(models["Product code"], models["Product name"]))
    p_to_price = dict(zip(models["Product code"], models["Product price"]))
    all_prods = list(p_to_cat.keys())
    return p_to_cat, p_to_name, p_to_price, all_prods

# Daten laden
try:
    product_to_category, product_to_name, product_to_price, ALL_PRODUCTS = load_data(EXCEL_PATH)
except Exception:
    st.error("Fehler: Datenbank konnte nicht geladen werden.")
    st.stop()

# Regelwerk
PALLET_RULES = [
    {"K1": 1}, {"K2": 2}, {"KB": 2}, {"B": 6}, {"K6": 24},
    {"K8": 6}, {"S": 4}, {"A": 4}, {"T4": 4}, {"T2": 2},
    {"8888": 2},
    {"A": 3, "S": 1}, {"A": 2, "S": 2}, {"A": 1, "S": 3},
    {"A": 2, "B": 2, "K6": 2}, {"A": 1, "S": 1, "B": 2, "K6": 2},
    {"S": 2, "B": 2, "K6": 2}, {"A": 3, "B": 1}, 
    {"A": 2, "S": 1, "B": 1}, {"A": 1, "S": 2, "B": 1},
    {"S": 3, "B": 1},
    {"KB": 1, "B": 1, "A": 1, "K6": 1},
    {"KB": 1, "B": 1, "S": 1, "K6": 1},
    {"A": 2, "K8": 2},
]

def check_rules(cat_counts):
    """Prüft, ob die Kombination erlaubt ist."""
    for rule in PALLET_RULES:
        is_rule_ok = True
        for cat, qty in cat_counts.items():
            if rule.get(cat, 0) < qty:
                is_rule_ok = False
                break
        if is_rule_ok:
            return True
    return False

def get_valid_products_for_next_step(current_items):
    """
    Ermittelt, welche Produkte noch hinzugefügt werden dürfen (mindestens 1 Stück).
    """
    current_counts = Counter()
    for p, q in current_items.items():
        current_counts[product_to_category.get(p)] += q
    
    valid_products = []
    for p in ALL_PRODUCTS:
        test_counts = current_counts.copy()
        cat = product_to_category.get(p)
        test_counts[cat] += 1
        
        if check_rules(test_counts):
            valid_products.append(p)
            
    return valid_products, current_counts

# === 3. Session State ===
if "pallet_number" not in st.session_state:
    st.session_state["pallet_number"] = 1
if "pallet_items" not in st.session_state:
    st.session_state["pallet_items"] = {} 
if "pallet_history" not in st.session_state:
    st.session_state["pallet_history"] = []

# === 4. UI Aufbau ===

# --- Header ---
col_logo, col_title = st.columns([1, 8])
with col_logo:
    try:
        st.image("Logo.png", width=100)
    except:
        st.write("📦")
with col_title:
    st.title("Paletten-Assistent")
    st.markdown("**Interaktive Beladungsplanung**")

st.divider()

# --- Hauptbereich ---
# Wir berechnen VOR dem Rendern, was erlaubt ist
allowed_products, current_cat_counts = get_valid_products_for_next_step(st.session_state["pallet_items"])
is_full = len(allowed_products) == 0 and len(st.session_state["pallet_items"]) > 0

# Grid Layout
left_panel, right_panel = st.columns([1, 1], gap="large")

# --- LINKE SPALTE: Eingabe ---
with left_panel:
    st.subheader(f"1. Auftrag erfassen (Palette #{st.session_state['pallet_number']})")
    
    with st.container(border=True):
        if is_full:
            st.success("✅ Palette ist optimal gefüllt. Keine weiteren Produkte möglich.")
            st.caption("Bitte Palette abschließen, um fortzufahren.")
        else:
            with st.form("add_form", clear_on_submit=True):
                # Nur erlaubte Produkte anzeigen
                sel_prod = st.selectbox(
                    "Verfügbares Produkt wählen", 
                    options=allowed_products,
                    format_func=lambda x: f"{x} – {product_to_name.get(x, '')}",
                    help="Es werden nur Produkte angezeigt, die noch auf die Palette passen."
                )
                
                # Mengenauswahl (könnte man noch dynamischer begrenzen, hier einfach 1-10)
                sel_qty = st.number_input("Anzahl Gebinde", min_value=1, max_value=10, step=1)
                
                if st.form_submit_button("⬇️ Zur Palette hinzufügen", use_container_width=True, type="primary"):
                    # Double Check Logic
                    test_counts = current_cat_counts.copy()
                    cat = product_to_category.get(sel_prod)
                    test_counts[cat] += sel_qty
                    
                    if check_rules(test_counts):
                        st.session_state["pallet_items"][sel_prod] = st.session_state["pallet_items"].get(sel_prod, 0) + sel_qty
                        st.rerun()
                    else:
                        st.toast("⚠️ Menge zu hoch! Das passt nicht mehr drauf.", icon="❌")

# --- RECHTE SPALTE: Aktueller Status ---
with right_panel:
    st.subheader("2. Aktueller Paletteninhalt")
    
    # Live Berechnung Preis
    current_total = sum(product_to_price.get(p, 0) * q for p, q in st.session_state["pallet_items"].items())
    item_count = sum(st.session_state["pallet_items"].values())

    # KPI Row
    kpi1, kpi2 = st.columns(2)
    kpi1.metric("Gesamtwert", f"{current_total:.2f} €")
    kpi2.metric("Gebinde", f"{item_count} Stk")

    # Tabelle statt Liste
    if st.session_state["pallet_items"]:
        df_items = []
        for p, q in st.session_state["pallet_items"].items():
            single_price = product_to_price.get(p, 0)
            df_items.append({
                "SKU": p,
                "Produkt": product_to_name.get(p, ""),
                "Menge": q,
                "Preis": f"{single_price * q:.2f} €"
            })
        
        st.dataframe(
            pd.DataFrame(df_items), 
            hide_index=True, 
            use_container_width=True,
            column_config={
                "Menge": st.column_config.NumberColumn("Menge", format="%d")
            }
        )
        
        # Aktionen
        col_btn1, col_btn2 = st.columns(2)
        if col_btn1.button("🗑️ Leeren", use_container_width=True):
            st.session_state["pallet_items"] = {}
            st.rerun()
            
        if col_btn2.button("💾 Palette abschließen", type="primary", use_container_width=True):
            # Speichern
            st.session_state["pallet_history"].append({
                "id": st.session_state["pallet_number"],
                "items": st.session_state["pallet_items"].copy(),
                "total": current_total,
                "timestamp": pd.Timestamp.now().strftime("%H:%M")
            })
            st.toast(f"Palette #{st.session_state['pallet_number']} gespeichert!", icon="✅")
            st.session_state["pallet_number"] += 1
            st.session_state["pallet_items"] = {}
            st.rerun()
            
    else:
        st.info("Noch keine Produkte geladen.")


# === 5. SIDEBAR: Historie ===
with st.sidebar:
    st.header("📋 Verlauf")
    
    if not st.session_state["pallet_history"]:
        st.caption("Noch keine Paletten fertiggestellt.")
    else:
        grand_total = sum(h["total"] for h in st.session_state["pallet_history"])
        st.metric("Gesamtumsatz (Session)", f"{grand_total:.2f} €")
        st.divider()
        
        # Rückwärts sortieren (neueste zuerst)
        for entry in reversed(st.session_state["pallet_history"]):
            with st.expander(f"Palette #{entry['id']} ({entry['timestamp']})"):
                st.write(f"**Summe: {entry['total']:.2f} €**")
                for p, q in entry["items"].items():
                    st.write(f"- {q}x {p}")
