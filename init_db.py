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

# Create Categories Table
c.execute("""
CREATE TABLE IF NOT EXISTS categories (
    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_name TEXT UNIQUE NOT NULL
)
""")

# Create Items Table
c.execute("""
CREATE TABLE IF NOT EXISTS items (
    item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_name TEXT NOT NULL,
    unit_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    is_daily_tracked BOOLEAN DEFAULT 1,
    FOREIGN KEY(unit_id) REFERENCES units(unit_id),
    FOREIGN KEY(category_id) REFERENCES categories(category_id)
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
    price_per_unit REAL,
    notes TEXT,
    used_qty REAL,
    FOREIGN KEY(item_id) REFERENCES items(item_id)
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS item_prices (
    price_id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    price_per_unit REAL,
    total_price REAL,
    quantity REAL,
    FOREIGN KEY(item_id) REFERENCES items(item_id)
)
""")

# Insert default units
default_units = ["kg", "oz", "pcs", "liters", "grams"]
for unit in default_units:
    c.execute("INSERT OR IGNORE INTO units (unit_name) VALUES (?)", (unit,))

# Insert default categories
default_categories = ["ikan", "saos", "bahan", "kepiting", "udang", "kerang", "cumi", "buah", "sayur"]
for category in default_categories:
    c.execute("INSERT OR IGNORE INTO categories (category_name) VALUES (?)", (category,))

conn.commit()
conn.close()

print("✅ Database initialized")
