import streamlit as st
from db import fetch_df
import tabs.add_item as add_item
import tabs.edit_item as edit_item
import tabs.log_stock as log_stock
import tabs.view_log as view_logs

st.set_page_config(page_title="Stock Tracker", layout="wide")
st.title("Stock Tracker")

tabs = st.tabs([
    "➕ Add Item",
    "✏️ Edit / Delete Item",
    "📥 Log Stock",
    "📅 View Logs",
])

with tabs[0]:
    add_item.render()

with tabs[1]:
    edit_item.render()

with tabs[2]:
    log_stock.render()

with tabs[3]:
    view_logs.render()
