import streamlit as st
from collections import Counter

st.title("Pallet Rule Assistant")

# === 所有 pallet 规则 ===
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

ALL_PRODUCTS = sorted({p for rule in PALLET_RULES for p in rule.keys()})


def can_add(current, product, rules):
    test = current.copy()
    test[product] = test.get(product, 0) + 1

    for rule in rules:
        ok = True
        for p, qty in test.items():
            if rule.get(p, 0) < qty:
                ok = False
                break
        if ok:
            return True
    return False


def allowed_products(current, products, rules):
    return [p for p in products if can_add(current, p, rules)]


# === 当前 pallet 状态 ===
st.subheader("当前 pallet 内容")

selected = st.multiselect(
    "已放入的产品（可重复选）：",
    ALL_PRODUCTS
)

current = dict(Counter(selected))

st.write("当前数量：", current)

# === 推荐 ===
allowed = allowed_products(current, ALL_PRODUCTS, PALLET_RULES)

st.subheader("还可以继续放的产品：")
st.write(allowed if allowed else "❌ 没有任何产品可以再放")
