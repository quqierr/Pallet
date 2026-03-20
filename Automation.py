import streamlit as st
import pandas as pd
from collections import Counter
import base64

# === 1. Konfiguration & Styling ===
st.set_page_config(page_title="Paletten-Assistent PRO", page_icon="📦", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; }
    div.stButton > button {
        background-color: #FFFFFF !important;
        color: #333333 !important;
        border: 1px solid #CCCCCC !important;
        border-radius: 4px !important;
        height: 3em;
        width: 100% !important;
        transition: all 0.2s;
    }
    div.stButton > button:hover {
        border-color: #000000 !important;
        background-color: #F9F9F9 !important;
    }
    div[data-testid="stBaseButton-primary"] {
        font-weight: bold !important;
        border: 2px solid #333333 !important;
    }
    </style>
""", unsafe_allow_html=True)

# === 2. Daten-Logik ===
@st.cache_data
def lade_daten(datei_pfad_main, datei_pfad_stock):
    try:
        # 1. Hauptdaten laden
        df = pd.read_excel(datei_pfad_main, sheet_name="Models")
        df["Product code"] = df["Product code"].astype(str).str.strip().str.upper()

        # 2. Bestandsdaten laden
        stock_map = {}
        try:
            df_stock = pd.read_excel(datei_pfad_stock, sheet_name="Lagerabgleich", header=5)
            df_stock = df_stock.iloc[:, [0, 7]]
            df_stock.columns = ["Material", "Stock"]
            df_stock = df_stock.dropna(subset=["Material"])
            
            df_stock["Material_Clean"] = df_stock["Material"].apply(lambda x: str(x).strip().upper().split('.')[0])
            df_stock["Stock_Clean"] = pd.to_numeric(df_stock["Stock"], errors="coerce").fillna(0)
            stock_map = dict(zip(df_stock["Material_Clean"], df_stock["Stock_Clean"]))
        except Exception as e:
            st.warning(f"Lagerliste konnte nicht voll geladen werden: {e}")

        # 3. Mappings erstellen
        df["Stock"] = df["Product code"].map(stock_map).fillna(0)
        df["Verfügbarkeit"] = df["Stock"].apply(lambda x: "Verfügbar" if x > 0 else "Nicht verfügbar")

        return {
            "p_zu_kat": dict(zip(df["Product code"], df["Category code"])),
            "p_zu_sub": dict(zip(df["Product code"], df["Sub-Categories"])),
            "p_zu_name": dict(zip(df["Product code"], df["Product name"])),
            "p_zu_preis": dict(zip(df["Product code"], df["Product price"])),
            "p_zu_stock": dict(zip(df["Product code"], df["Stock"])),
            "p_zu_status": dict(zip(df["Product code"], df["Verfügbarkeit"])),
            "alle_skus": df["Product code"].tolist()
        }
    except Exception as e:
        st.error(f"Kritischer Fehler: {e}")
        return None

# Daten initialisieren
data = lade_daten("Expert Automation Final v02.xlsx", "Lagerliste SAP 20260320.xlsx")

if data:
    p_zu_kat = data["p_zu_kat"]
    p_zu_sub = data["p_zu_sub"]
    p_zu_name = data["p_zu_name"]
    p_zu_preis = data["p_zu_preis"]
    p_zu_status = data["p_zu_status"]
    ALLE_PRODUKTE = data["alle_skus"]
else:
    st.stop()

# === 3. Palettenregeln ===
PALETTEN_REGELN = [
    {"K1": 1}, {"K2": 2}, {"KB": 2}, {"B": 6}, {"K6": 24}, {"K8": 6}, {"S": 4}, {"A": 4},
    {"T4": 4}, {"T2": 2}, {"8888": 2}, {"A": 3, "S": 1}, {"A": 2, "S": 2}, {"A": 1, "S": 3},
    {"A": 2, "B": 2, "K6": 2}, {"A": 1, "S": 1, "B": 2, "K6": 2}, {"S": 2, "B": 2, "K6": 2},
    {"A": 3, "B": 1}, {"A": 2, "S": 1, "B": 1}, {"A": 1, "S": 2, "B": 1}, {"S": 3, "B": 1},
    {"KB": 1, "B": 1, "A": 1, "K6": 1}, {"KB": 1, "B": 1, "S": 1, "K6": 1}, {"A": 2, "K8": 2},
]

def check_palette_valid(test_counts):
    if not test_counts: return True
    # Entferne Kategorien mit Menge 0 für den Vergleich
    test_counts = {k: v for k, v in test_counts.items() if v > 0}
    
    for regel in PALETTEN_REGELN:
        ist_regel_erfuellt = True
        # Eine Regel passt nur, wenn alle Kategorien in test_counts in der Regel sind
        # UND die Menge kleiner oder gleich der Regelvorgabe ist.
        for kat, menge in test_counts.items():
            if menge > regel.get(kat, 0):
                ist_regel_erfuellt = False
                break
        if ist_regel_erfuellt: return True
    return False

# === 4. Session State ===
if "palette_nr" not in st.session_state: st.session_state["palette_nr"] = 1
if "waren_auf_palette" not in st.session_state: st.session_state["waren_auf_palette"] = {}
if "verlauf" not in st.session_state: st.session_state["verlauf"] = []

# === 5. Header ===
def get_base64(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    except: return None

logo_base64 = get_base64("Logo Final.png")
logo_html = f'<img src="data:image/png;base64,{logo_base64}" width="270">' if logo_base64 else '<h1>📦</h1>'

st.markdown(f"""
<div style="display: flex; align-items: center; gap: 30px; margin-bottom: 20px;">
    <div>{logo_html}</div>
    <div>
        <h1 style="margin: 0; font-size: 40px;">Paletten-Management</h1>
        <p style="margin: 0; font-size: 18px; color: #666666;">Play with the number ones</p>
    </div>
