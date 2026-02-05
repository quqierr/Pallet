import streamlit as st
import pandas as pd
from collections import Counter

st.title("Pallet Assistant (Category-based)")

# === Excel Sheet ===
uploaded_file = st.file_uploader("Bitte Excel-Datei hochladen", type=["xlsx"])

if not uploaded_file:
    st.stop()

# === Product infomation ===

models = pd.read_excel(uploaded_file, sheet_name="Models")

product_to_category = dict(zip(models["Product code"], models["Category code"]))
product_to_name = dict(zip(models["Product code"], models["Product name"]))
product_to_price = dict(zip(models["Product code"], models["Product price"]))

ALL_PRODUCTS = list(product_to_category.keys())

# === Rule ===
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


# === Rule check function ===
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


# === User input ===
st.subheader("Products already in the Pallet")

selected_products = st.multiselect(
    "Select Product code (repeat allowed):",
    ALL_PRODUCTS,
    format_func=lambda x: f"{x} – {product_to_name[x]}"
)

# === Current pallet status ===
current_categories = Counter(
    product_to_category[p] for p in selected_products
)

st.write("Current Category count:", dict(current_categories))

# === Total pallet price ===
total_price = sum(product_to_price[p] for p in selected_products)
st.write(f"💰 Total Pallet Price: € {total_price:.2f}")

# === Recommend what can still be added ===
allowed_products = []

for p in ALL_PRODUCTS:
    cat = product_to_category[p]
    if can_add_category(current_categories, cat):
        allowed_products.append(p)

st.subheader("Products that can still be added:")

if allowed_products:
    st.write([
        f"{p} – {product_to_name[p]} (€{product_to_price[p]:.2f})"
        for p in allowed_products
    ])
else:
    st.write("❌ Pallet is full")
