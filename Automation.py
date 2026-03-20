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
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        padding-left: 10px;
        padding-right: 10px;
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


# === 2. Daten laden ===
EXCEL_PFAD_MAIN = "Expert Automation Final v02.xlsx"
EXCEL_PFAD_STOCK = "Lagerliste SAP 20260320.xlsx"

@st.cache_data(ttl=60)
def lade_daten(datei_pfad_main, datei_pfad_stock):
    try:
        # === Hauptdaten (Produktkatalog) ===
        df = pd.read_excel(datei_pfad_main, sheet_name="Models")
        df["Product price"] = pd.to_numeric(df["Product price"], errors="coerce")

        # === Bestandsdaten (SAP Export) ===
        try:
            df_stock = pd.read_excel(datei_pfad_stock)
            
            # 1. Spalte für Product Code identifizieren (jetzt "Material")
            code_col = "Material" if "Material" in df_stock.columns else "Product code"
            
            # 2. Spalte für Bestand identifizieren
            if "Available Stock 1C12" in df_stock.columns:
                stock_col = "Available Stock 1C12"
            elif "available Stock" in df_stock.columns:
                stock_col = "available Stock"
            elif "M" in df_stock.columns:
                stock_col = "M"
            else:
                stock_col = None

            if stock_col and code_col in df_stock.columns:
                df_stock["Stock_Clean"] = pd.to_numeric(df_stock[stock_col], errors="coerce").fillna(0)
                # Mapping erstellen: Material-Nummer -> Bestandsmenge
                stock_map = dict(zip(df_stock[code_col], df_stock["Stock_Clean"]))
            else:
                st.warning("Spalte 'Material' oder Bestandsspalte nicht gefunden.")
                stock_map = {}

        except Exception as e:
            st.warning(f"Lagerliste konnte nicht verarbeitet werden: {e}")
            stock_map = {}

        # === Bestände an Hauptdaten mappen ===
        # Wir nutzen die Spalte "Product code" aus der Main-Datei, um den Bestand aus der Map zu ziehen
        df["Stock"] = df["Product code"].map(stock_map).fillna(0)

        # Verfügbarkeits-Logik
        df["Verfügbarkeit"] = df["Stock"].apply(lambda x: "Verfügbar" if x > 0 else "Nicht verfügbar")

        # Mappings für die App-Logik
        p_zu_kat = dict(zip(df["Product code"], df["Category code"]))
        p_zu_sub = dict(zip(df["Product code"], df["Sub-Categories"]))
        p_zu_name = dict(zip(df["Product code"], df["Product name"]))
        p_zu_preis = dict(zip(df["Product code"], df["Product price"]))
        p_zu_stock = dict(zip(df["Product code"], df["Stock"]))
        p_zu_status = dict(zip(df["Product code"], df["Verfügbarkeit"]))

        return p_zu_kat, p_zu_sub, p_zu_name, p_zu_preis, p_zu_stock, p_zu_status, list(p_zu_kat.keys())

    except Exception as e:
        st.error(f"Kritischer Fehler beim Laden der Hauptdaten: {e}")
        return {}, {}, {}, {}, {}, {}, []

    # === 合并库存 ===
    df["Stock"] = df["Product code"].map(stock_map).fillna(0)

    # === 库存状态 ===
    df["Verfügbarkeit"] = df["Stock"].apply(lambda x: "Verfügbar" if x > 10 else "Nicht verfügbar")

    # === 映射 ===
    p_zu_kat = dict(zip(df["Product code"], df["Category code"]))
    p_zu_sub = dict(zip(df["Product code"], df["Sub-Categories"]))
    p_zu_name = dict(zip(df["Product code"], df["Product name"]))
    p_zu_preis = dict(zip(df["Product code"], df["Product price"]))
    p_zu_stock = dict(zip(df["Product code"], df["Stock"]))
    p_zu_status = dict(zip(df["Product code"], df["Verfügbarkeit"]))

    return p_zu_kat, p_zu_sub, p_zu_name, p_zu_preis, p_zu_stock, p_zu_status, list(p_zu_kat.keys())

# 加载数据时增加子类别变量
produkt_zu_kategorie, produkt_zu_sub, produkt_zu_name, produkt_zu_preis, produkt_zu_stock, produkt_zu_status, ALLE_PRODUKTE = lade_daten(EXCEL_PFAD_MAIN, EXCEL_PFAD_STOCK)

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
    for regel in PALETTEN_REGELN:
        ist_regel_erfuellt = True
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
logo_html = f'<img src="data:image/png;base64,{logo_base64}" width="270">' if logo_base64 else '<div style="font-size:24px; font-weight:bold;">[LOGO]</div>'

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
    aktuelle_counts[produkt_zu_kategorie[p]] += q

col1, col2 = st.columns([2, 3], gap="large")

