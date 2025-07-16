import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

# DB connection
conn = sqlite3.connect("data/stock_tracker.db", check_same_thread=False)
c = conn.cursor()

st.set_page_config(page_title="Seafood Stock Tracker", layout="wide")
st.title("Seafood Stock Tracker")

# Fetch units and categories
units_df = pd.read_sql_query("SELECT * FROM units ORDER BY unit_name", conn)
unit_names = units_df["unit_name"].tolist()
unit_name_to_id = dict(zip(units_df["unit_name"], units_df["unit_id"]))

categories_df = pd.read_sql_query("SELECT * FROM categories ORDER BY category_name", conn)
category_names = categories_df["category_name"].tolist()
category_name_to_id = dict(zip(categories_df["category_name"], categories_df["category_id"]))

st.divider()
st.subheader("Inventory Manager")

tab_add, tab_edit = st.tabs(["Add Item", "Edit / Delete Item"])

with tab_add:
    with st.form("add_item_form", clear_on_submit=True):
        item_name = st.text_input("Item Name", placeholder="e.g. Salmon")
        unit_name = st.selectbox("Unit", unit_names)
        category_name = st.selectbox("Category", category_names)
        is_daily = st.checkbox("Tracked Daily?", value=True)

        submit = st.form_submit_button("➕ Add Item")
        if submit:
            if item_name and unit_name and category_name:
                existing_names = [name.casefold() for name in pd.read_sql_query("SELECT item_name FROM items", conn)["item_name"]]
                if item_name.casefold() in existing_names:
                    st.error(f"❌ An item with the name '{item_name}' already exists.")
                else:
                    unit_id = unit_name_to_id[unit_name]
                    category_id = category_name_to_id[category_name]
                    c.execute("""
                        INSERT INTO items (item_name, unit_id, category_id, is_daily_tracked)
                        VALUES (?, ?, ?, ?)
                    """, (item_name, unit_id, category_id, int(is_daily)))
                    conn.commit()
                    st.success(f"✅ Added item: {item_name}")
                    st.rerun()
            else:
                st.error("❌ All fields are required.")

with tab_edit:
    search_query = st.text_input("🔍 Search Item by Name", key="search_query")
    search_query_casefold = search_query.casefold() if search_query else ""

    edit_item_df = pd.read_sql_query("""
        SELECT i.*, u.unit_name, c.category_name FROM items i
        JOIN units u ON i.unit_id = u.unit_id
        JOIN categories c ON i.category_id = c.category_id
    """, conn)

    filtered_df = edit_item_df[edit_item_df["item_name"].str.casefold().str.contains(search_query_casefold)] if search_query_casefold else pd.DataFrame()

    if search_query and filtered_df.empty:
        st.info("No items match your search.")
    elif not filtered_df.empty:
        selected_name = st.selectbox("Select Item to Edit", filtered_df["item_name"].tolist(), key="select_edit_item")
        selected_row = filtered_df[filtered_df["item_name"] == selected_name].iloc[0]

        with st.form(f"edit_form_{selected_row['item_id']}", clear_on_submit=False):
            st.markdown(f"**Editing: {selected_row['item_name']} ({selected_row['unit_name']})**")
            new_name = st.text_input("Item Name", value=selected_row['item_name'], key=f"name_{selected_row['item_id']}")
            new_unit_name = st.selectbox("Unit", unit_names, index=unit_names.index(selected_row['unit_name']), key=f"unit_{selected_row['item_id']}")
            new_category_name = st.selectbox("Category", category_names, index=category_names.index(selected_row['category_name']), key=f"cat_{selected_row['item_id']}")
            new_daily = st.checkbox("Tracked Daily?", value=bool(selected_row['is_daily_tracked']), key=f"daily_{selected_row['item_id']}")

            save = st.form_submit_button("📂 Save Changes")
            delete = st.form_submit_button("🗑 Delete Item")

            if save:
                existing_names_df = pd.read_sql_query("SELECT item_id, item_name FROM items", conn)
                name_conflict = any(
                    existing_row["item_id"] != selected_row["item_id"] and
                    existing_row["item_name"].casefold() == new_name.casefold()
                    for _, existing_row in existing_names_df.iterrows()
                )

                if name_conflict:
                    st.error(f"❌ Cannot rename to '{new_name}' — another item already has that name.")
                else:
                    new_unit_id = unit_name_to_id[new_unit_name]
                    new_category_id = category_name_to_id[new_category_name]
                    c.execute("""
                        UPDATE items
                        SET item_name = ?, unit_id = ?, category_id = ?, is_daily_tracked = ?
                        WHERE item_id = ?
                    """, (new_name, new_unit_id, new_category_id, int(new_daily), selected_row['item_id']))
                    conn.commit()
                    st.success("✅ Item updated.")
                    st.rerun()

            elif delete:
                c.execute("DELETE FROM items WHERE item_id = ?", (selected_row['item_id'],))
                conn.commit()
                st.warning("🗑 Item deleted.")
                st.rerun()

