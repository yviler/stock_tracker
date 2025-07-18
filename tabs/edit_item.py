# tabs/edit_item.py
import streamlit as st
from db import get_conn, fetch_df

def render():
    conn = get_conn()
    c = conn.cursor()

    # 1) Load lookup tables
    unit_df = fetch_df("SELECT * FROM units ORDER BY unit_name", ())
    unit_names = unit_df["unit_name"].tolist()
    unit_id_map = dict(zip(unit_names, unit_df["unit_id"]))

    cat_df = fetch_df("SELECT * FROM categories ORDER BY category_name", ())
    cat_names = cat_df["category_name"].tolist()
    cat_id_map = dict(zip(cat_names, cat_df["category_id"]))

    # 2) Fetch all items
    items_df = fetch_df("""
        SELECT
          i.item_id,
          i.item_name,
          u.unit_name,
          c.category_name,
          i.is_daily_tracked
        FROM items i
        JOIN units u ON i.unit_id = u.unit_id
        JOIN categories c ON i.category_id = c.category_id
        ORDER BY i.item_name
    """, ())

    st.subheader("✏️ Edit / Delete Item")

    # 3) No items guard
    if items_df.empty:
        st.info("No items available. Please add one first.")
        return

    # 4) Single selectbox with type-ahead
    selected_name = st.selectbox(
        "Select item to edit (type to search)…",
        items_df["item_name"].tolist()
    )
    row = items_df[items_df["item_name"] == selected_name].iloc[0]

    # 5) Edit form (only Save inside)
    form_key = f"edit_form_{row['item_id']}"
    with st.form(form_key):
        st.markdown(f"**Editing:** {row['item_name']}  •  _{row['unit_name']}_, _{row['category_name']}_")
        new_name = st.text_input("Name", value=row["item_name"])
        new_unit = st.selectbox("Unit", unit_names, index=unit_names.index(row["unit_name"]))
        new_cat  = st.selectbox("Category", cat_names, index=cat_names.index(row["category_name"]))
        new_daily = st.checkbox("Tracked Daily?", value=bool(row["is_daily_tracked"]))

        # ★ Only one form_submit_button allowed here, no key= argument
        save_clicked = st.form_submit_button("💾 Save Changes")

    # 6) Handle Save
    if save_clicked:
        # Check duplicates
        existing = fetch_df("SELECT item_id, item_name FROM items", ())
        conflict = any(
            r["item_id"] != row["item_id"] and
            r["item_name"].casefold() == new_name.casefold()
            for _, r in existing.iterrows()
        )
        if conflict:
            st.error("❌ Another item already uses that name.")
        else:
            c.execute("""
                UPDATE items
                SET item_name       = ?,
                    unit_id         = ?,
                    category_id     = ?,
                    is_daily_tracked = ?
                WHERE item_id = ?
            """, (
                new_name,
                unit_id_map[new_unit],
                cat_id_map[new_cat],
                int(new_daily),
                row["item_id"]
            ))
            conn.commit()
            st.success("✅ Item updated.")
            st.rerun()

    # 7) Delete button outside the form
    delete_clicked = st.button("🗑 Delete Item", key=f"delete_{row['item_id']}")
    if delete_clicked:
        c.execute("DELETE FROM items WHERE item_id = ?", (row["item_id"],))
        conn.commit()
        st.warning("🗑 Item deleted.")
        st.rerun()