with col1:
    st.subheader(f"Aktuelle Palette #{st.session_state['palette_nr']}")

    moegliche_produkte = [
        p for p in ALLE_PRODUKTE
        if check_palette_valid({**aktuelle_counts, produkt_zu_kategorie[p]: aktuelle_counts[produkt_zu_kategorie[p]] + 1})
    ]

    if not moegliche_produkte:
        st.success("✅ **Palette ist optimal ausgelastet!**")
        gewaehlte_sku = None
        menge_erlaubt = False
    else:
        gewaehlte_sku = st.selectbox(
            "Produkt wählen",
            options=moegliche_produkte,
            format_func=lambda x: f"[{produkt_zu_sub.get(x, '')}] {x} – {produkt_zu_name.get(x, '')}"
        )
        menge = st.number_input("Menge", min_value=1, max_value=50, value=1)
        
        # 【修正的逻辑区域：正确验证数量是否被允许】
        menge_erlaubt = False
        if gewaehlte_sku:
            if produkt_zu_status.get(gewaehlte_sku) == "Nicht verfügbar":
                st.error("❌ Produkt aktuell nicht verfügbar!")
            else:
                test_counts = aktuelle_counts.copy()
                test_counts[produkt_zu_kategorie[gewaehlte_sku]] += menge
                menge_erlaubt = check_palette_valid(test_counts)
                if not menge_erlaubt:
                    st.error("❌ Kombination nicht erlaubt oder Limit überschritten!")

    b_col1, b_col2, b_col3 = st.columns([1, 1, 1], gap="small")
    with b_col1:
        if st.button("➕ Hinzufügen", type="primary", use_container_width=True, disabled=not (gewaehlte_sku and menge_erlaubt)):
            st.session_state["waren_auf_palette"][gewaehlte_sku] = st.session_state["waren_auf_palette"].get(gewaehlte_sku, 0) + menge
            st.rerun()
    with b_col2:
        if st.button("🗑️ Leeren", use_container_width=True):
            st.session_state["waren_auf_palette"] = {}
            st.rerun()
    with b_col3:
        if st.button("💾 Speichern", use_container_width=True, disabled=not st.session_state["waren_auf_palette"]):
            preis = sum(produkt_zu_preis.get(p, 0) * q for p, q in st.session_state["waren_auf_palette"].items())
            total_anzahl = sum(st.session_state["waren_auf_palette"].values())
            if total_anzahl == 1:
                sku = list(st.session_state["waren_auf_palette"].keys())[0]
                if produkt_zu_kategorie.get(sku) != "K1": preis += 81
            
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
        df_list = []
        for p, q in st.session_state["waren_auf_palette"].items():
            df_list.append({
                "SKU": p,
                "Sub-Kategorie": produkt_zu_sub.get(p, ""),
                "Name": produkt_zu_name.get(p, ""),
                "Menge": f"{q} Stk.",
                "Gesamtpreis": f"{produkt_zu_preis.get(p, 0) * q:,.2f} €"
            })
        st.dataframe(pd.DataFrame(df_list), use_container_width=True, hide_index=True)
        
        total_summe = sum(produkt_zu_preis.get(p, 0) * q for p, q in st.session_state["waren_auf_palette"].items())
        if sum(st.session_state["waren_auf_palette"].values()) == 1:
            sku = list(st.session_state["waren_auf_palette"].keys())[0]
            if produkt_zu_kategorie.get(sku) != "K1":
                total_summe += 81
                st.info("Versandkosten für Einzelstück-Lieferung: 81,00 €")

        st.markdown(f"""
        <div style="text-align: right; padding: 10px; border-top: 2px solid #EEEEEE;">
        <span style="font-size: 16px; color: #666666;">Gesamtwert der aktuellen Palette:</span><br>
        <span style="font-size: 24px; font-weight: bold; color: #0C5CA8;">{total_summe:,.2f} €</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("Die Palette ist leer.")

# === 7. Historie ===
st.divider()
st.subheader("Palettenübersicht")
for e in reversed(st.session_state["verlauf"]):
    with st.container(border=True):
        c1, c2 = st.columns(2)
        c1.write(f"**Palette #{e['id']}**")
        c2.markdown(f"<p style='text-align:right;'><b>{e['total']:,.2f} €</b></p>", unsafe_allow_html=True)
        h_df = [{
            "Sub-Kategorie": produkt_zu_sub.get(s), 
            "Produkt": produkt_zu_name.get(s), 
            "Menge": q
        } for s, q in e['items'].items()]
        st.dataframe(pd.DataFrame(h_df), use_container_width=True, hide_index=True)

st.write("")
gesamt_aller_paletten = sum(e["total"] for e in st.session_state["verlauf"])
st.markdown(f"""
<div style="text-align: right; padding: 20px; border-top: 3px double #EEEEEE; background-color: #F9F9F9; border-radius: 8px;">
<span style="font-size: 18px; color: #333333;">GESAMTSUMME ALLER PALETTEN:</span><br>
<span style="font-size: 32px; font-weight: bold; color: #0C5CA8;">{gesamt_aller_paletten:,.2f} €</span>
</div>
<div style="text-align: center; font-size: 13px; color: #666666; margin-top: 30px;">
Preise Stand 16.02.2026. Alle Preise sind freibleibend und unverbindlich. Änderungen und Irrtümer vorbehalten.
</div>
""", unsafe_allow_html=True)
