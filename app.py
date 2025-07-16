import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

# DB connection
conn = sqlite3.connect("data/stock_tracker.db", check_same_thread=False)
c = conn.cursor()

st.set_page_config(page_title="Seafood Stock Tracker", layout="wide")
st.title("Seafood Stock Tracker")

# Fetch units
units_df = pd.read_sql_query("SELECT * FROM units ORDER BY unit_name", conn)
unit_names = units_df["unit_name"].tolist()
unit_name_to_id = dict(zip(units_df["unit_name"], units_df["unit_id"]))
unit_id_to_name = dict(zip(units_df["unit_id"], units_df["unit_name"]))

st.divider()
st.subheader("Inventory Manager")

tab_add, tab_edit = st.tabs(["Add Item", "Edit / Delete Item"])

with tab_add:
    with st.form("add_item_form", clear_on_submit=True):
        item_name = st.text_input("Item Name", placeholder="e.g. Salmon")
        unit_selection = st.selectbox("Unit", ["(Custom)"] + unit_names, key="unit_selection")
        show_custom = unit_selection == "(Custom)"
        custom_unit = st.text_input("Enter Custom Unit", placeholder="e.g. ml, tablespoon", key="custom_unit", disabled=not show_custom)
        unit_name = custom_unit.strip() if show_custom else unit_selection

        category = st.text_input("Category", placeholder="e.g. fish, condiment")
        is_daily = st.checkbox("Tracked Daily?", value=True)

        submit = st.form_submit_button("➕ Add Item")
        if submit:
            if item_name and unit_name:
                existing_names = [name.casefold() for name in pd.read_sql_query("SELECT item_name FROM items", conn)["item_name"]]
                if item_name.casefold() in existing_names:
                    st.error(f"❌ An item with the name '{item_name}' already exists.")
                else:
                    if show_custom:
                        existing_units = [u.casefold() for u in unit_names]
                        if unit_name.casefold() in existing_units:
                            st.error(f"❌ Unit '{unit_name}' already exists. Please select it from the list.")
                            st.stop()
                        else:
                            c.execute("INSERT INTO units (unit_name) VALUES (?)", (unit_name,))
                            conn.commit()
                            unit_id = c.execute("SELECT unit_id FROM units WHERE unit_name = ?", (unit_name,)).fetchone()[0]
                    else:
                        unit_id = unit_name_to_id[unit_name]

                    c.execute("""
                        INSERT INTO items (item_name, unit_id, category, is_daily_tracked)
                        VALUES (?, ?, ?, ?)
                    """, (item_name, unit_id, category, int(is_daily)))
                    conn.commit()
                    st.success(f"✅ Added item: {item_name}")
                    st.rerun()
            else:
                st.error("❌ Item name and unit are required.")

with tab_edit:
    search_query = st.text_input("🔍 Search Item by Name", key="search_query")
    search_query_casefold = search_query.casefold() if search_query else ""

    edit_item_df = pd.read_sql_query("""
        SELECT i.*, u.unit_name FROM items i
        JOIN units u ON i.unit_id = u.unit_id
    """, conn)

    filtered_df = edit_item_df[edit_item_df["item_name"].str.casefold().str.contains(search_query_casefold)] if search_query_casefold else pd.DataFrame()

    if search_query and filtered_df.empty:
        st.info("No items match your search.")
    elif not filtered_df.empty:
        selected_name = st.selectbox("Select Item to Edit", filtered_df["item_name"].tolist(), key="select_edit_item")
        selected_row = filtered_df[filtered_df["item_name"] == selected_name].iloc[0]

        with st.form(f"edit_form_{selected_row['item_id']}", clear_on_submit=True):
            st.markdown(f"**Editing: {selected_row['item_name']} ({selected_row['unit_name']})**")
            new_name = st.text_input("Item Name", value=selected_row['item_name'], key=f"name_{selected_row['item_id']}")
            new_unit_name = st.selectbox("Unit", unit_names, index=unit_names.index(selected_row['unit_name']), key=f"unit_{selected_row['item_id']}")
            new_unit_id = unit_name_to_id[new_unit_name]
            new_category = st.text_input("Category", value=selected_row['category'] or "", key=f"cat_{selected_row['item_id']}")
            new_daily = st.checkbox("Tracked Daily?", value=bool(selected_row['is_daily_tracked']), key=f"daily_{selected_row['item_id']}")

            col1, col2 = st.columns([1, 1])
            with col1:
                save = st.form_submit_button("📂 Save Changes")
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
                        c.execute("""
                            UPDATE items
                            SET item_name = ?, unit_id = ?, category = ?, is_daily_tracked = ?
                            WHERE item_id = ?
                        """, (new_name, new_unit_id, new_category, int(new_daily), selected_row['item_id']))
                        conn.commit()
                        st.success("✅ Item updated.")
                        st.rerun()

            with col2:
                delete = st.form_submit_button("🗑 Delete Item")
                if delete:
                    c.execute("DELETE FROM items WHERE item_id = ?", (selected_row['item_id'],))
                    conn.commit()
                    st.warning("🗑 Item deleted.")
                    st.rerun()

st.divider()
st.subheader("Daily Stock Logging")

item_df = pd.read_sql_query("SELECT i.*, u.unit_name FROM items i JOIN units u ON i.unit_id = u.unit_id", conn)

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

            c.execute("""
                INSERT INTO stock_log (
                    date, item_id, opening_stock, shipment_in,
                    closing_stock, waste_qty, waste_reason,
                    void_qty, void_reason, notes, used_qty
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                notes,
                used
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