</div>
""", unsafe_allow_html=True)
st.divider()

# === 6. Haupt-Layout ===
aktuelle_counts = Counter()
for p, q in st.session_state["waren_auf_palette"].items():
    aktuelle_counts[p_zu_kat[p]] += q

col1, col2 = st.columns([2, 3], gap="large")

with col1:
    st.subheader(f"Aktuelle Palette #{st.session_state['palette_nr']}")

    # Filtern nach möglichen Produkten (Validierung gegen Regeln)
    moegliche_produkte = [
        p for p in ALLE_PRODUKTE
        if check_palette_valid({**aktuelle_counts, p_zu_kat[p]: aktuelle_counts[p_zu_kat[p]] + 1})
    ]

    if not moegliche_produkte:
        st.success("✅ **Palette ist nach Regeln optimal ausgelastet!**")
        gewaehlte_sku = None
    else:
        gewaehlte_sku = st.selectbox(
            "Produkt wählen",
            options=moegliche_produkte,
            format_func=lambda x: f"[{p_zu_sub.get(x, '')}] {x} – {p_zu_name.get(x, '')}"
        )
        menge = st.number_input("Menge", min_value=1, max_value=50, value=1)
        
        menge_erlaubt = False
        if gewaehlte_sku:
            if p_zu_status.get(gewaehlte_sku) == "Nicht verfügbar":
                st.error("❌ Produkt aktuell nicht verfügbar!")
            else:
                test_counts = aktuelle_counts.copy()
                test_counts[p_zu_kat[gewaehlte_sku]] += menge
                menge_erlaubt = check_palette_valid(test_counts)
                if not menge_erlaubt:
                    st.error("❌ Diese Menge sprengt die Palettenregeln!")

    # Buttons
    b_col1, b_col2, b_col3 = st.columns(3)
    with b_col1:
        if st.button("➕ Hinzufügen", type="primary", disabled=not (gewaehlte_sku and 'menge_erlaubt' in locals() and menge_erlaubt)):
            st.session_state["waren_auf_palette"][gewaehlte_sku] = st.session_state["waren_auf_palette"].get(gewaehlte_sku, 0) + menge
            st.rerun()
    with b_col2:
        if st.button("🗑️ Leeren"):
            st.session_state["waren_auf_palette"] = {}
            st.rerun()
    with b_col3:
        if st.button("💾 Speichern", disabled=not st.session_state["waren_auf_palette"]):
            preis = sum(p_zu_preis.get(p, 0) * q for p, q in st.session_state["waren_auf_palette"].items())
            if sum(st.session_state["waren_auf_palette"].values()) == 1:
                sku = list(st.session_state["waren_auf_palette"].keys())[0]
                if p_zu_kat.get(sku) != "K1": preis += 81
            
            st.session_state["verlauf"].append({
                "id": st.session_state["palette_nr"],
                "items": st.session_state["waren_auf_palette"].copy(),
                "total": preis
            })
            st.session_state["waren_auf_palette"] = {}
            st.session_state["palette_nr"] += 1
            st.rerun()

with col2:
    st.subheader("Ladungsübersicht")
    if st.session_state["waren_auf_palette"]:
        items_data = []
        for p, q in st.session_state["waren_auf_palette"].items():
            items_data.append({
                "SKU": p,
                "Sub-Kategorie": p_zu_sub.get(p, ""),
                "Name": p_zu_name.get(p, ""),
                "Menge": f"{q} Stk.",
                "Preis": f"{p_zu_preis.get(p, 0) * q:,.2f} €"
            })
        st.table(pd.DataFrame(items_data))
        
        total_summe = sum(p_zu_preis.get(p, 0) * q for p, q in st.session_state["waren_auf_palette"].items())
        if sum(st.session_state["waren_auf_palette"].values()) == 1:
            sku = list(st.session_state["waren_auf_palette"].keys())[0]
            if p_zu_kat.get(sku) != "K1":
                total_summe += 81
                st.info("Hinweis: +81€ Einzelstück-Versand")

        st.markdown(f"<h2 style='text-align:right;'>{total_summe:,.2f} €</h2>", unsafe_allow_html=True)
    else:
        st.info("Die Palette ist leer.")

# === 7. Historie ===
if st.session_state["verlauf"]:
    st.divider()
    st.subheader("Gespeicherte Paletten")
    for e in reversed(st.session_state["verlauf"]):
        with st.expander(f"Palette #{e['id']} - {e['total']:,.2f} €"):
            h_df = [{"SKU": s, "Name": p_zu_name.get(s), "Menge": q} for s, q in e['items'].items()]
            st.dataframe(pd.DataFrame(h_df), use_container_width=True)

    gesamt_aller_paletten = sum(e["total"] for e in st.session_state["verlauf"])
    st.markdown(f"""
    <div style="text-align: right; padding: 20px; background-color: #F9F9F9; border-radius: 8px;">
        <span style="font-size: 18px;">GESAMTSUMME:</span><br>
        <span style="font-size: 32px; font-weight: bold; color: #0C5CA8;">{gesamt_aller_paletten:,.2f} €</span>
    </div>
    """, unsafe_allow_html=True)
