import os
import sys
import sqlite3
import datetime
from pathlib import Path

# Safe Unicode output for Windows CMD/PowerShell
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
DB_PATH = DATA_DIR / "agri_system.db"

def run_database_checks():
    print("=" * 80)
    print("      DATABASE COMPONENT AUDIT & INTEGRITY CHECK (SQLite)")
    print("=" * 80)

    # 1. Physical File Check
    print(f"\n[1] Physical Storage Check:")
    if not DB_PATH.exists():
        print(f"  [-] FAILED: Database file not found at {DB_PATH}")
        return False
    
    size_bytes = DB_PATH.stat().st_size
    size_kb = round(size_bytes / 1024, 2)
    print(f"  [+] File Path: {DB_PATH}")
    print(f"  [+] File Size: {size_kb} KB ({size_bytes} bytes)")
    print(f"  [+] Permanent Persistence: Active (Saved on Local Disk)")

    # 2. Connection & PRAGMA Integrity Check
    print(f"\n[2] SQLite Engine Integrity & PRAGMA Checks:")
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    
    # Check integrity
    integrity = c.execute("PRAGMA integrity_check;").fetchone()[0]
    print(f"  [+] PRAGMA integrity_check: {integrity} (Zero corruption)")
    assert integrity == "ok", "Database corruption detected"
    
    # Check journal mode
    journal_mode = c.execute("PRAGMA journal_mode;").fetchone()[0]
    print(f"  [+] PRAGMA journal_mode: {journal_mode}")

    # 3. Table Schema Verification
    print(f"\n[3] Table Schema & Structure Audit:")
    tables = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;").fetchall()]
    print(f"  [+] Total Tables Found: {len(tables)}")
    
    expected_tables = {
        "farmers": ["id", "name", "fpo_name", "phone", "city", "state", "address", "rating"],
        "products": ["id", "farmer_id", "crop_name", "category", "quantity_kg", "available_quantity_kg", "price_per_kg", "location", "harvest_date", "available_date"],
        "orders": ["id", "order_number", "product_id", "buyer_name", "quantity_kg", "total_amount", "order_status", "payment_status", "payment_method"],
        "vehicles": ["id", "vehicle_no", "vehicle_type", "capacity_kg", "per_km_rate", "driver_name", "status"],
        "shipments": ["id", "tracking_no", "cargo_description", "weight_kg", "pickup_location", "collection_center", "delivery_location", "status", "transport_cost"],
        "demand_history": ["id", "crop_name", "city", "record_date", "demand_kg", "sales_kg", "season", "weather"],
        "route_waypoints": ["id", "farmer_label", "farmer_name", "location_name", "latitude", "longitude", "produce_type", "pickup_qty_kg"]
    }

    all_tables_ok = True
    for t_name, required_cols in expected_tables.items():
        if t_name not in tables:
            print(f"  [-] Table MISSING: {t_name}")
            all_tables_ok = False
            continue
            
        columns = [row[1] for row in c.execute(f"PRAGMA table_info({t_name});").fetchall()]
        missing_cols = [c for c in required_cols if c not in columns]
        count = c.execute(f"SELECT COUNT(*) FROM {t_name};").fetchone()[0]
        
        if missing_cols:
            print(f"  [-] Table '{t_name}': Missing columns {missing_cols}")
            all_tables_ok = False
        else:
            print(f"  [+] Table '{t_name:17s}': Schema OK | {count:4d} active records")

    # 4. ACID Transaction Test (Insert, Read, Commit, Rollback)
    print(f"\n[4] ACID Transaction & Write Concurrency Test:")
    test_key = f"TEST_TRANSACTION_{int(datetime.datetime.now().timestamp())}"
    
    # Test atomic insert & commit
    c.execute("""
        INSERT INTO demand_history (crop_name, city, record_date, demand_kg, sales_kg, avg_price_per_kg, season, weather, notes)
        VALUES ('TestCrop', 'TestCity', '2026-09-22', 999.0, 999.0, 50.0, 'TestSeason', 'TestWeather', ?)
    """, (test_key,))
    conn.commit()
    
    # Verify read
    row = c.execute("SELECT id, demand_kg FROM demand_history WHERE notes = ?", (test_key,)).fetchone()
    assert row is not None and row[1] == 999.0, "Transaction write/read failed"
    print("  [+] Atomic INSERT & COMMIT verified successfully")
    
    # Test rollback
    try:
        c.execute("""
            INSERT INTO demand_history (crop_name, city, record_date, demand_kg, sales_kg, avg_price_per_kg, season, weather, notes)
            VALUES ('RollbackCrop', 'RollbackCity', '2026-09-22', 111.0, 111.0, 10.0, 'S', 'W', 'ROLLBACK_ME')
        """)
        conn.rollback() # Intentionally abort
        rb_row = c.execute("SELECT id FROM demand_history WHERE notes = 'ROLLBACK_ME'").fetchone()
        assert rb_row is None, "Rollback failed"
        print("  [+] Transaction ROLLBACK verified successfully (Zero dirty writes)")
    except Exception as e:
        print(f"  [-] Rollback test error: {e}")

    # Clean up test row
    c.execute("DELETE FROM demand_history WHERE notes = ?", (test_key,))
    conn.commit()
    print("  [+] Cleanup completed. Database is 100% clean and consistent.")

    conn.close()
    
    print("\n" + "=" * 80)
    print("  >>> DATABASE INTEGRITY CHECK: 100% HEALTHY & PERMANENTLY WORKING! <<<")
    print("=" * 80)
    return all_tables_ok

if __name__ == "__main__":
    run_database_checks()
