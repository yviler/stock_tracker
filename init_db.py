import sqlite3

conn = sqlite3.connect("data/stock_tracker.db")
c = conn.cursor()

# Create Units Table
c.execute("""
CREATE TABLE IF NOT EXISTS units (
    unit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    unit_name TEXT UNIQUE NOT NULL
)
""")

# Create Items Table
c.execute("""
CREATE TABLE IF NOT EXISTS items (
    item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_name TEXT NOT NULL,
    unit_id INTEGER NOT NULL,
    category TEXT,
    is_daily_tracked BOOLEAN DEFAULT 1,
    FOREIGN KEY(unit_id) REFERENCES units(unit_id)
)
""")

# Create Stock Log Table
c.execute("""
CREATE TABLE IF NOT EXISTS stock_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    item_id INTEGER,
    opening_stock REAL,
    shipment_in REAL,
    closing_stock REAL,
    waste_qty REAL,
    waste_reason TEXT,
    void_qty REAL,
    void_reason TEXT,
    notes TEXT,
    used_qty REAL,
    FOREIGN KEY(item_id) REFERENCES items(item_id)
)
""")

# Optionally populate default units (only if not exists)
default_units = ["kg", "oz", "pcs", "liters", "grams"]
for unit in default_units:
    c.execute("INSERT OR IGNORE INTO units (unit_name) VALUES (?)", (unit,))

conn.commit()
conn.close()

print("✅ Database initialized.")
