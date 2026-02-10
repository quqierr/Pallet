import streamlit as st
import pandas as pd
from collections import Counter

col1, col2 = st.columns([1, 6])

with col1:
    st.image("Logo.png", width=200)

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

st.set_page_config(page_title="Pallet Assistant", page_icon="📦")
st.title("📦 Paletten-Assistent")
st.subheader("Produkte auf der Palette")

# === Excel Sheet ===
EXCEL_PATH = "data.xlsx"

# === Caching Data for Performance ===
@st.cache_data
def load_data(file_path):
    models = pd.read_excel(file_path, sheet_name="Models")
    p_to_cat = dict(zip(models["Product code"], models["Category code"]))
    p_to_name = dict(zip(models["Product code"], models["Product name"]))
    p_to_price = dict(zip(models["Product code"], models["Product price"]))
    p_to_cat_fullname = dict(zip(models["Product code"], models["Sub-Categories"]))
    all_prods = list(p_to_cat.keys())
    return p_to_cat, p_to_name, p_to_price, p_to_cat_fullname, all_prods

product_to_category, product_to_name, product_to_price, product_to_cat_fullname, ALL_PRODUCTS = load_data(EXCEL_PATH)


# === Rule Definition ===
PALLET_RULES = [
    {"K1": 1},
    {"K2": 2},
    {"KB": 2}, 
    {"B": 6},
    {"K6": 24},
    {"K8": 6},
    {"S": 4}, 
    {"A": 4},
    {"T4": 4},
    {"T2": 2},
    {"8888": 2},
    {"A": 3, "S": 1},
    {"A": 2, "S": 2},
    {"A": 1, "S": 3},
    {"A": 2, "B": 2, "K6": 2},
    {"A": 1, "S": 1, "B": 2, "K6": 2},
    {"S": 2, "B": 2, "K6": 2},
    {"A": 3, "B": 1}, 
    {"A": 2, "S": 1, "B": 1},
    {"A": 1, "S": 2, "B": 1},
    {"S": 3, "B": 1},
    {"KB": 1, "B": 1, "A": 1, "K6": 1},
    {"KB": 1, "B": 1, "S": 1, "K6": 1},
    {"A": 2, "K8": 2},
]

# === Helper Functions ===

def check_rules(cat_counts):
    for rule in PALLET_RULES:
        is_rule_ok = True
        for cat, qty in cat_counts.items():
            if rule.get(cat, 0) < qty:
                is_rule_ok = False
                break
        if is_rule_ok:
            return True
    return False

def get_allowed_products(current_counts):
    allowed = []
    for p in ALL_PRODUCTS:
        cat = product_to_category[p]
        test_counts = current_counts.copy()
        test_counts[cat] = test_counts.get(cat, 0) + 1
        
        if check_rules(test_counts):
            allowed.append(p)
    return allowed

# === User Input & Logic (SKU + Menge) ===

if "pallet_number" not in st.session_state:
    st.session_state["pallet_number"] = 1

if "pallet_items" not in st.session_state:
    st.session_state["pallet_items"] = {}  # {product_code: qty}

st.subheader(f"📦 Produkte auf Palette #{st.session_state['pallet_number']}")

# --- Produkt auswählen ---
selected_sku = st.selectbox(
    "Produkt auswählen",
    options=ALL_PRODUCTS,
    format_func=lambda x: f"{x} – {product_to_name.get(x, 'Unknown')}"
)

qty = st.number_input(
    "Menge",
    min_value=1,
    max_value=50,
    step=1
)

if st.button("➕ Produkt hinzufügen / aktualisieren"):
    st.session_state["pallet_items"][selected_sku] = qty
    st.rerun()

# --- Aktuelle Palette anzeigen ---
if st.session_state["pallet_items"]:
    st.write("### Aktuelle Paletteninhalte")

    for p, q in st.session_state["pallet_items"].items():
        st.write(f"- **{p}** ({product_to_name[p]}) × {q}")

    if st.button("🗑️ Palette leeren"):
        st.session_state["pallet_items"] = {}
        st.rerun()

# === Status Calculation ===
current_counts = Counter()

for p, qty in st.session_state["pallet_items"].items():
    cat = product_to_category[p]
    current_counts[cat] += qty

is_current_valid = check_rules(current_counts)

# 判断还能不能再加 1 件任意 SKU
can_add_more = False
for p in ALL_PRODUCTS:
    test_counts = current_counts.copy()
    test_counts[product_to_category[p]] += 1
    if check_rules(test_counts):
        can_add_more = True
        break

# 价格
total_price = sum(
    product_to_price[p] * qty
    for p, qty in st.session_state["pallet_items"].items()
)

st.write(f"💰 **Gesamtpreis der Palette: € {total_price:.2f}**")

st.subheader("Status")

if not is_current_valid:
    st.error("❌ Palette ist überladen")
    st.caption("Die aktuelle Kombination entspricht keiner zulässigen Palettenregel.")

elif is_current_valid and not can_add_more:
    st.success("✅ Palette ist voll")
    st.caption("Maximale Kapazität erreicht.")

    if st.button("➕ Neue Palette hinzufügen"):
        st.session_state["pallet_items"] = {}
        st.session_state["pallet_number"] += 1
        st.rerun()

else:
    st.info("✅ Palette kann weiter beladen werden")
    
    with st.expander("Show available additions details"):
        
        available_names = sorted(list(set(product_to_cat_fullname[p] for p in allowed_additions)))
        
        st.write(f"**Available Categories to add:**")
        st.write(", ".join(available_names))
        
        st.write("---")
        st.write("**Specific products (Sample):**")
        
        for p in allowed_additions[:60]:
            cat_fullname = product_to_cat_fullname[p]
            p_name = product_to_name[p]
            st.write(f"- {p} ({p_name}) [Category: {cat_fullname}]")
            

            

            
