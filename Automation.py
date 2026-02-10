import streamlit as st
import pandas as pd
from collections import Counter
import base64

# === 1. Konfiguration & Styling (白色简约风格) ===
st.set_page_config(page_title="Paletten-Assistent PRO", page_icon="📦", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; }
    
    /* 按钮基础样式 */
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

    /* 重点按钮（Hinzufügen）样式 */
    div[data-testid="stBaseButton-primary"] {
        font-weight: bold !important;
        border: 2px solid #333333 !important;
    }
    </style>
""", unsafe_allow_html=True)

# === 2. Daten laden (从 Excel 加载数据) ===
EXCEL_PFAD = "Expert Automation.xlsx"

@st.cache_data
def lade_daten(datei_pfad):
    try:
        df = pd.read_excel(datei_pfad, sheet_name="Models")
    except Exception:
        # 备用数据（如果文件丢失）
        data = {
            "Product code": ["SKU-01", "SKU-02"],
            "Category code": ["A", "B"],
            "Product name": ["Beispiel Produkt A", "Beispiel Produkt B"],
            "Product price": [100.0, 200.0]
        }
        df = pd.DataFrame(data)
    
    p_zu_kat = dict(zip(df["Product code"], df["Category code"]))
    p_zu_name = dict(zip(df["Product code"], df["Product name"]))
    p_zu_preis = dict(zip(df["Product code"], df["Product price"]))
    alle_produkte = list(p_zu_kat.keys())
    return p_zu_kat, p_zu_name, p_zu_preis, alle_produkte

produkt_zu_kategorie, produkt_zu_name, produkt_zu_preis, ALLE_PRODUKTE = lade_daten(EXCEL_PFAD)

# === 3. Paletten-Regeln (校验逻辑) ===
PALETTEN_REGELN = [
    {"K1": 1}, {"K2": 2}, {"KB": 2}, {"B": 6}, {"K6": 24}, {"K8": 6}, {"S": 4}, {"A": 4}
]

def pruefe_regeln(aktuelle_mengen):
    """
    检查当前的分类组合是否符合规则。
    逻辑：只要有一种规则能容纳当前所有分类的数量，就返回 True。
    """
    if not aktuelle_mengen:
        return True
    for regel in PALETTEN_REGELN:
        passt = True
        for kat, menge in aktuelle_mengen.items():
            if menge > regel.get(kat, 0):
                passt = False
                break
        if passt:
            return True
    return False

# === 4. Session State (状态管理) ===
if "palette_nr" not in st.session_state: st.session_state["palette_nr"] = 1
if "waren_auf_palette" not in st.session_state: st.session_state["waren_auf_palette"] = {}
if "verlauf" not in st.session_state: st.session_state["verlauf"] = []

# === 5. Header (Logo 与标题水平对齐) ===
def get_base64(bin_file):
    with open(bin_file, 'rb') as f:
        return base64.b64encode(f.read()).decode()

try:
    logo_base64 = get_base64("Logo 2.png")
    logo_html = f'<img src="data:image/png;base64,{logo_base64}" width="250">'
except:
    logo_html = '<div style="font-size:24px; font-weight:bold;">[LOGO]</div>'

st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 30px; margin-bottom: 20px;">
        <div>{logo_html}</div>
        <div style="display: flex; flex-direction: column; justify-content: center;">
            <h1 style="margin: 0; padding: 0; line-height: 1.1; font-size: 40px;">Paletten-Management</h1>
            <p style="margin: 0; padding: 0; font-size: 18px; color: #666666;">Play with the number ones</p>
        </div>
    </div>
""", unsafe_allow_html=True)
st.divider()

# === 6. Haupt-UI (主界面) ===
# 计算当前已有的分类数量
aktuelle_counts = Counter()
for p, q in st.session_state["waren_auf_palette"].items():
    aktuelle_counts[produkt_zu_kategorie[p]] += q

# 找出至少还能再加 1 个的所有产品
moegliche_produkte = [
    p for p in ALLE_PRODUKTE 
    if pruefe_regeln({**aktuelle_counts, produkt_zu_kategorie[p]: aktuelle_counts[produkt_zu_kategorie[p]] + 1})
]

