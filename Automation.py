import streamlit as st
import pandas as pd
from collections import Counter

# === 1. Konfiguration & Layout ===
st.set_page_config(page_title="Pallet Assistant", page_icon="📦", layout="wide")

col1, col2 = st.columns([1, 6])
with col1:
    # Falls das Bild nicht existiert, fangen wir den Fehler ab, damit die App nicht crasht
    try:
        st.image("Logo.png", width=150)
    except:
        st.write("📦") # Platzhalter
with col2:
    st.markdown(
        """
        <div style="display: flex; align-items: center; height: 70px;">
            <h2 style="margin: 0;">Play with the number ones</h2>
        </div>
        """, 
        unsafe_allow_html=True
    )

st.divider()
st.title("📦 Paletten-Assistent")

# === 2. Daten laden ===
EXCEL_PATH = "Expert Automation.xlsx"

@st.cache_data
def load_data(file_path):
    # Fallback für Demo-Zwecke, falls Datei fehlt (für Copy-Paste User hilfreich)
    try:
        models = pd.read_excel(file_path, sheet_name="Models")
    except FileNotFoundError:
        st.error(f"Datei '{file_path}' nicht gefunden. Bitte Pfad prüfen.")
        return {}, {}, {}, {}, []

    p_to_cat = dict(zip(models["Product code"], models["Category code"]))
    p_to_name = dict(zip(models["Product code"], models["Product name"]))
    p_to_price = dict(zip(models["Product code"], models["Product price"]))
    p_to_cat_fullname = dict(zip(models["Product code"], models["Sub-Categories"]))
    all_prods = list(p_to_cat.keys())
    
    return p_to_cat, p_to_name, p_to_price, p_to_cat_fullname, all_prods

# Daten initialisieren
try:
    product_to_category, product_to_name, product_to_price, product_to_cat_fullname, ALL_PRODUCTS = load_data(EXCEL_PATH)
except Exception as e:
    st.error(f"Fehler beim Laden der Daten: {e}")
    st.stop()

# === 3. Regelwerk ===
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
    """Prüft, ob die aktuelle Beladung EINER der Regeln entspricht (also 'in Ordnung' ist)."""
    for rule in PALLET_RULES:
        is_rule_ok = True
        for cat, qty in cat_counts.items():
            # Wenn wir mehr haben als die Regel erlaubt, passt diese Regel nicht
            if rule.get(cat, 0) < qty:
                is_rule_ok = False
                break
        if is_rule_ok:
            return True
    return False

# === 4. Session State ===
if "pallet_number" not in st.session_state:
    st.session_state["pallet_number"] = 1
if "pallet_items" not in st.session_state:
    st.session_state["pallet_items"] = {}  # {sku: qty}
if "pallet_history" not in st.session_state:
    st.session_state["pallet_history"] = [] # Liste von Dicts: [{"items": {...}, "total": 123.45}]

# === 5. UI: Produkte hinzufügen ===
st.subheader(f"1️⃣ Produkte hinzufügen (Palette #{st.session_state['pallet_number']})")

with st.form("add_product_form", clear_on_submit=True):
    col_input1, col_input2, col_btn = st.columns([3, 1, 1])
    
    with col_input1:
        selected_sku = st.selectbox(
            "Produkt", 
            options=ALL_PRODUCTS, 
            format_func=lambda x: f"{x} – {product_to_name.get(x, 'Unknown')}"
        )
    
    with col_input2:
        qty_input = st.number_input("Menge", min_value=1, max_value=50, step=1, value=1)
        
    with col_btn:
        st.write("") # Spacer
        st.write("") # Spacer
        add_submitted = st.form_submit_button("➕ Hinzufügen")

    if add_submitted:
        # Logik: Wenn Produkt schon da, Menge addieren, sonst neu anlegen
        if selected_sku in st.session_state["pallet_items"]:
            st.session_state["pallet_items"][selected_sku] += qty_input
        else:
            st.session_state["pallet_items"][selected_sku] = qty_input
        st.rerun()

