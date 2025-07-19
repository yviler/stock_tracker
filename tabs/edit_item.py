# tabs/edit_item.py
import os
import streamlit as st
from db import get_conn, fetch_df

def render():
    conn = get_conn()
    c    = conn.cursor()

    # —–––––––––––––––––––––––––––––––––––––––––––
    # DEBUG #1: Which DB file are we using?
    dbs = conn.execute("PRAGMA database_list").fetchall()
    # dbs = [(seq, name, file), …]
    st.write("🗄️ Open SQLite files:", dbs)
    # You should see a single entry with the path to your stock_tracker.db

    # 1) Load lookup tables
    unit_df     = fetch_df("SELECT * FROM units ORDER BY unit_name", ())
    unit_names  = unit_df["unit_name"].tolist()
    unit_id_map = dict(zip(unit_names, unit_df["unit_id"]))

    cat_df      = fetch_df("SELECT * FROM categories ORDER BY category_name", ())
    cat_names   = cat_df["category_name"].tolist()
    cat_id_map  = dict(zip(cat_names, cat_df["category_id"]))

    # 2) Fetch all items (and show count)
    items_df = fetch_df("""
        SELECT i.item_id, i.item_name, u.unit_name, c.category_name, i.is_daily_tracked
        FROM items i
        JOIN units u       ON i.unit_id     = u.unit_id
        JOIN categories c  ON i.category_id = c.category_id
        ORDER BY i.item_name
    """, ())
    st.write(f"📋 Items in DB: {len(items_df)}")

    st.subheader("✏️ Edit / Delete Item")
    if items_df.empty:
        st.info("No items available. Please add some first.")
        return

    # 3) Pick one
    selected = st.selectbox("Select item to edit (start typing)…", items_df["item_name"].tolist())
    row = items_df[items_df["item_name"] == selected].iloc[0]

    # 4) Show current values
    st.markdown(f"**Editing:** {row['item_name']}  •  _{row['unit_name']}_ • _{row['category_name']}_")

    # 5) Editable widgets
    new_name  = st.text_input("Name", value=row["item_name"], key=f"name_{row['item_id']}")
    new_unit  = st.selectbox("Unit", unit_names,
                             index=unit_names.index(row["unit_name"]),
                             key=f"unit_{row['item_id']}")
    new_cat   = st.selectbox("Category", cat_names,
                             index=cat_names.index(row["category_name"]),
                             key=f"cat_{row['item_id']}")
    new_daily = st.checkbox("Tracked Daily?", value=bool(row["is_daily_tracked"]),
                            key=f"daily_{row['item_id']}")

    col1, col2 = st.columns(2)

    # —–––––––––––––––––––––––––––––––––––––––––––
    # DEBUG #2: Show the row before any change
    st.write("🕵️ Row before any change:", row.to_dict())

    # 6) Save button
    with col1:
        if st.button("💾 Save Changes", key=f"save_{row['item_id']}"):
            st.write("▶️ [DEBUG] Save clicked")
            try:
                c.execute("""
                    UPDATE items
                    SET item_name        = ?,
                        unit_id          = ?,
                        category_id      = ?,
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
                st.write("✔️ [DEBUG] Commit succeeded.")
            except Exception as e:
                st.write("❌ [DEBUG] Commit failed:", e)

            # DEBUG #3: Read it back immediately
            updated = fetch_df("SELECT * FROM items WHERE item_id = ?", (row["item_id"],))
            st.write("🗄️ [DEBUG] Row after UPDATE:", updated)

    # 7) Delete button
    with col2:
        if st.button("🗑 Delete Item", key=f"del_{row['item_id']}"):
            st.write("▶️ [DEBUG] Delete clicked")
            try:
                c.execute("DELETE FROM items WHERE item_id = ?", (row["item_id"],))
                conn.commit()
                st.write("✔️ [DEBUG] DELETE succeeded.")
            except Exception as e:
                st.write("❌ [DEBUG] DELETE failed:", e)

            # DEBUG #4: Verify deletion
            remaining = fetch_df("SELECT * FROM items WHERE item_id = ?", (row["item_id"],))
            st.write("🗄️ [DEBUG] Row after DELETE (should be empty):", remaining)
