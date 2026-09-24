import sqlite3
import os
import json
import shutil
from pathlib import Path
from datetime import datetime

# Serverless environment detection (Vercel, AWS Lambda, etc.)
IS_SERVERLESS = bool(os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"))

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA_DIR = REPO_ROOT / "data"
DEFAULT_DB_PATH = DEFAULT_DATA_DIR / "agri_system.db"

# Allow explicit override via DB_PATH or DATABASE_PATH
env_db_path = os.environ.get("DB_PATH") or os.environ.get("DATABASE_PATH")

if env_db_path:
    DB_PATH = Path(env_db_path)
    DB_DIR = DB_PATH.parent
elif IS_SERVERLESS:
    # On Vercel serverless functions, the root filesystem is read-only.
    # /tmp is the only writable directory.
    DB_DIR = Path("/tmp") / "agrosetu_data"
    DB_PATH = DB_DIR / "agri_system.db"
else:
    DB_DIR = DEFAULT_DATA_DIR
    DB_PATH = DEFAULT_DB_PATH

try:
    DB_DIR.mkdir(parents=True, exist_ok=True)
except OSError:
    pass

def ensure_database_ready():
    """Ensures database file exists and is accessible. Copies seed DB to /tmp if in serverless."""
    if IS_SERVERLESS and not DB_PATH.exists():
        try:
            DB_DIR.mkdir(parents=True, exist_ok=True)
            if DEFAULT_DB_PATH.exists():
                shutil.copy2(str(DEFAULT_DB_PATH), str(DB_PATH))
        except Exception as e:
            print(f"Warning copying seed database to /tmp: {e}")

ensure_database_ready()

def get_db_connection():
    """Returns a SQLite connection with row factory set to dict-like rows."""
    ensure_database_ready()
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

    # Pan-India Fleet Vehicles & Coordinates for ALL farmers across India
    national_vehicles = [
        ("MH-15-EG-4412", "Refrigerated Cold Van (2.5T)", 2500, 24.0, "Gajanan Jadhav", "9822456781", "Nashik Hub, Maharashtra", 19.9975, 73.7898),
        ("MH-12-PQ-8901", "Mini-Truck Tata 407 (3.5T)", 3500, 18.5, "Santosh Shinde", "9890123987", "Pune Market Yard, Maharashtra", 18.5204, 73.8567),
        ("MH-17-BC-5520", "3-Wheeler Heavy Tempo (1.2T)", 1200, 14.0, "Pravin More", "9765432109", "Sangamner Center, Maharashtra", 19.5761, 74.2070),
        ("MH-16-AY-7734", "10T Eicher Logistics Lorry", 10000, 32.0, "Dnyaneshwar Gaikwad", "9821876543", "Ahmednagar Hub, Maharashtra", 19.0948, 74.7480),
        ("MH-11-DF-2299", "Insulated Cold Container (4T)", 4000, 26.0, "Sunil Pawar", "9834567890", "Satara Depot, Maharashtra", 17.6805, 74.0183),
        ("PB-10-CZ-9911", "Tata 407 Reefer Van (3.5T)", 3500, 22.0, "Harbhajan Gill", "9814123456", "Ludhiana Granary Depot, Punjab", 30.9010, 75.8573),
        ("HR-05-MK-3420", "Insulated Cold Van (4T)", 4000, 24.0, "Rajender Malik", "9896123456", "Karnal Agro Center, Haryana", 29.6857, 76.9905),
        ("DL-1L-AA-3344", "16T Heavy Multi-Axle Truck", 16000, 38.0, "Harpreet Singh", "9811223344", "Delhi Azadpur Terminal, Delhi", 28.7126, 77.1740),
        ("MP-09-GF-8812", "Eicher Pro 6-Wheeler (7.5T)", 7500, 28.0, "Mukesh Yadav", "9826112233", "Indore Krishi Mandi, MP", 22.7196, 75.8577),
        ("MP-04-TR-6231", "Tata 407 Cold Carrier (3T)", 3000, 21.0, "Ghanshyam Gurjar", "9826123456", "Bhopal Karond Mandi, MP", 23.2599, 77.4126),
        ("GJ-06-AX-4512", "Eicher Pro Reefer (4.5T)", 4500, 25.0, "Pravinbhai Shah", "9825123456", "Vadodara / Anand Hub, Gujarat", 22.3072, 73.1812),
        ("KA-04-BL-8877", "Ashok Leyland Reefer (5T)", 5000, 26.0, "Basavaraj Patil", "9845123456", "Bengaluru Yeshwanthpur APMC, Karnataka", 12.9716, 77.5946),
        ("AP-07-TJ-5544", "Tata 407 Spices Express (3.5T)", 3500, 22.0, "Raghava Rao", "9848123456", "Guntur Spices Yard, Andhra Pradesh", 16.3067, 80.4365)
    ]
    for v in national_vehicles:
        v_no, v_type, v_cap, v_rate, v_drv, v_ph, v_loc, v_lat, v_lon = v
        existing = cursor.execute("SELECT id FROM vehicles WHERE vehicle_no = ?", (v_no,)).fetchone()
        if existing:
            cursor.execute("UPDATE vehicles SET lat = ?, lon = ?, current_location = ? WHERE vehicle_no = ?;", (v_lat, v_lon, v_loc, v_no))
        else:
            cursor.execute("""
            INSERT INTO vehicles (vehicle_no, vehicle_type, capacity_kg, per_km_rate, driver_name, driver_phone, current_location, status, lat, lon)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'Available', ?, ?);
            """, (v_no, v_type, v_cap, v_rate, v_drv, v_ph, v_loc, v_lat, v_lon))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print(f"Database successfully initialized at: {DB_PATH}")
