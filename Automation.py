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
    all_prods = list(p_to_cat.keys())
    return p_to_cat, p_to_name, p_to_price, all_prods

product_to_category, product_to_name, product_to_price, ALL_PRODUCTS = load_data(uploaded_file)

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
    """
    检查给定的分类数量是否符合任意一条规则。
    返回 True 表示合法（在规则内），False 表示不合法（超载）。
    """
    for rule in PALLET_RULES:
        is_rule_ok = True
        for cat, qty in cat_counts.items():
            # 如果现有数量 > 规则允许数量，则该规则不适用
            if rule.get(cat, 0) < qty:
                is_rule_ok = False
                break
        if is_rule_ok:
            return True
    return False

def get_allowed_products(current_counts):
    """
    基于当前状态，计算还有哪些产品可以添加。
    """
    allowed = []
    for p in ALL_PRODUCTS:
        cat = product_to_category[p]
        # 模拟添加这个产品
        test_counts = current_counts.copy()
        test_counts[cat] = test_counts.get(cat, 0) + 1
        
        # 检查添加后是否合法
        if check_rules(test_counts):
            allowed.append(p)
    return allowed

# === User Input & Logic ===

# 初始化 Session State 用于存储选择，以便我们能动态过滤选项
if "selected_products" not in st.session_state:
    st.session_state["selected_products"] = []

st.subheader("Products already in the Pallet")

# 1. 计算当前已选的状态
current_counts = Counter(
    product_to_category[p] for p in st.session_state["selected_products"]
)

# 2. 计算当前合法的后续选项 (Lookahead)
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

# 手动同步 session state (虽然使用了 key 通常会自动同步，但为了保险起见)
if selected != st.session_state["selected_products"]:
    st.session_state["selected_products"] = selected
    st.rerun() # 重新运行以刷新列表逻辑

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

else: # is_current_valid and can_add_more
    st.info("✅ Pallet can still load")
    

    with st.expander("Show available additions details"):
        available_cats = set(product_to_category[p] for p in allowed_additions)
        st.write(f"Available Categories to add: {', '.join(available_cats)}")
        
        st.write("Specific products (Sample):")
        for p in allowed_additions[:30]:
            st.write(f"- {p} ({product_to_name[p]})")
        if len(allowed_additions) > 10:
            st.write(f"... and {len(allowed_additions)-10} more.")
