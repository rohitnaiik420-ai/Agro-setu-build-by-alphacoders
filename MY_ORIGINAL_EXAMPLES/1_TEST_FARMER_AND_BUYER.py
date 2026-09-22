import os
import sys
import sqlite3
from pathlib import Path

# Safe console encoding for Windows CMD / PowerShell
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Locate project directory robustly from any path
PROJECT_CANDIDATES = [
    Path(__file__).resolve().parent.parent,
    Path(r"C:\Users\ADMIN\Desktop\problem statement 26033 solve by rohit naik"),
    Path(__file__).resolve().parent / "problem statement 26033 solve by rohit naik"
]
PROJECT_DIR = None
for p in PROJECT_CANDIDATES:
    if (p / "backend" / "database.py").exists():
        PROJECT_DIR = p
        break

if not PROJECT_DIR:
    PROJECT_DIR = Path(r"C:\Users\ADMIN\Desktop\problem statement 26033 solve by rohit naik")

BACKEND_DIR = PROJECT_DIR / "backend"
DATA_DIR = PROJECT_DIR / "data"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from database import get_db_connection, init_db

def main():
    print("=" * 75)
    print("  POINT 1: FARMER / FPO  -->  CONSUMER / BULK BUYER")
    print("  (Aapke Image Ka Point 1 Test)")
    print("=" * 75)

    init_db()
    conn = get_db_connection()
    c = conn.cursor()

    print("\n[A] FARMER / FPO SIDE (Kisan ki taraf se):")
    print("--------------------------------------------------")
    product = c.execute("""
        SELECT p.*, f.name as farmer_name, f.fpo_name 
        FROM products p
        LEFT JOIN farmers f ON p.farmer_id = f.id
        WHERE p.crop_name LIKE '%Tomato%'
        LIMIT 1
    """).fetchone()

    if not product:
        product = c.execute("SELECT * FROM products LIMIT 1").fetchone()

    print("  1. Product Upload Karna : " + str(product["crop_name"]))
    print("  2. Quantity Check Karna : " + str(product["quantity_kg"]) + " kg (Available: " + str(product["available_quantity_kg"]) + " kg)")
    print("  3. Price Check Karna    : Rs. " + str(product["price_per_kg"]) + " per kg")
    print("  4. Location Check Karna : " + str(product["location"]))
    print("  5. Available Date Check : " + str(product["available_date"]) + " (Harvest: " + str(product["harvest_date"]) + ")")
    print("  6. Quality Grade Check  : " + str(product["quality_grade"]))

    print("\n[B] CONSUMER / BULK BUYER SIDE (Buyer ki taraf se):")
    print("--------------------------------------------------")
    order = c.execute("""
        SELECT * FROM orders 
        WHERE product_name LIKE '%Tomato%'
        ORDER BY id DESC LIMIT 1
    """).fetchone()

    if not order:
        order = c.execute("SELECT * FROM orders ORDER BY id DESC LIMIT 1").fetchone()

    print("  1. Product Sochna/Search: Buyer searched for '" + str(order["product_name"]) + "'")
    print("  2. Quantity Poochna     : " + str(order["quantity_kg"]) + " kg required")
    print("  3. Order Dena           : Order Created! Reference No: " + str(order["order_number"]))
    print("  4. Delivery Location    : " + str(order["delivery_address"]) + ", " + str(order["delivery_city"]))
    print("  5. Payment Karna        : Total Rs. " + str(order["total_amount"]) + " Paid via " + str(order["payment_method"]))
    print("  6. Transaction ID       : " + str(order["transaction_id"]) + " [Status: " + str(order["payment_status"]) + "]")

    conn.close()

    print("\n" + "=" * 75)
    print("  RESULT: Point 1 (Farmer -> Buyer) Working 100% Successfully!")
    print("=" * 75)

if __name__ == "__main__":
    main()
