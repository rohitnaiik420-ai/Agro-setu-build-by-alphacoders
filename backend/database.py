import sqlite3
import os
import json
from pathlib import Path
from datetime import datetime

DB_DIR = Path(__file__).resolve().parent.parent / "data"
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DB_DIR / "agri_system.db"

def get_db_connection():
    """Returns a SQLite connection with row factory set to dict-like rows."""
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database schema if tables do not already exist."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Farmers / FPOs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS farmers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        fpo_name TEXT NOT NULL,
        phone TEXT NOT NULL,
        city TEXT NOT NULL,
        state TEXT DEFAULT 'Maharashtra',
        address TEXT,
        rating REAL DEFAULT 4.8,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Products / Crops listed by Farmers
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        farmer_id INTEGER,
        crop_name TEXT NOT NULL,
        category TEXT NOT NULL,
        quantity_kg REAL NOT NULL,
        available_quantity_kg REAL NOT NULL,
        price_per_kg REAL NOT NULL,
        location TEXT NOT NULL,
        harvest_date TEXT NOT NULL,
        available_date TEXT NOT NULL,
        quality_grade TEXT DEFAULT 'Grade A',
        description TEXT,
        image_url TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (farmer_id) REFERENCES farmers(id)
    );
    """)

    # 3. Orders placed by Consumers / Bulk Buyers
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_number TEXT UNIQUE NOT NULL,
        product_id INTEGER NOT NULL,
        product_name TEXT NOT NULL,
        farmer_name TEXT NOT NULL,
        buyer_name TEXT NOT NULL,
        buyer_phone TEXT NOT NULL,
        buyer_email TEXT,
        delivery_address TEXT NOT NULL,
        delivery_city TEXT NOT NULL,
        quantity_kg REAL NOT NULL,
        price_per_kg REAL NOT NULL,
        total_amount REAL NOT NULL,
        order_status TEXT DEFAULT 'Confirmed',
        payment_status TEXT DEFAULT 'Paid',
        payment_method TEXT DEFAULT 'UPI',
        transaction_id TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (product_id) REFERENCES products(id)
    );
    """)

    # 4. Logistics Vehicles / Fleet
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vehicles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vehicle_no TEXT UNIQUE NOT NULL,
        vehicle_type TEXT NOT NULL,
        capacity_kg REAL NOT NULL,
        per_km_rate REAL NOT NULL,
        driver_name TEXT NOT NULL,
        driver_phone TEXT NOT NULL,
        current_location TEXT NOT NULL,
        status TEXT DEFAULT 'Available'
    );
    """)

    # 5. Logistics Shipments (Nashik -> Collection Center -> Pune Buyer)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS shipments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tracking_no TEXT UNIQUE NOT NULL,
        order_id INTEGER,
        cargo_description TEXT NOT NULL,
        weight_kg REAL NOT NULL,
        pickup_location TEXT NOT NULL,
        collection_center TEXT NOT NULL,
        delivery_location TEXT NOT NULL,
        vehicle_id INTEGER,
        vehicle_no TEXT,
        driver_name TEXT,
        driver_phone TEXT,
        status TEXT DEFAULT 'In Transit',
        distance_km REAL NOT NULL,
        estimated_hours REAL NOT NULL,
        transport_cost REAL NOT NULL,
        eta_timestamp TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (order_id) REFERENCES orders(id),
        FOREIGN KEY (vehicle_id) REFERENCES vehicles(id)
    );
    """)

    # 6. Demand Forecasting Historical Data
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS demand_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        crop_name TEXT NOT NULL,
        city TEXT NOT NULL,
        record_date TEXT NOT NULL,
        demand_kg REAL NOT NULL,
        sales_kg REAL NOT NULL,
        avg_price_per_kg REAL NOT NULL,
        season TEXT NOT NULL,
        weather TEXT NOT NULL,
        festival_factor REAL DEFAULT 1.0,
        notes TEXT
    );
    """)

    # 7. Route Optimization Waypoints (Scenario: 5 Farmers -> Central Hub)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS route_waypoints (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        farmer_label TEXT NOT NULL,
        farmer_name TEXT NOT NULL,
        location_name TEXT NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        produce_type TEXT NOT NULL,
        pickup_qty_kg REAL NOT NULL,
        stop_order INTEGER DEFAULT 0
    );
    """)

    # --- Schema Migrations for GPS & Breakdown Recovery ---
    # Ensure vehicles table has lat, lon coordinates
    v_cols = [c[1] for c in cursor.execute("PRAGMA table_info(vehicles);").fetchall()]
    if "lat" not in v_cols:
        cursor.execute("ALTER TABLE vehicles ADD COLUMN lat REAL DEFAULT 18.5204;")
    if "lon" not in v_cols:
        cursor.execute("ALTER TABLE vehicles ADD COLUMN lon REAL DEFAULT 73.8567;")

    # Ensure shipments table has breakdown recovery & live GPS columns
    s_cols = [c[1] for c in cursor.execute("PRAGMA table_info(shipments);").fetchall()]
    gps_breakdown_columns = [
        ("current_lat", "REAL DEFAULT 19.4520"),
        ("current_lon", "REAL DEFAULT 74.1500"),
        ("current_location_desc", "TEXT DEFAULT 'NH-60 Agro-Corridor, near Sangamner'"),
        ("breakdown_status", "TEXT DEFAULT 'NORMAL'"),
        ("breakdown_reason", "TEXT DEFAULT ''"),
        ("breakdown_lat", "REAL DEFAULT 0"),
        ("breakdown_lon", "REAL DEFAULT 0"),
        ("breakdown_timestamp", "TEXT DEFAULT ''"),
        ("backup_vehicle_id", "INTEGER DEFAULT 0"),
        ("backup_vehicle_no", "TEXT DEFAULT ''"),
        ("backup_vehicle_type", "TEXT DEFAULT ''"),
        ("backup_driver_name", "TEXT DEFAULT ''"),
        ("backup_driver_phone", "TEXT DEFAULT ''"),
        ("backup_distance_km", "REAL DEFAULT 0"),
        ("backup_eta_mins", "INTEGER DEFAULT 0")
    ]
    for col_name, col_def in gps_breakdown_columns:
        if col_name not in s_cols:
            cursor.execute(f"ALTER TABLE shipments ADD COLUMN {col_name} {col_def};")

    # Update known vehicle coordinates for accurate GPS distances
    vehicle_coords = [
        ("MH-15-EG-4412", 19.9975, 73.7898), # Nashik Hub
        ("MH-12-PQ-8901", 19.4520, 74.1500), # En route NH-60
        ("MH-17-BC-5520", 19.5761, 74.2070), # Sangamner Center (Nearest backup ~15 km!)
        ("MH-16-AY-7734", 19.0948, 74.7480), # Ahmednagar Hub (~68 km)
        ("MH-11-DF-2299", 17.6805, 74.0183), # Satara Depot (~195 km)
        ("DL-1L-AA-3344", 28.7126, 77.1740), # Delhi Azadpur
        ("MP-09-GF-8812", 22.7196, 75.8577)  # Indore Krishi Mandi
    ]
    for v_no, v_lat, v_lon in vehicle_coords:
        cursor.execute("UPDATE vehicles SET lat = ?, lon = ? WHERE vehicle_no = ?;", (v_lat, v_lon, v_no))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print(f"Database successfully initialized at: {DB_PATH}")
