with col1:
    st.subheader(f"📍 Aktuelle Palette #{st.session_state['palette_nr']}")
    
    # 计算当前哪些产品还能加进去
    moegliche_produkte = [
        p for p in ALLE_PRODUKTE 
        if check_palette_valid({**aktuelle_counts, produkt_zu_kategorie[p]: aktuelle_counts[produkt_zu_kategorie[p]] + 1})
    ]

    if not moegliche_produkte:
        # === 这里改成了绿色成功提示和对勾 ===
        st.success("✅ **Palette ist optimal ausgelastet!**")
        st.info("Diese Palette hat ihr Limit erreicht und kann gespeichert werden.")
        gewaehlte_sku = None
        menge_erlaubt = False
    else:
        gewaehlte_sku = st.selectbox("Produkt wählen", options=moegliche_produkte, 
                                     format_func=lambda x: f"{x} – {produkt_zu_name.get(x, '')}")
        menge = st.number_input("Menge", min_value=1, max_value=50, value=1)

        # 实时校验
        if gewaehlte_sku:
            test_counts = aktuelle_counts.copy()
            kat = produkt_zu_kategorie[gewaehlte_sku]
            test_counts[kat] += menge
            menge_erlaubt = check_palette_valid(test_counts)
            
            if not menge_erlaubt:
                st.error(f"❌ Kombination nicht erlaubt oder Limit überschritten!")
        else:
            menge_erlaubt = False

    st.write("") 

    # --- 按钮布局 (Hinzufügen | Leeren | Gap | Speichern) ---
    b_col1, b_col2, b_gap, b_col3 = st.columns([1, 1, 0.2, 1])
    
    with b_col1:
        # 如果托盘满了，添加按钮自然不可用
        add_ok = gewaehlte_sku is not None and menge_erlaubt
        if st.button("➕ Hinzufügen", type="primary", use_container_width=True, disabled=not add_ok):
            st.session_state["waren_auf_palette"][gewaehlte_sku] = st.session_state["waren_auf_palette"].get(gewaehlte_sku, 0) + menge
            st.rerun()
            
    with b_col2:
        if st.button("🗑️ Leeren", use_container_width=True):
            st.session_state["waren_auf_palette"] = {}
            st.rerun()

    with b_col3:
        hat_inhalt = len(st.session_state["waren_auf_palette"]) > 0
        # 即使托盘没满，只要有东西就能保存；如果满了，这个按钮就是下一步的重点
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
