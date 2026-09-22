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

    print("Cleared existing tables. Inserting fresh nationwide seed data...")

    # 1. Seed Farmers / FPOs Across India
    farmers_data = [
        # Western India (Maharashtra - Original Problem Statement)
        ("Ramesh Patil", "Nashik Sahyadri Farmer Producer Co.", "9822014521", "Nashik", "Maharashtra", "Dindori Road, Nashik", 4.9),
        ("Sunita Shinde", "Sangamner Agro FPO", "9850123490", "Sangamner", "Maharashtra", "Akole By-pass, Sangamner", 4.8),
        ("Balasaheb Gadakh", "Ahmednagar Krushi Vikas Samiti", "9860341278", "Ahmednagar", "Maharashtra", "Rahuri Farm Colony, Ahmednagar", 4.7),
        ("Vitthalrao Kadam", "Pune Peri-Urban Vegetable Growers", "9890456123", "Pune", "Maharashtra", "Khadakwasla Basin, Pune", 4.9),
        ("Anand Bhosale", "Satara Hill-Produce Producer Co.", "9823789012", "Satara", "Maharashtra", "Wai Tehsil, Satara", 4.8),
        ("Mahesh Deshmukh", "Godavari Valley Farmers Group", "9422567890", "Nashik", "Maharashtra", "Pimpalgaon Baswant, Nashik", 4.9),
        
        # North India (Punjab, UP, Haryana, Rajasthan)
        ("Gurpreet Singh", "Malwa Golden Grain FPO", "9814012345", "Ludhiana", "Punjab", "Samrala Road, Ludhiana", 4.9),
        ("Ramakant Yadav", "Kashi Ganga Agro Producer Co.", "9415098765", "Varanasi", "Uttar Pradesh", "Rohania Mandi Road, Varanasi", 4.8),
        ("Rajender Malik", "Karnal Basmati Rice Growers", "9812034567", "Karnal", "Haryana", "GT Road Agro Hub, Karnal", 4.9),
        ("Kailash Choudhary", "Jaipur Organic Millets FPO", "9414076543", "Jaipur", "Rajasthan", "Chomu Mandi, Jaipur", 4.7),
        
        # Central India (Madhya Pradesh)
        ("Shivraj Chouhan", "Malwa Soyabean & Wheat Producer Co.", "9826011223", "Indore", "Madhya Pradesh", "Sanwer Road, Indore", 4.9),
        ("Mangilal Patidar", "Ujjain Krishi Kalyan FPO", "9827055443", "Ujjain", "Madhya Pradesh", "Agar Road, Ujjain", 4.8),
        
        # Gujarat
        ("Hasmukh Patel", "Charotar Dairy & Agro Cooperative", "9825033221", "Anand", "Gujarat", "Amul Dairy Road, Anand", 4.9),
        
        # South India (Andhra Pradesh, Karnataka, Tamil Nadu)
        ("Venkat Reddy", "Guntur Mirchi & Spices FPO", "9848012399", "Guntur", "Andhra Pradesh", "Mirchi Yard, Guntur", 4.9),
        ("Basavaraj Gowda", "Cauvery Basin Organic Farmers", "9448099881", "Mysuru", "Karnataka", "Nanjangud Agro Ring Rd, Mysuru", 4.8)
    ]
    cursor.executemany("""
    INSERT INTO farmers (name, fpo_name, phone, city, state, address, rating)
    VALUES (?, ?, ?, ?, ?, ?, ?);
    """, farmers_data)

    # 2. Seed Products / Crops Across India
    today = datetime.date.today()
    harvest_1 = (today - datetime.timedelta(days=2)).isoformat()
    avail_1 = (today + datetime.timedelta(days=1)).isoformat()
    harvest_2 = (today - datetime.timedelta(days=1)).isoformat()
    avail_2 = today.isoformat()
    harvest_3 = (today).isoformat()
    avail_3 = (today + datetime.timedelta(days=3)).isoformat()

    products_data = [
        # Maharashtra Original Crops
        (1, "Organic Hybrid Tomato (लाल टमाटर)", "Vegetables", 3500, 3500, 38.0, "Nashik, Maharashtra", harvest_1, avail_1, "Grade A+ Export", "Farm-fresh ripe red tomatoes, firm skin, ideal for bulk retail and puree processing.", "https://images.unsplash.com/photo-1592924357228-91a4daadcfea?w=500&auto=format&fit=crop&q=60"),
        (1, "Nashik Pink Onion (गुलाबी कांदा)", "Vegetables", 8000, 8000, 28.5, "Nashik, Maharashtra", harvest_2, avail_2, "Grade A", "Sun-cured medium pungent pink onions with excellent storage life up to 4 months.", "https://images.unsplash.com/photo-1618512496248-a07fe83aa8cb?w=500&auto=format&fit=crop&q=60"),
        (2, "Sangamner Dark Green Chilli (हरी मिर्च)", "Vegetables", 1200, 1200, 48.0, "Sangamner, Maharashtra", harvest_2, avail_2, "Grade A", "Hot spicy fresh green chillies, harvested in morning dew, high capsaicin content.", "https://images.unsplash.com/photo-1588252303782-cb80119abd6d?w=500&auto=format&fit=crop&q=60"),
        (3, "Bhagwa Pomegranate (सिंदूरी अनार)", "Fruits", 2500, 2500, 110.0, "Ahmednagar, Maharashtra", harvest_1, avail_1, "Grade A+ Export", "Deep ruby-red arils, sweet soft seeds, TSS > 15 Brix. Direct orchard harvest.", "https://images.unsplash.com/photo-1541344999736-83eca272f6fc?w=500&auto=format&fit=crop&q=60"),
        (3, "Sharbati Golden Wheat (गेहूं)", "Grains", 10000, 10000, 36.0, "Ahmednagar, Maharashtra", harvest_2, avail_3, "Grade A Premium", "Lustrous heavy golden grains, high protein gluten profile for soft rotis.", "https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?w=500&auto=format&fit=crop&q=60"),
        (4, "Green Bell Pepper / Capsicum (शिमला मिर्च)", "Vegetables", 1800, 1800, 52.0, "Pune, Maharashtra", harvest_3, avail_2, "Polyhouse Grade A", "Crisp, thick-walled green capsicum cultivated under shaded polyhouse in Pune rural.", "https://images.unsplash.com/photo-1563565375-f3fdfdbefa83?w=500&auto=format&fit=crop&q=60"),
        (4, "Fresh Pune Palak & Methi (पालक/मेथी)", "Vegetables", 850, 850, 22.0, "Pune, Maharashtra", harvest_3, avail_2, "Grade A", "Tender pesticide-tested green leafy bundles, freshly cut.", "https://images.unsplash.com/photo-1576045057995-568f588f82fb?w=500&auto=format&fit=crop&q=60"),
        (5, "Mahabaleshwar Fresh Strawberries (स्ट्रॉबेरी)", "Fruits", 900, 900, 190.0, "Satara, Maharashtra", harvest_3, avail_2, "Grade A+ Cold Chain", "Sweet fragrant mountain strawberries packed in ventilated punnets, cold-chain ready.", "https://images.unsplash.com/photo-1464965911861-746a04b4bca6?w=500&auto=format&fit=crop&q=60"),
        (5, "Satara Fresh Ginger / Adrak (अदरक)", "Vegetables", 1500, 1500, 75.0, "Satara, Maharashtra", harvest_1, avail_1, "Grade A", "Spicy aromatic thick rhizome ginger with zero soil residue, high essential oil.", "https://images.unsplash.com/photo-1615485290382-441e4d049cb5?w=500&auto=format&fit=crop&q=60"),
        (6, "Thompson Seedless Grapes (हरे अंगूर)", "Fruits", 4000, 4000, 85.0, "Nashik, Maharashtra", harvest_2, avail_3, "Export Quality", "Crisp sweet green grapes with natural bloom, GlobalGAP certified harvest.", "https://images.unsplash.com/photo-1537640538966-79f369143f8f?w=500&auto=format&fit=crop&q=60"),
        
        # Pan-India Produce
        (7, "Punjab Traditional Basmati 1121 Rice (बासमती चावल)", "Grains", 12000, 12000, 68.0, "Ludhiana, Punjab", harvest_1, avail_2, "Aged Export Grade", "Extra-long grain aromatic basmati rice aged 12 months, cooking elongation > 2.0x.", "https://images.unsplash.com/photo-1586201375761-83865001e31c?w=500&auto=format&fit=crop&q=60"),
        (8, "Banarasi Desi Cauliflower & Pea (गोभी व मटर)", "Vegetables", 3000, 3000, 32.0, "Varanasi, Uttar Pradesh", harvest_2, avail_2, "Grade A Mandi", "Freshly picked snow-white curds and sweet green peas from the Ganga alluvial basin.", "https://images.unsplash.com/photo-1568584711075-3d021a7c3ca3?w=500&auto=format&fit=crop&q=60"),
        (9, "Karnal Pure Pusa Basmati Paddy (धान)", "Grains", 15000, 15000, 42.0, "Karnal, Haryana", harvest_3, avail_3, "Grade A Farm Direct", "Clean dried golden paddy direct from Haryana farm gates, moisture 12%.", "https://images.unsplash.com/photo-1536304993881-ff6e9eefa2a6?w=500&auto=format&fit=crop&q=60"),
        (10, "Rajasthan Organic Bajra / Pearl Millet (बाजरा)", "Grains", 8000, 8000, 26.0, "Jaipur, Rajasthan", harvest_2, avail_3, "Certified Organic", "Nutrient-dense drought-resistant pearl millet, high iron and zinc content.", "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=500&auto=format&fit=crop&q=60"),
        (11, "Malwa Bold Yellow Soyabean (सोयाबीन)", "Cash Crops", 10000, 10000, 46.5, "Indore, Madhya Pradesh", harvest_1, avail_2, "Grade A Oilseed", "Cleaned bold yellow soyabean with 18.5% oil content and high protein.", "https://images.unsplash.com/photo-1599940824399-b87987ceb72a?w=500&auto=format&fit=crop&q=60"),
        (12, "Ujjain Desi Garlic / Lahsun (देसी लहसुन)", "Vegetables", 4000, 4000, 120.0, "Ujjain, Madhya Pradesh", harvest_1, avail_2, "Grade A Storage", "Pungent white cloves, thoroughly dried, ideal for commercial paste and spices.", "https://images.unsplash.com/photo-1540148426945-6cf22a6b2383?w=500&auto=format&fit=crop&q=60"),
        (13, "Anand Farm-Fresh Chilled Cow Milk (दूध)", "Dairy", 5000, 5000, 56.0, "Anand, Gujarat", harvest_3, avail_2, "Fat 4.2% SNF 8.5%", "Direct morning dairy milking, chilled to 4 deg C immediately, bulk milk tankers.", "https://images.unsplash.com/photo-1550583724-b2692b85b150?w=500&auto=format&fit=crop&q=60"),
        (14, "Guntur Teja Spicy Red Chilli (तेजा लाल मिर्च)", "Spices", 6000, 6000, 160.0, "Guntur, Andhra Pradesh", harvest_1, avail_1, "Grade A Export", "World-renowned high SHU pungent dried red chillies, stalkless option available.", "https://images.unsplash.com/photo-1563865436874-9aef32095fad?w=500&auto=format&fit=crop&q=60"),
        (15, "Mysuru Nanjangud Rasabale Banana (केला)", "Fruits", 3200, 3200, 45.0, "Mysuru, Karnataka", harvest_2, avail_2, "GI Tag Certified", "Unique sweet aroma and delicate flavor, Geographical Indication tagged fruit.", "https://images.unsplash.com/photo-1571771894821-ce9b6c11b08e?w=500&auto=format&fit=crop&q=60")
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
        ("MH-11-DF-2299", "Insulated Cold Container (4T)", 4000, 26.0, "Sunil Pawar", "9834567890", "Satara Depot", "Available"),
        ("DL-1L-AA-3344", "16T Heavy Multi-Axle Truck", 16000, 38.0, "Harpreet Singh", "9811223344", "Delhi Azadpur Mandi", "Available"),
        ("MP-09-GF-8812", "Eicher Pro 6-Wheeler (7.5T)", 7500, 28.0, "Mukesh Yadav", "9826112233", "Indore Krishi Mandi", "Available")
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
        ("ORD-2026-004", 8, "Mahabaleshwar Fresh Strawberries", "Anand Bhosale", "Nitin Salunkhe (Dessert Kitchen)", "9855443322", "nitin@desserts.in", "Koregaon Park North Main Rd", "Pune", 150, 190.0, 28500.0, "Scheduled", "Paid", "UPI", "UPI-ICICI-665544"),
        ("ORD-2026-005", 11, "Punjab Traditional Basmati 1121 Rice", "Gurpreet Singh", "Aman Grover (Delhi Mega Grocery)", "9811002233", "aman@delhigrocery.com", "Chandni Chowk Grain Market", "Delhi", 3000, 68.0, 204000.0, "Confirmed", "Paid", "NetBanking", "NEFT-PNB-778899")
    ]
    cursor.executemany("""
    INSERT INTO orders (
        order_number, product_id, product_name, farmer_name, buyer_name,
        buyer_phone, buyer_email, delivery_address, delivery_city,
        quantity_kg, price_per_kg, total_amount, order_status,
        payment_status, payment_method, transaction_id
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, orders_data)

    # 5. Seed Shipments
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
            "Balasaheb Farm, Rahuri, Ahmednagar", "Rahuri Krishi Hub", "Bremen Circle Cold Store, Pune",
            1, "MH-15-EG-4412", "Gajanan Jadhav", "9822456781",
            "Delivered", 145.0, 3.2, 3480.0,
            "Delivered at 10:15 AM"
        ),
        (
            "SHIP-MAHA-103", 2, "Nashik Pink Onion (Jute Sacks)", 2000.0,
            "Lasalgaon Mandi Yard, Nashik", "Lasalgaon Bulk Depot", "Turbhe Market Yard, Navi Mumbai",
            4, "MH-16-AY-7734", "Dnyaneshwar Gaikwad", "9821876543",
            "Scheduled", 185.0, 4.5, 5920.0,
            "Tomorrow 06:00 AM"
        ),
        (
            "SHIP-NORTH-201", 5, "Punjab Basmati Rice (Aged Sacks)", 3000.0,
            "Samrala Farm Depot, Ludhiana", "Ludhiana Agro Aggregator", "Azadpur Mandi Shed 4, Delhi",
            6, "DL-1L-AA-3344", "Harpreet Singh", "9811223344",
            "In Transit", 315.0, 6.2, 11970.0,
            "Tomorrow 08:30 AM"
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

    # 6. Seed Demand History (360 Records for AI Engine)
    crops_cities = [
        ("Tomato", "Pune", 35.0, 1000.0),
        ("Tomato", "Mumbai", 42.0, 1600.0),
        ("Tomato", "Delhi", 38.0, 2200.0),
        ("Onion", "Mumbai", 28.0, 1800.0),
        ("Onion", "Pune", 26.0, 1100.0),
        ("Wheat", "Indore", 32.0, 2500.0),
        ("Rice", "Delhi", 60.0, 3000.0),
        ("Pomegranate", "Pune", 110.0, 800.0),
        ("Green Chilli", "Ahmedabad", 50.0, 950.0)
    ]
    history_records = []
    base_date = datetime.date.today() - datetime.timedelta(days=40)

    for crop, city, avg_p, base_d in crops_cities:
        for day_offset in range(40):
            cur_date = base_date + datetime.timedelta(days=day_offset)
            season = "Monsoon" if day_offset < 15 else ("Kharif Harvest" if day_offset < 30 else "Winter")
            weather = "Moderate Rain" if (day_offset % 7 == 0) else "Sunny / Clear"
            rand_factor = 0.88 + 0.24 * (day_offset % 9) / 9.0
            actual_demand = round(base_d * rand_factor, 1)
            actual_sales = round(actual_demand * random.uniform(0.92, 0.98), 1)

            history_records.append((
                crop, city, cur_date.isoformat(),
                actual_demand, actual_sales, avg_p,
                season, weather, "Historical Mandi Records"
            ))

    cursor.executemany("""
    INSERT INTO demand_history (
        crop_name, city, record_date, demand_kg, sales_kg, avg_price_per_kg,
        season, weather, notes
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, history_records)

    conn.commit()
    conn.close()
    print("All nationwide seed data successfully written and committed to SQLite database!")

if __name__ == "__main__":
    seed_all()
