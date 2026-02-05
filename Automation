import pandas as pd
import streamlit as st

st.title("Pallet Combination Assistant")

# 上传 Excel
uploaded_file = st.file_uploader("上传 Excel 文件", type=["xlsx"])

if uploaded_file:
    models = pd.read_excel(uploaded_file, sheet_name="Models")
    combination = pd.read_excel(uploaded_file, sheet_name="Combination")

    # 生成规则表
    rules = []
    for col in combination.columns:
        products = combination[col].dropna().tolist()
        for a in products:
            for b in products:
                if a != b:
                    rules.append((a, b))
    rules_df = pd.DataFrame(rules, columns=["Product_A", "Product_B"])

    # 选择已放产品
    selected_products = st.multiselect(
        "已放入 pallet 的产品：",
        models["Product code"].tolist()
    )

    # 计算剩余空间
    used = 0
    for p in selected_products:
        cap = models.loc[models["Product code"] == p, "Numbers on one pallet"].values[0]
        used += 1 / cap

    remaining = max(0, 1 - used)
    st.write(f"剩余 pallet 空间：{round(remaining, 2)}")

    # 推荐逻辑
    def get_allowed_products(selected_products, remaining_space):
        allowed = []

        for _, row in models.iterrows():
            product = row["Product code"]
            capacity = row["Numbers on one pallet"]
            needed_space = 1 / capacity

            if needed_space > remaining_space:
                continue

            ok = True
            for sel in selected_products:
                if not (
                    ((rules_df["Product_A"] == sel) & (rules_df["Product_B"] == product)).any()
                ):
                    ok = False
                    break

            if ok:
                allowed.append(product)

        return allowed

    if selected_products:
        allowed = get_allowed_products(selected_products, remaining)
        st.subheader("还能放的产品：")
        st.write(allowed)
