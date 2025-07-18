import streamlit as st
from db import get_conn, fetch_df
from datetime import date

def render():
    conn = get_conn()
    c = conn.cursor()

    st.subheader("📥 Daily Stock Logging")
    items = fetch_df("""
        SELECT i.item_id, i.item_name, u.unit_name
        FROM items i
        JOIN units u ON i.unit_id = u.unit_id
    """)
    if items.empty:
        st.warning("No items available.")
        return

    with st.form("stock_log_form"):
        d = st.date_input("Date", value=date.today())
        sel_idx = st.selectbox("Item", items.index, format_func=lambda i: items.at[i, "item_name"])
        row = items.loc[sel_idx]

        opening = st.number_input("Opening Stock", min_value=0.0)
        shipment = st.number_input("Shipment In", min_value=0.0)
        price = st.number_input("Price per Unit", min_value=0.0, step=100.0)
        closing = st.number_input("Closing Stock", min_value=0.0)
        waste = st.number_input("Waste Qty", min_value=0.0)
        void = st.number_input("Void Qty", min_value=0.0)
        notes = st.text_area("Notes")

        if st.form_submit_button("Log Stock"):
            used = opening + shipment - (closing + waste + void)
            c.execute("""
                INSERT INTO stock_log
                  (date,item_id, opening_stock, shipment_in, closing_stock, waste_qty, void_qty, price_per_unit, notes, used_qty)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                d.strftime("%Y-%m-%d"),
                row["item_id"],
                opening, shipment, closing, waste, void,
                price, notes, used
            ))
            conn.commit()
            st.success("Logged successfully.")

