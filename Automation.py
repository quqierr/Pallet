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
    div.stButton > button {
        background-color: #FFFFFF !important;
        color: #333333 !important;
        border: 1px solid #CCCCCC !important;
        border-radius: 4px !important;
        height: 3em;
        width: 100% !important; /* 让它填满所在的列 */
        transition: all 0.2s;

        /* --- 核心修复：防止图片中那种情况 --- */
        white-space: nowrap;      /* 🛑 DIESER PUNKT IST AM WICHTIGSTEN! Verhindert Textumbruch */
        overflow: hidden;         /* Schneidet überschüssigen Text ab, falls er zu lang ist */
        text-overflow: ellipsis;  /* Fügt "..." hinzu, wenn Text abgeschnitten wird */
        padding-left: 10px;       /* Fügt etwas Padding hinzu, damit der Text nicht am Rand klebt */
        padding-right: 10px;
    }
    div[data-testid="stBaseButton-primary"] {
        font-weight: bold !important;
        border: 2px solid #333333 !important;
    }
    </style>
""", unsafe_allow_html=True)

# === 2. Daten laden ===
EXCEL_PFAD = "Expert Automation Final v02.xlsx"

@st.cache_data
def lade_daten(datei_pfad):

    try:
        df = pd.read_excel(datei_pfad, sheet_name="Models")

        # 确保价格是数字
        df["Product price"] = pd.to_numeric(df["Product price"], errors="coerce")

    except Exception as e:
        st.error(f"Excel读取失败: {e}")

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

# === 3. Palettenregeln ===
PALETTEN_REGELN = [
    {"K1": 1}, {"K2": 2}, {"KB": 2}, {"B": 6}, {"K6": 24}, {"K8": 6}, {"S": 4}, {"A": 4},
    {"T4": 4}, {"T2": 2}, {"8888": 2}, {"A": 3, "S": 1}, {"A": 2, "S": 2}, {"A": 1, "S": 3},
    {"A": 2, "B": 2, "K6": 2}, {"A": 1, "S": 1, "B": 2, "K6": 2}, {"S": 2, "B": 2, "K6": 2},
    {"A": 3, "B": 1}, {"A": 2, "S": 1, "B": 1}, {"A": 1, "S": 2, "B": 1}, {"S": 3, "B": 1},
    {"KB": 1, "B": 1, "A": 1, "K6": 1}, {"KB": 1, "B": 1, "S": 1, "K6": 1}, {"A": 2, "K8": 2},
]

def check_palette_valid(test_counts):
    if not test_counts:
        return True
    for regel in PALETTEN_REGELN:
        ist_regel_erfuellt = True
        for kat, menge in test_counts.items():
            if menge > regel.get(kat, 0):
                ist_regel_erfuellt = False
                break
        if ist_regel_erfuellt:
            return True
    return False

# === 4. Session State ===
if "palette_nr" not in st.session_state: st.session_state["palette_nr"] = 1
if "waren_auf_palette" not in st.session_state: st.session_state["waren_auf_palette"] = {}
if "verlauf" not in st.session_state: st.session_state["verlauf"] = []

# === 5. Header ===
def get_base64(bin_file):
    with open(bin_file, 'rb') as f:
        return base64.b64encode(f.read()).decode()

try:
    logo_html = f'<img src="data:image/png;base64,{get_base64("Logo Final.png")}" width="270">'
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
    st.subheader(f"Aktuelle Palette #{st.session_state['palette_nr']}")

    moegliche_produkte = [
        p for p in ALLE_PRODUKTE
        if check_palette_valid({**aktuelle_counts, produkt_zu_kategorie[p]: aktuelle_counts[produkt_zu_kategorie[p]] + 1})
    ]

    if not moegliche_produkte:
        st.success("✅ **Palette ist optimal ausgelastet!**")
        st.info("Bitte klicken Sie auf „💾 Speichern“, um zu speichern.")
        gewaehlte_sku = None
        menge_erlaubt = False
    else:
        if len(st.session_state["waren_auf_palette"]) > 0:
            st.warning("⚠️ Die Palette ist noch nicht vollständig ausgelastet.")

        gewaehlte_sku = st.selectbox(
            "Produkt wählen",
            options=moegliche_produkte,
            format_func=lambda x: f"{x} – {produkt_zu_name.get(x, '')}"
        )

        menge = st.number_input("Menge", min_value=1, max_value=50, value=1)

        if gewaehlte_sku:
            test_counts = aktuelle_counts.copy()
            kat = produkt_zu_kategorie[gewaehlte_sku]
            test_counts[kat] += menge
            menge_erlaubt = check_palette_valid(test_counts)

            if not menge_erlaubt:
                st.error("❌ Kombination nicht erlaubt oder Limit überschritten!")
        else:
            menge_erlaubt = False

    b_col1, b_col2, b_col3 = st.columns([1, 1, 1], gap="small")

    with b_col1:
        add_ok = gewaehlte_sku is not None and menge_erlaubt
        if st.button("➕ Hinzufügen", type="primary", use_container_width=True, disabled=not add_ok):
            st.session_state["waren_auf_palette"][gewaehlte_sku] = \
                st.session_state["waren_auf_palette"].get(gewaehlte_sku, 0) + menge
            st.rerun()

    with b_col2:
        if st.button("🗑️ Leeren", use_container_width=True):
            st.session_state["waren_auf_palette"] = {}
            st.rerun()

    with b_col3:
        hat_inhalt = len(st.session_state["waren_auf_palette"]) > 0
        if st.button("💾 Speichern", use_container_width=True, disabled=not hat_inhalt):

            preis = sum(
                produkt_zu_preis.get(p, 0) * q
                for p, q in st.session_state["waren_auf_palette"].items()
            )

            # ✅ 运费逻辑
            total_anzahl = sum(st.session_state["waren_auf_palette"].values())
            
            if total_anzahl == 1:
                sku = list(st.session_state["waren_auf_palette"].keys())[0]
                if produkt_zu_kategorie.get(sku) != "K1":
                    preis += 81

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
            einzelpreis = produkt_zu_preis.get(p, 0)
            df_list.append({
                "SKU": str(p),
                "Name": str(produkt_zu_name.get(p, "Unbekannt")),
                "Menge": f"{q} Stk.",
                "Gesamtpreis": f"{einzelpreis * q:,.2f} €"
            })

        df_display = pd.DataFrame(df_list)
        st.dataframe(df_display, use_container_width=True, hide_index=True)

        total_summe = sum(
            produkt_zu_preis.get(p, 0) * q
            for p, q in st.session_state["waren_auf_palette"].items()
        )

        # ✅ 实时运费显示
        total_anzahl = sum(st.session_state["waren_auf_palette"].values())
        
        if total_anzahl == 1:
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
        h_df = [{"Produkt": produkt_zu_name.get(s), "Menge": q} for s, q in e['items'].items()]
        st.dataframe(pd.DataFrame(h_df), use_container_width=True, hide_index=True)

st.write("")
gesamt_aller_paletten = sum(e["total"] for e in st.session_state["verlauf"])

st.markdown(f"""
<div style="text-align: right; padding: 20px; border-top: 3px double #EEEEEE; background-color: #F9F9F9; border-radius: 8px;">
<span style="font-size: 18px; color: #333333;">GESAMTSUMME ALLER PALETTEN:</span><br>
<span style="font-size: 32px; font-weight: bold; color: #0C5CA8;">{gesamt_aller_paletten:,.2f} €</span>
</div>
""", unsafe_allow_html=True)

# ✅ 法律声明
st.markdown("""
<div style="text-align: center; font-size: 13px; color: #666666; margin-top: 30px;">
Preise Stand 16.02.2026. Alle Preise sind freibleibend und unverbindlich.
Änderungen und Irrtümer vorbehalten.
</div>
""", unsafe_allow_html=True)
