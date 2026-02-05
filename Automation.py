import streamlit as st
import pandas as pd
from collections import Counter

st.set_page_config(page_title="Pallet Assistant", page_icon="📦")
st.title("📦 Pallet Assistant")

# === Excel Sheet ===
uploaded_file = st.file_uploader("Bitte Excel-Datei hochladen", type=["xlsx"])

if not uploaded_file:
    st.info("Bitte laden Sie eine Datei hoch, um zu beginnen.")
    st.stop()

# === Caching Data for Performance ===
@st.cache_data
def load_data(file):
    models = pd.read_excel(file, sheet_name="Models")
    p_to_cat = dict(zip(models["Product code"], models["Category code"]))
    p_to_name = dict(zip(models["Product code"], models["Product name"]))
    p_to_price = dict(zip(models["Product code"], models["Product price"]))
    p_to_cat_fullname = dict(zip(models["Product code"], models["Sub-Categories"]))
    all_prods = list(p_to_cat.keys())
    return p_to_cat, p_to_name, p_to_price, p_to_cat_fullname, all_prods

product_to_category, product_to_name, product_to_price, product_to_cat_fullname, ALL_PRODUCTS = load_data(uploaded_file)

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
        # 模拟添加这个产品
        test_counts = current_counts.copy()
        test_counts[cat] = test_counts.get(cat, 0) + 1
        
        if check_rules(test_counts):
            allowed.append(p)
    return allowed

# === User Input & Logic ===

if "selected_products" not in st.session_state:
    st.session_state["selected_products"] = []

st.subheader("Products already in the Pallet")

# 1. 计算当前已选的状态
current_counts = Counter(
    product_to_category[p] for p in st.session_state["selected_products"]
)

# 2. 计算当前合法的后续选项
allowed_additions = get_allowed_products(current_counts)

# 3. 构建 Multiselect 的选项列表

valid_options = list(set(st.session_state["selected_products"]) | set(allowed_additions))

# 4. 渲染 Multiselect
valid_options.sort()

selected = st.multiselect(
    "Select Product code (Dynamically filtered):",
    options=valid_options,
    default=st.session_state["selected_products"],
    format_func=lambda x: f"{x} – {product_to_name.get(x, 'Unknown')}",
    key="multiselect_widget" # 使用 key 让 Streamlit 自动更新 session_state
)

# 手动同步 session state
if selected != st.session_state["selected_products"]:
    st.session_state["selected_products"] = selected
    st.rerun()

# === Status Calculation ===
current_counts = Counter(
    product_to_category[p] for p in selected
)

# 核心状态判断逻辑
is_current_valid = check_rules(current_counts)
can_add_more = len(allowed_additions) > 0

st.divider()


# 计算价格
total_price = sum(product_to_price.get(p, 0) for p in selected)
st.write(f"💰 **Total Pallet Price: € {total_price:.2f}**")

st.subheader("Status")

if not is_current_valid:
    st.error("❌ Pallet is exceeded capacity")
    st.caption("The current combination does not match any allowed rule.")

elif is_current_valid and not can_add_more:
    st.success("✅ Pallet is full")
    st.caption("Maximum capacity reached. No other items can be added.")
    
else: 
    st.info("✅ Pallet can still load")
    
    with st.expander("Show available additions details"):
        
        available_names = sorted(list(set(product_to_cat_fullname[p] for p in allowed_additions)))
        
        st.write(f"**Available Categories to add:**")
        st.write(", ".join(available_names))
        
        st.write("---")
        st.write("**Specific products (Sample):**")
        
        for p in allowed_additions[:10]:
            cat_fullname = product_to_cat_fullname[p]
            p_name = product_to_name[p]
            st.write(f"- {p} ({p_name}) [Category: {cat_fullname}]")
            

            

            
