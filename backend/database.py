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

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print(f"Database successfully initialized at: {DB_PATH}")