st.divider()
st.subheader("Daily Stock Logging")

item_df = pd.read_sql_query("""
    SELECT i.*, u.unit_name, c.category_name FROM items i
    JOIN units u ON i.unit_id = u.unit_id
    JOIN categories c ON i.category_id = c.category_id
""", conn)

if item_df.empty:
    st.warning("⚠️ No items available. Please add items first.")
else:
    with st.form("stock_log_form"):
        log_date = st.date_input("Date", value=date.today())

        selected_index = st.selectbox("Select Item", item_df.index, format_func=lambda i: item_df.at[i, "item_name"])
        selected_row = item_df.loc[selected_index]
        selected_item_id = selected_row["item_id"]
        selected_item_name = selected_row["item_name"]

        st.markdown("### 📦 Stock Data")
        opening = st.number_input("Opening Stock", min_value=0.0, step=0.1)
        shipment = st.number_input("Shipment In", min_value=0.0, step=0.1)
        closing = st.number_input("Closing Stock", min_value=0.0, step=0.1)
        price = st.number_input("Price per Unit (for Shipment In)", min_value=0.0, step=100.0)

        st.markdown("### 🗑 Waste")
        waste = st.number_input("Waste Quantity", min_value=0.0, step=0.1)
        waste_reason = st.text_input("Waste Reason")

        st.markdown("### ❌ Void")
        void = st.number_input("Void Quantity", min_value=0.0, step=0.1)
        void_reason = st.text_input("Void Reason")

        notes = st.text_area("Notes (optional)")

        submitted_log = st.form_submit_button("Log Stock")
        if submitted_log:
            used = opening + shipment - (closing + waste + void)
            total_price = price * shipment if shipment else 0

            c.execute("""
                INSERT INTO stock_log (
                    date, item_id, opening_stock, shipment_in,
                    closing_stock, waste_qty, waste_reason,
                    void_qty, void_reason, price_per_unit, notes, used_qty
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                log_date.strftime("%Y-%m-%d"),
                selected_item_id,
                opening,
                shipment,
                closing,
                waste,
                waste_reason,
                void,
                void_reason,
                price,
                notes,
                used
            ))

            if shipment > 0 and price > 0:
                c.execute("""
                    INSERT INTO item_prices (item_id, date, price_per_unit, total_price, quantity)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    selected_item_id,
                    log_date.strftime("%Y-%m-%d"),
                    price,
                    total_price,
                    shipment
                ))

            conn.commit()
            st.success(f"✅ Logged stock for {selected_item_name} on {log_date.strftime('%Y-%m-%d')} — Used: {used:.2f}")

st.divider()
st.subheader("View Logged Stock")

log_date_to_view = st.date_input("Select Date to View Logs", value=date.today(), key="log_view_date")

log_df = pd.read_sql_query("""
    SELECT l.*, i.item_name, u.unit_name
    FROM stock_log l
    JOIN items i ON l.item_id = i.item_id
    JOIN units u ON i.unit_id = u.unit_id
    WHERE l.date = ?
    ORDER BY i.item_name
""", conn, params=(log_date_to_view.strftime("%Y-%m-%d"),))

if log_df.empty:
    st.info("No logs found for this date.")
else:
    st.dataframe(log_df, use_container_width=True)