col1, col2 = st.columns([2, 3], gap="large")

with col1:
    st.subheader(f"📍 Aktuelle Palette #{st.session_state['palette_nr']}")
    
    with st.container():
        if not moegliche_produkte:
            st.success("Die Palette ist voll ausgelastet.")
            gewaehlte_sku = None
        else:
            gewaehlte_sku = st.selectbox(
                "Produkt wählen", 
                options=moegliche_produkte, 
                format_func=lambda x: f"{x} – {produkt_zu_name.get(x, '')}"
            )
            menge = st.number_input("Menge", min_value=1, max_value=50, value=1, step=1)
            
            # --- 核心修复：根据当前输入的 Menge 进行校验 ---
            if gewaehlte_sku:
                test_counts = aktuelle_counts.copy()
                kategorie = produkt_zu_kategorie.get(gewaehlte_sku)
                test_counts[kategorie] += menge
                menge_erlaubt = pruefe_regeln(test_counts)
            else:
                menge_erlaubt = False

            if not menge_erlaubt and gewaehlte_sku:
                st.error(f"❌ {menge} Einheiten überschreiten das Limit!")

        st.write("") # 间距

        # --- 按钮行：对齐 Hinzufügen, Speichern, Leeren ---
        btn_col1, btn_col2, btn_col3 = st.columns(3)
        
        with btn_col1:
            # 只有当数量合法时才允许点击
            add_aktiv = gewaehlte_sku is not None and menge_erlaubt
            if st.button("➕ Hinzufügen", type="primary", use_container_width=True, disabled=not add_aktiv):
                st.session_state["waren_auf_palette"][gewaehlte_sku] = st.session_state["waren_auf_palette"].get(gewaehlte_sku, 0) + menge
                st.rerun()
        
        with btn_col2:
            palette_hat_inhalt = len(st.session_state["waren_auf_palette"]) > 0
            if st.button("💾 Speichern", use_container_width=True, disabled=not palette_hat_inhalt):
                gesamt_preis = sum(produkt_zu_preis.get(p, 0) * q for p, q in st.session_state["waren_auf_palette"].items())
                st.session_state["verlauf"].append({
                    "id": st.session_state["palette_nr"], 
                    "items": st.session_state["waren_auf_palette"].copy(), 
                    "total": gesamt_preis
                })
                st.session_state["waren_auf_palette"] = {}
                st.session_state["palette_nr"] += 1
                st.rerun()

        with btn_col3:
            if st.button("🗑️ Leeren", use_container_width=True):
                st.session_state["waren_auf_palette"] = {}
                st.rerun()

with col2:
    st.subheader("📝 Ladungsübersicht")
    if st.session_state["waren_auf_palette"]:
        tabelle_daten = []
        for p, q in st.session_state["waren_auf_palette"].items():
            tabelle_daten.append({
                "SKU": p,
                "Name": produkt_zu_name.get(p, ""),
                "Menge": q,
                "Gesamt": f"{produkt_zu_preis.get(p, 0) * q:,.2f} €"
            })
        st.table(pd.DataFrame(tabelle_daten))
        total_summe = sum(produkt_zu_preis.get(p, 0) * q for p, q in st.session_state["waren_auf_palette"].items())
        st.markdown(f"### **Gesamtwert: {total_summe:,.2f} €**")
    else:
        st.info("Die Palette ist leer.")

# === 7. Historie ===
st.divider()
st.subheader("📋 Historie abgeschlossener Paletten")
if not st.session_state["verlauf"]:
    st.write("Keine Einträge vorhanden.")
else:
    for eintrag in reversed(st.session_state["verlauf"]):
        with st.container(border=True):
            h_col1, h_col2 = st.columns(2)
            h_col1.markdown(f"#### 📦 Palette #{eintrag['id']}")
            h_col2.markdown(f"<p style='text-align:right; font-weight:bold; color:#1a4a73;'>{eintrag['total']:,.2f} €</p>", unsafe_allow_html=True)
            
            liste = [{"Produkt": produkt_zu_name.get(sku), "Menge": f"{q} Stk."} for sku, q in eintrag["items"].items()]
            st.dataframe(pd.DataFrame(liste), use_container_width=True, hide_index=True)
