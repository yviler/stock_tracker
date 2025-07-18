import streamlit as st
import pandas as pd
from db import fetch_df
from datetime import date

def render():
    st.subheader("📅 View Logged Stock")
    d = st.date_input("Select date", value=date.today(), key="view_date")
    df = fetch_df("""
        SELECT l.*, i.item_name, u.unit_name
        FROM stock_log l
        JOIN items i ON l.item_id = i.item_id
        JOIN units u ON i.unit_id = u.unit_id
        WHERE l.date=?
        ORDER BY i.item_name
    """, (d.strftime("%Y-%m-%d"),))
    if df.empty:
        st.info("No records.")
    else:
        st.dataframe(df)