# === 6. UI: Aktuelle Palette prüfen ===
st.divider()
col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("2️⃣ Inhalt der aktuellen Palette")
    
    if not st.session_state["pallet_items"]:
        st.info("Die Palette ist noch leer.")
        current_total_price = 0.0
        current_counts = Counter()
        is_current_valid = True # Leere Palette ist technisch gesehen "gültig" oder neutral
        can_add_more = True
    else:
        # Berechnung
        current_counts = Counter()
        current_total_price = 0.0
        
        # Liste anzeigen
        for p, q in st.session_state["pallet_items"].items():
            line_price = product_to_price.get(p, 0) * q
            current_total_price += line_price
            
            # Kategorie zählen
            cat = product_to_category.get(p, "Unknown")
            current_counts[cat] += q
            
            st.write(f"▪️ **{q}x** {product_to_name.get(p, p)} ({p}) — {line_price:.2f} €")

        st.markdown(f"#### **Summe: {current_total_price:.2f} €**")
        
        # Validierung
        is_current_valid = check_rules(current_counts)
        
        # Prüfen ob noch Platz ist
        can_add_more = False
        for p in ALL_PRODUCTS:
            test_counts = current_counts.copy()
            cat = product_to_category.get(p)
            if cat:
                test_counts[cat] += 1
                if check_rules(test_counts):
                    can_add_more = True
                    break

with col_right:
    st.subheader("Status")
    
    if not st.session_state["pallet_items"]:
        st.write("⚪ Warte auf Produkte...")
    elif not is_current_valid:
        st.error("❌ Palette ist überladen/ungültig")
        st.caption("Die aktuelle Kombination passt in keine der definierten Regeln.")
    elif is_current_valid and not can_add_more:
        st.success("✅ Palette ist voll")
        st.caption("Maximale Kapazität erreicht.")
    else:
        st.info("✅ Palette ist gültig (Platz vorhanden)")
        # Vorschläge berechnen
        allowed_cats = set()
        for p in ALL_PRODUCTS:
            test_counts = current_counts.copy()
            cat = product_to_category.get(p)
            if cat:
                test_counts[cat] += 1
                if check_rules(test_counts):
                    allowed_cats.add(product_to_cat_fullname.get(p, cat))
        
        if allowed_cats:
            with st.expander("Was passt noch dazu?"):
                st.write(", ".join(sorted(allowed_cats)))

# === 7. UI: Aktionen (Speichern / Reset) ===
st.divider()
col_actions1, col_actions2 = st.columns(2)

with col_actions1:
    if st.button("🗑️ Aktuelle Palette leeren (Reset)"):
        st.session_state["pallet_items"] = {}
        st.rerun()

with col_actions2:
    # Button nur aktiv, wenn Items drauf sind und Palette gültig ist (optional)
    if st.button("💾 Palette abschließen & Neue beginnen", type="primary", disabled=not st.session_state["pallet_items"]):
        if not is_current_valid:
            st.warning("Achtung: Du speicherst eine ungültige Palette!")
        
        # 1. Speichern
        pallet_record = {
            "id": st.session_state["pallet_number"],
            "items": st.session_state["pallet_items"].copy(),
            "total_price": current_total_price
        }
        st.session_state["pallet_history"].append(pallet_record)
        
        # 2. Reset & Hochzählen
        st.session_state["pallet_items"] = {}
        st.session_state["pallet_number"] += 1
        
        st.success("Palette gespeichert!")
        st.rerun()

# === 8. Historie ===
st.markdown("---")
st.subheader("📋 Gespeicherte Paletten")

if not st.session_state["pallet_history"]:
    st.caption("Noch keine Paletten abgeschlossen.")
else:
    grand_total = 0.0
    
    # Rückwärts iterieren, damit die neueste oben steht
    for record in reversed(st.session_state["pallet_history"]):
        p_id = record["id"]
        p_items = record["items"]
        p_total = record["total_price"]
        grand_total += p_total
        
        with st.expander(f"📦 Palette #{p_id} (Summe: {p_total:.2f} €)"):
            for sku, q in p_items.items():
                name = product_to_name.get(sku, "Unknown")
                price_single = product_to_price.get(sku, 0)
                st.write(f"- {q}x {name} ({sku}) à {price_single:.2f} €")
            
            st.write(f"**Total: {p_total:.2f} €**")

    st.markdown(f"### Gesamtwert aller Aufträge: {grand_total:.2f} €")
