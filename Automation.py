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
        width: 100%;
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

# === 2. Daten laden ===
EXCEL_PFAD = "Expert Automation.xlsx"

@st.cache_data
def lade_daten(datei_pfad):
    try:
        df = pd.read_excel(datei_pfad, sheet_name="Models")
    except Exception:
        data = {
            "Product code": ["SKU-01", "SKU-02"],
            "Category code": ["A", "B"],
            "Product name": ["Produkt A", "Produkt B"],
            "Product price": [100.0, 200.0]
        }
        df = pd.DataFrame(data)
    
    p_zu_kat = dict(zip(df["Product code"], df["Category code"]))
    p_zu_name = dict(zip(df["Product code"], df["Product name"]))
    p_zu_preis = dict(zip(df["Product code"], df["Product price"]))
    return p_zu_kat, p_zu_name, p_zu_preis, list(p_zu_kat.keys())

produkt_zu_kategorie, produkt_zu_name, produkt_zu_preis, ALLE_PRODUKTE = lade_daten(EXCEL_PFAD)

# === 3. Optimierte Logik (修复 3 台报错的问题) ===
PALLET_REGELN = [
    {"K1": 1}, {"K2": 2}, {"KB": 2}, {"B": 6}, {"K6": 24}, {"K8": 6}, {"S": 4}, {"A": 4},
    {"T4": 4}, {"T2": 2}, {"8888": 2}, {"A": 3, "S": 1}, {"A": 2, "S": 2}, {"A": 1, "S": 3},
    {"A": 2, "B": 2, "K6": 2}, {"A": 1, "S": 1, "B": 2, "K6": 2}, {"S": 2, "B": 2, "K6": 2},
    {"A": 3, "B": 1}, {"A": 2, "S": 1, "B": 1}, {"A": 1, "S": 2, "B": 1}, {"S": 3, "B": 1},
    {"KB": 1, "B": 1, "A": 1, "K6": 1}, {"KB": 1, "B": 1, "S": 1, "K6": 1}, {"A": 2, "K8": 2},
]

def pruefe_menge_erlaubt(kategorie, neue_gesamtmenge):
    """
    检查特定分类的总数是否超过了该分类在所有规则中的最大允许值。
    """
    max_erlaubt = max([r.get(kategorie, 0) for r in PALETTEN_REGELN])
    return neue_gesamtmenge <= max_erlaubt

# === 4. Session State ===
if "palette_nr" not in st.session_state: st.session_state["palette_nr"] = 1
if "waren_auf_palette" not in st.session_state: st.session_state["waren_auf_palette"] = {}
if "verlauf" not in st.session_state: st.session_state["verlauf"] = []

# === 5. Header ===
def get_base64(bin_file):
    with open(bin_file, 'rb') as f: return base64.b64encode(f.read()).decode()

try:
    logo_html = f'<img src="data:image/png;base64,{get_base64("Logo 2.png")}" width="250">'
except:
    logo_html = '<div style="font-size:24px; font-weight:bold;">[LOGO]</div>'

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
    st.subheader(f" Aktuelle Palette #{st.session_state['palette_nr']}")
    
    # 过滤掉已经达到上限的产品
    moegliche_produkte = [
        p for p in ALLE_PRODUKTE 
        if pruefe_menge_erlaubt(produkt_zu_kategorie[p], aktuelle_counts[produkt_zu_kategorie[p]] + 1)
    ]

    if not moegliche_produkte:
        st.success("Die Palette ist voll.")
        gewaehlte_sku = None
    else:
        gewaehlte_sku = st.selectbox("Produkt wählen", options=moegliche_produkte, 
                                     format_func=lambda x: f"{x} – {produkt_zu_name.get(x, '')}")
        menge = st.number_input("Menge", min_value=1, max_value=50, value=1)

        # 实时校验输入数量
        if gewaehlte_sku:
            kat = produkt_zu_kategorie[gewaehlte_sku]
            menge_erlaubt = pruefe_menge_erlaubt(kat, aktuelle_counts[kat] + menge)
        else:
            menge_erlaubt = False

        if not menge_erlaubt:
            st.error(f"❌ Limit überschritten! Maximal {max([r.get(kat, 0) for r in PALETTEN_REGELN])} Einheiten erlaubt.")

    st.write("") 

    # --- 按钮布局调整 ---
    # 使用 4 列：Hinzufügen | Leeren | (Gap) | Speichern
    b_col1, b_col2, b_gap, b_col3 = st.columns([1, 1, 0.2, 1])
    
    with b_col1:
        add_ok = gewaehlte_sku is not None and menge_erlaubt
        if st.button("➕ Hinzufügen", type="primary", use_container_width=True, disabled=not add_ok):
            st.session_state["waren_auf_palette"][gewaehlte_sku] = st.session_state["waren_auf_palette"].get(gewaehlte_sku, 0) + menge
            st.rerun()
            
    with b_col2:
        if st.button("🗑️ Leeren", use_container_width=True):
            st.session_state["waren_auf_palette"] = {}
            st.rerun()

    # b_gap 留空，起到距离效果

    with b_col3:
        hat_inhalt = len(st.session_state["waren_auf_palette"]) > 0
        if st.button("💾 Speichern", use_container_width=True, disabled=not hat_inhalt):
            preis = sum(produkt_zu_preis.get(p, 0) * q for p, q in st.session_state["waren_auf_palette"].items())
            st.session_state["verlauf"].append({
                "id": st.session_state["palette_nr"], 
                "items": st.session_state["waren_auf_palette"].copy(), 
                "total": preis
            })
            st.session_state["waren_auf_palette"] = {}
            st.session_state["palette_nr"] += 1
            st.rerun()

with col2:
    st.subheader(" Ladungsübersicht")
    if st.session_state["waren_auf_palette"]:
        df_list = [{"SKU": p, "Name": produkt_zu_name.get(p), "Menge": q, 
                    "Summe": f"{produkt_zu_preis.get(p, 0) * q:,.2f} €"} 
                   for p, q in st.session_state["waren_auf_palette"].items()]
        st.table(pd.DataFrame(df_list))
    else:
        st.info("Palette ist leer.")

# === 7. Historie ===
st.divider()
st.subheader(" Palettenübersicht")
for e in reversed(st.session_state["verlauf"]):
    with st.container(border=True):
        c1, c2 = st.columns(2)
        c1.write(f"**Palette #{e['id']}**")
        c2.markdown(f"<p style='text-align:right;'><b>{e['total']:,.2f} €</b></p>", unsafe_allow_html=True)
        h_df = [{"Produkt": produkt_zu_name.get(s), "Menge": q} for s, q in e['items'].items()]
        st.dataframe(pd.DataFrame(h_df), use_container_width=True, hide_index=True)
