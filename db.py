import sqlite3
import pandas as pd

DB_PATH = "data/stock_tracker.db"

_conn = None

def get_conn():
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    return _conn

def get_cursor():
    return get_conn().cursor()

def fetch_df(query, params=()):
    return pd.read_sql_query(query, get_conn(), params=params)

