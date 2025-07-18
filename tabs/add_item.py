import streamlit as st
import pandas as pd
from db import get_conn, fetch_df

def render():
    conn = get_conn()
    c = conn.cursor()

    unit_df = fetch_df("SELECT * FROM units ORDER BY unit_name")
    category_df = fetch_df("SELECT * FROM categories ORDER BY category_name")
    unit_names = unit_df["unit_name"].tolist()
    unit_id_map = dict(zip(unit_df["unit_name"], unit_df["unit_id"]))
    category_names = category_df["category_name"].tolist()
    category_id_map = dict(zip(category_df["category_name"], category_df["category_id"]))

    with st.form("add_item_form", clear_on_submit=True):
        st.subheader("➕ Add New Item")
        item_name = st.text_input("Item Name")
        unit_name = st.selectbox("Unit", unit_names)
        category_name = st.selectbox("Category", category_names)
        is_daily = st.checkbox("Tracked Daily?", value=True)

        if st.form_submit_button("Add Item"):
            if not item_name:
                st.error("Name is required.")
            else:
                existing = [n.casefold() for n in fetch_df("SELECT item_name FROM items")["item_name"]]
                if item_name.casefold() in existing:
                    st.error("This item already exists.")
                else:
                    c.execute("""
                        INSERT INTO items (item_name, unit_id, category_id, is_daily_tracked)
                        VALUES (?, ?, ?, ?)
                    """, (
                        item_name,
                        unit_id_map[unit_name],
                        category_id_map[category_name],
                        int(is_daily)
                    ))
                    conn.commit()
                    st.success(f"Added {item_name}")
                    st.rerun()

