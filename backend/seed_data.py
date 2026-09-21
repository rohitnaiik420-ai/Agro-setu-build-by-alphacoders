import datetime
import random
from database import get_db_connection, init_db

def seed_all():
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    # Clear existing data to ensure clean reproducible state
    tables = ["farmers", "products", "orders", "vehicles", "shipments", "demand_history", "route_waypoints"]
    for t in tables:
        cursor.execute(f"DELETE FROM {t};")
        cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{t}';")

    print("Cleared existing tables. Inserting fresh seed data...")

    # 1. Seed Farmers / FPOs
    farmers_data = [
        ("Ramesh Patil", "Nashik Sahyadri Farmer Producer Co.", "9822014521", "Nashik", "Dindori Road, Nashik", 4.9),
        ("Sunita Shinde", "Sangamner Agro FPO", "9850123490", "Sangamner", "Akole By-pass, Sangamner", 4.8),
        ("Balasaheb Gadakh", "Ahmednagar Krushi Vikas Samiti", "9860341278", "Ahmednagar", "Rahuri Farm Colony, Ahmednagar", 4.7),
        ("Vitthalrao Kadam", "Pune Peri-Urban Vegetable Growers", "9890456123", "Pune", "Khadakwasla Basin, Pune", 4.9),
        ("Anand Bhosale", "Satara Hill-Produce Producer Co.", "9823789012", "Satara", "Wai Tehsil, Satara", 4.8),
        ("Mahesh Deshmukh", "Godavari Valley Farmers Group", "9422567890", "Nashik", "Pimpalgaon Baswant, Nashik", 4.9)
    ]
    cursor.executemany("""
    INSERT INTO farmers (name, fpo_name, phone, city, address, rating)
    VALUES (?, ?, ?, ?, ?, ?);
    """, farmers_data)

    # 2. Seed Products / Crops
    today = datetime.date.today()
    harvest_1 = (today - datetime.timedelta(days=2)).isoformat()
    avail_1 = (today + datetime.timedelta(days=1)).isoformat()
    harvest_2 = (today - datetime.timedelta(days=1)).isoformat()
    avail_2 = today.isoformat()
    harvest_3 = (today).isoformat()
    avail_3 = (today + datetime.timedelta(days=3)).isoformat()

    products_data = [
        (1, "Organic Hybrid Tomato (लाल टमाटर)", "Vegetables", 3500, 3500, 38.0, "Nashik", harvest_1, avail_1, "Grade A+ Export", "Farm-fresh ripe red tomatoes, firm skin, ideal for bulk retail and puree processing.", "https://images.unsplash.com/photo-1592924357228-91a4daadcfea?w=500&auto=format&fit=crop&q=60"),
        (1, "Nashik Pink Onion (गुलाबी कांदा)", "Vegetables", 8000, 8000, 28.5, "Nashik", harvest_2, avail_2, "Grade A", "Sun-cured medium pungent pink onions with excellent storage life up to 4 months.", "https://images.unsplash.com/photo-1618512496248-a07fe83aa8cb?w=500&auto=format&fit=crop&q=60"),
        (2, "Sangamner Dark Green Chilli (हरी मिर्च)", "Vegetables", 1200, 1200, 48.0, "Sangamner", harvest_2, avail_2, "Grade A", "Hot spicy fresh green chillies, harvested in morning dew, high capsaicin content.", "https://images.unsplash.com/photo-1588252303782-cb80119abd6d?w=500&auto=format&fit=crop&q=60"),
        (3, "Bhagwa Pomegranate (सिंदूरी अनार)", "Fruits", 2500, 2500, 110.0, "Ahmednagar", harvest_1, avail_1, "Grade A+ Export", "Deep ruby-red arils, sweet soft seeds, TSS > 15 Brix. Direct orchard harvest.", "https://images.unsplash.com/photo-1541344999736-83eca272f6fc?w=500&auto=format&fit=crop&q=60"),
        (3, "Sharbati Golden Wheat (गेहूं)", "Grains", 10000, 10000, 36.0, "Ahmednagar", harvest_2, avail_3, "Grade A Premium", "Lustrous heavy golden grains, high protein gluten profile for soft rotis.", "https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?w=500&auto=format&fit=crop&q=60"),
        (4, "Green Bell Pepper / Capsicum (शिमला मिर्च)", "Vegetables", 1800, 1800, 52.0, "Pune", harvest_3, avail_2, "Polyhouse Grade A", "Crisp, thick-walled green capsicum cultivated under shaded polyhouse in Pune rural.", "https://images.unsplash.com/photo-1563565375-f3fdfdbefa83?w=500&auto=format&fit=crop&q=60"),
        (4, "Fresh Pune Palak & Methi (पालक/मेथी)", "Vegetables", 850, 850, 22.0, "Pune", harvest_3, avail_2, "Grade A", "Tender pesticide-tested green leafy bundles, freshly cut.", "https://images.unsplash.com/photo-1576045057995-568f588f82fb?w=500&auto=format&fit=crop&q=60"),
        (5, "Mahabaleshwar Fresh Strawberries (स्ट्रॉबेरी)", "Fruits", 900, 900, 190.0, "Satara", harvest_3, avail_2, "Grade A+ Cold Chain", "Sweet fragrant mountain strawberries packed in ventilated punnets, cold-chain ready.", "https://images.unsplash.com/photo-1464965911861-746a04b4bca6?w=500&auto=format&fit=crop&q=60"),
        (5, "Satara Fresh Ginger / Adrak (अदरक)", "Vegetables", 1500, 1500, 75.0, "Satara", harvest_1, avail_1, "Grade A", "Spicy aromatic thick rhizome ginger with zero soil residue, high essential oil.", "https://images.unsplash.com/photo-1615485290382-441e4d049cb5?w=500&auto=format&fit=crop&q=60"),
        (6, "Thompson Seedless Grapes (हरे अंगूर)", "Fruits", 4000, 4000, 85.0, "Nashik", harvest_2, avail_3, "Export Quality", "Crisp sweet green grapes with natural bloom, GlobalGAP certified harvest.", "https://images.unsplash.com/photo-1537640538966-79f369143f8f?w=500&auto=format&fit=crop&q=60")
    ]
    cursor.executemany("""
    INSERT INTO products (
        farmer_id, crop_name, category, quantity_kg, available_quantity_kg,
        price_per_kg, location, harvest_date, available_date,
        quality_grade, description, image_url
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, products_data)

    # 3. Seed Vehicles (Fleet)
    vehicles_data = [
        ("MH-15-EG-4412", "Refrigerated Cold Van (2.5T)", 2500, 24.0, "Gajanan Jadhav", "9822456781", "Nashik Hub", "Available"),
        ("MH-12-PQ-8901", "Mini-Truck Tata 407 (3.5T)", 3500, 18.5, "Santosh Shinde", "9890123987", "Pune Market Yard", "On Route"),
        ("MH-17-BC-5520", "3-Wheeler Heavy Tempo (1.2T)", 1200, 14.0, "Pravin More", "9765432109", "Sangamner Center", "Available"),
        ("MH-16-AY-7734", "10T Eicher Logistics Lorry", 10000, 32.0, "Dnyaneshwar Gaikwad", "9821876543", "Ahmednagar Hub", "Available"),
        ("MH-11-DF-2299", "Insulated Cold Container (4T)", 4000, 26.0, "Sunil Pawar", "9834567890", "Satara Depot", "Available")
    ]
    cursor.executemany("""
    INSERT INTO vehicles (vehicle_no, vehicle_type, capacity_kg, per_km_rate, driver_name, driver_phone, current_location, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    """, vehicles_data)

    # 4. Seed Orders & Payments
    orders_data = [
        ("ORD-2026-001", 1, "Organic Hybrid Tomato", "Ramesh Patil", "Priya Kulkarni (Reliance Fresh Pune)", "9820011223", "priya@reliancefresh.in", "Market Yard Sector 4, Gultekdi", "Pune", 500, 38.0, 19000.0, "In Transit", "Paid", "UPI", "UPI-HDFC-998811"),
        ("ORD-2026-002", 2, "Nashik Pink Onion", "Ramesh Patil", "Kishore Jain (Vashi APMC Wholesale)", "9819876543", "kjain@apmc.org", "Turbhe Market, Sector 19", "Navi Mumbai", 2000, 28.5, 57000.0, "Confirmed", "Paid", "NetBanking", "NEFT-SBI-442211"),
        ("ORD-2026-003", 4, "Bhagwa Pomegranate", "Balasaheb Gadakh", "Deepak Chopra (Fresh Fruit Mart)", "9822334455", "deepak@freshmart.com", "Aundh Road, Bremen Circle", "Pune", 350, 110.0, 38500.0, "Delivered", "Paid", "Card", "TXN-CARD-881203"),
        ("ORD-2026-004", 8, "Mahabaleshwar Fresh Strawberries", "Anand Bhosale", "Nitin Salunkhe (Dessert Kitchen)", "9855443322", "nitin@desserts.in", "Koregaon Park North Main Rd", "Pune", 150, 190.0, 28500.0, "Scheduled", "Paid", "UPI", "UPI-ICICI-665544")
    ]
    cursor.executemany("""
    INSERT INTO orders (
        order_number, product_id, product_name, farmer_name, buyer_name,
        buyer_phone, buyer_email, delivery_address, delivery_city,
        quantity_kg, price_per_kg, total_amount, order_status,
        payment_status, payment_method, transaction_id
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, orders_data)

    # 5. Seed Shipments (Matching problem statement: Farmer, Nashik -> Collection Center -> Pune Buyer)
    shipments_data = [
        (
            "SHIP-MAHA-101", 1, "Organic Hybrid Tomatoes (Bulk Crates)", 500.0,
            "Farmer Farm, Nashik", "Nashik Collection Center (Pimpalgaon)", "Gultekdi Market Yard, Pune Buyer",
            2, "MH-12-PQ-8901", "Santosh Shinde", "9890123987",
            "In Transit", 212.0, 4.8, 3922.0,
            (datetime.datetime.now() + datetime.timedelta(hours=2)).strftime("%I:%M %p Today")
        ),
        (
            "SHIP-MAHA-102", 3, "Bhagwa Pomegranates (Cold Packed)", 350.0,
            "Farmer Farm, Ahmednagar", "Rahuri Collection Depot", "Aundh Hub, Pune",
            1, "MH-15-EG-4412", "Gajanan Jadhav", "9822456781",
            "Delivered", 125.0, 2.7, 3000.0,
            "Delivered at 09:30 AM"
        ),
        (
            "SHIP-MAHA-103", 4, "Mahabaleshwar Strawberries", 150.0,
            "Farmer Farm, Satara (Wai)", "Satara Agro Center", "Koregaon Park, Pune",
            5, "MH-11-DF-2299", "Sunil Pawar", "9834567890",
            "Scheduled", 112.0, 2.5, 2912.0,
            (datetime.datetime.now() + datetime.timedelta(hours=5)).strftime("%I:%M %p Today")
        )
    ]
    cursor.executemany("""
    INSERT INTO shipments (
        tracking_no, order_id, cargo_description, weight_kg,
        pickup_location, collection_center, delivery_location,
        vehicle_id, vehicle_no, driver_name, driver_phone,
        status, distance_km, estimated_hours, transport_cost, eta_timestamp
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, shipments_data)

    # 6. Seed Route Waypoints (The 5 Farmers from problem statement!)
    waypoints_data = [
        ("Farmer A", "Ramesh Patil", "Nashik", 19.9975, 73.7898, "Tomato & Grapes", 850, 1),
        ("Farmer B", "Sunita Shinde", "Sangamner", 19.5761, 74.2070, "Green Chillies & Onion", 620, 2),
        ("Farmer C", "Balasaheb Gadakh", "Ahmednagar", 19.0948, 74.7480, "Pomegranates & Wheat", 950, 3),
        ("Farmer D", "Vitthalrao Kadam", "Pune", 18.5204, 73.8567, "Capsicum & Greens", 700, 4),
        ("Farmer E", "Anand Bhosale", "Satara", 17.6805, 74.0183, "Ginger & Strawberry", 500, 5)
    ]
    cursor.executemany("""
    INSERT INTO route_waypoints (farmer_label, farmer_name, location_name, latitude, longitude, produce_type, pickup_qty_kg, stop_order)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    """, waypoints_data)

    # 7. Seed Demand History (Multi-month trends for Pune, Mumbai, Nashik)
    crops = ["Tomato", "Onion", "Pomegranate", "Chilli"]
    cities = ["Pune", "Mumbai", "Nashik"]
    history_records = []

    for c in cities:
        for cr in crops:
            base = 1000.0 if c == "Pune" and cr == "Tomato" else random.randint(600, 1800)
            for d_offset in range(30, 0, -1):
                rec_date = (today - datetime.timedelta(days=d_offset)).isoformat()
                noise = random.uniform(-80, 110)
                demand = max(200.0, round(base + noise, 0))
                sales = round(demand * random.uniform(0.92, 0.98), 0)
                price = 35.0 + random.uniform(-4, 6)
                history_records.append((
                    cr, c, rec_date, demand, sales, round(price, 1),
                    "Monsoon", "Rainy / Cloudy", 1.2 if d_offset <= 7 else 1.0, "Verified APMC Mandi Auction data"
                ))

    cursor.executemany("""
    INSERT INTO demand_history (crop_name, city, record_date, demand_kg, sales_kg, avg_price_per_kg, season, weather, festival_factor, notes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, history_records)

    conn.commit()
    conn.close()
    print("All seed data successfully written and committed to SQLite database!")

if __name__ == "__main__":
    seed_all()
