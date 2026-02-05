import streamlit as st
import pandas as pd
from collections import Counter

st.title("Pallet Assistant (Category-based)")

# Excel Sheet
uploaded_file = st.file_uploader("Bitte Excel-Datei hochladen", type=["xlsx"])

if not uploaded_file:
    st.stop()

# Product code | Category code
models = pd.read_excel(uploaded_file, sheet_name="Models")
product_to_category = dict(
    zip(models["Product code"], models["Category code"])
)

ALL_PRODUCTS = list(product_to_category.keys())
ALL_CATEGORIES = set(product_to_category.values())

# Rules
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


def can_add_category(current_cat_count, new_cat):
    test = current_cat_count.copy()
    test[new_cat] = test.get(new_cat, 0) + 1

    for rule in PALLET_RULES:
        ok = True
        for cat, qty in test.items():
            if rule.get(cat, 0) < qty:
                ok = False
                break
        if ok:
            return True
    return False


# Input
st.subheader("Product in the Pallet")

selected_products = st.multiselect(
    "Product in the Pallet：",
    ALL_PRODUCTS
)


# === 推荐还能放什么 Product ===
allowed_products = []

for p in ALL_PRODUCTS:
    cat = product_to_category[p]
    if can_add_category(current_categories, cat):
        allowed_products.append(p)

st.subheader("Product to put：")
if allowed_products:
    st.write(allowed_products)
else:
    st.write("Pallet is full")
