import os
import uuid
import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, Query, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

import sys
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

try:
    from backend.database import get_db_connection, init_db, DB_PATH
    from backend.forecasting_engine import calculate_forecast
    from backend.route_optimizer import solve_route_optimization, DEFAULT_WAYPOINTS, haversine_distance, CITY_COORDINATES, get_coordinates_for_city
    from backend.seed_data import seed_all
except ImportError:
    from database import get_db_connection, init_db, DB_PATH
    from forecasting_engine import calculate_forecast
    from route_optimizer import solve_route_optimization, DEFAULT_WAYPOINTS, haversine_distance, CITY_COORDINATES, get_coordinates_for_city
    from seed_data import seed_all

# Directory setup
BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
try:
    FRONTEND_DIR.mkdir(parents=True, exist_ok=True)
except OSError:
    pass

app = FastAPI(
    title="Agro-Logistics & Marketplace Platform (Problem Statement 26033)",
    description="Integrated Farmer-Buyer Marketplace, Logistics & Fleet Tracking, AI Demand Forecasting, and Multi-stop Route Optimization",
    version="1.0.0"
)

# Enable CORS (support environment variable ALLOWED_ORIGINS if configured)
allowed_origins_env = os.environ.get("ALLOWED_ORIGINS")
if allowed_origins_env:
    allowed_origins = [o.strip() for o in allowed_origins_env.split(",") if o.strip()]
    allow_credentials = True
else:
    allowed_origins = ["*"]
    allow_credentials = False

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure DB initialized on startup
@app.on_event("startup")
def startup_event():
    init_db()
    try:
        conn = get_db_connection()
        count = conn.cursor().execute("SELECT COUNT(*) FROM farmers").fetchone()[0]
        conn.close()
        if count == 0:
            seed_all()
    except Exception as e:
        print(f"Startup DB check note: {e}")


# ==================== PYDANTIC SCHEMAS ====================

class FarmerCreateSchema(BaseModel):
    name: str
    fpo_name: Optional[str] = "Independent Farm Producer"
    phone: str
    city: str
    state: str = "Maharashtra"
    address: Optional[str] = ""
    rating: Optional[float] = 4.8

class ProductCreateSchema(BaseModel):
    farmer_id: Optional[int] = 1
    crop_name: str
    category: str = "Vegetables"
    quantity_kg: float = Field(..., gt=0)
    price_per_kg: float = Field(..., gt=0)
    location: str
    harvest_date: str
    available_date: str
    quality_grade: str = "Grade A"
    description: Optional[str] = ""
    image_url: Optional[str] = ""

class OrderCreateSchema(BaseModel):
    product_id: int
    buyer_name: str
    buyer_phone: str
    buyer_email: Optional[str] = ""
    delivery_address: str
    delivery_city: str
    quantity_kg: float = Field(..., gt=0)
    payment_method: str = "UPI"

class PaymentProcessSchema(BaseModel):
    payment_method: str = "UPI"
    transaction_id: Optional[str] = None

class ShipmentCreateSchema(BaseModel):
    order_id: Optional[int] = None
    cargo_description: str
    weight_kg: float
    pickup_location: str
    collection_center: str
    delivery_location: str
    vehicle_id: Optional[int] = None

class ShipmentStatusUpdateSchema(BaseModel):
    status: str

class BreakdownTriggerSchema(BaseModel):
    reason: Optional[str] = "Engine Overheating on NH-60 Corridor"
    breakdown_lat: Optional[float] = None
    breakdown_lon: Optional[float] = None

class RouteOptimizeRequest(BaseModel):
    waypoints: Optional[List[Dict[str, Any]]] = None
    hub: Optional[Dict[str, Any]] = None

# ==================== REST API ENDPOINTS ====================

@app.get("/api/health")
def health_check():
    return {"status": "ok", "timestamp": datetime.datetime.now().isoformat(), "project": "Problem Statement 26033 - Agro-Logistics"}

@app.get("/api/stats")
def get_dashboard_stats():
    conn = get_db_connection()
    c = conn.cursor()
    
    total_products = c.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    total_farmers = c.execute("SELECT COUNT(*) FROM farmers").fetchone()[0]
    total_orders = c.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    total_sales_val = c.execute("SELECT COALESCE(SUM(total_amount), 0) FROM orders WHERE payment_status = 'Paid'").fetchone()[0]
    active_shipments = c.execute("SELECT COUNT(*) FROM shipments WHERE status != 'Delivered'").fetchone()[0]
    active_vehicles = c.execute("SELECT COUNT(*) FROM vehicles WHERE status = 'Available'").fetchone()[0]
    
    conn.close()
    return {
        "total_products": total_products,
        "total_farmers": total_farmers,
        "total_orders": total_orders,
        "total_sales_inr": round(total_sales_val, 2),
        "active_shipments": active_shipments,
        "available_vehicles": active_vehicles
    }

# ----- 1. FARMER & BUYER MARKETPLACE -----

@app.get("/api/products")
def list_products(category: Optional[str] = None, location: Optional[str] = None, search: Optional[str] = None):
    conn = get_db_connection()
    c = conn.cursor()
    
    query = """
    SELECT p.*, f.name as farmer_name, f.fpo_name, f.phone as farmer_phone, f.rating as farmer_rating
    FROM products p
    LEFT JOIN farmers f ON p.farmer_id = f.id
    WHERE 1=1
    """
    params = []
    if category and category.lower() != "all":
        query += " AND p.category = ?"
        params.append(category)
    if location and location.lower() != "all":
        query += " AND p.location LIKE ?"
        params.append(f"%{location}%")
    if search:
        query += " AND (p.crop_name LIKE ? OR p.description LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])
        
    query += " ORDER BY p.id DESC"
    rows = c.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.post("/api/products", status_code=status.HTTP_201_CREATED)
def add_product(item: ProductCreateSchema):
    conn = get_db_connection()
    c = conn.cursor()
    
    # Check if farmer exists
    farmer = c.execute("SELECT name FROM farmers WHERE id = ?", (item.farmer_id,)).fetchone()
    if not farmer:
        # Default to first farmer if none specified
        first_farmer = c.execute("SELECT id FROM farmers LIMIT 1").fetchone()
        item.farmer_id = first_farmer[0] if first_farmer else 1

    img = item.image_url.strip() if item.image_url else ""
    if not img:
        # Provide clean high-quality default agriculture stock images based on category
        cat_lower = item.category.lower()
        if "fruit" in cat_lower:
            img = "https://images.unsplash.com/photo-1619566636858-adf3ef46400b?w=500&auto=format&fit=crop&q=60"
        elif "grain" in cat_lower:
            img = "https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?w=500&auto=format&fit=crop&q=60"
        else:
            img = "https://images.unsplash.com/photo-1592924357228-91a4daadcfea?w=500&auto=format&fit=crop&q=60"

    c.execute("""
    INSERT INTO products (
        farmer_id, crop_name, category, quantity_kg, available_quantity_kg,
        price_per_kg, location, harvest_date, available_date,
        quality_grade, description, image_url
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (
        item.farmer_id, item.crop_name, item.category, item.quantity_kg, item.quantity_kg,
        item.price_per_kg, item.location, item.harvest_date, item.available_date,
        item.quality_grade, item.description, img
    ))
    conn.commit()
    new_id = c.lastrowid
    conn.close()
    return {"message": "Product successfully listed on marketplace", "id": new_id}

@app.get("/api/farmers")
def list_farmers():
    conn = get_db_connection()
    rows = conn.cursor().execute("SELECT * FROM farmers ORDER BY id ASC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.post("/api/farmers", status_code=status.HTTP_201_CREATED)
def register_farmer(farmer: FarmerCreateSchema):
    """Allows ANY farmer from ANY village, district, or state in India to register."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
    INSERT INTO farmers (name, fpo_name, phone, city, state, address, rating)
    VALUES (?, ?, ?, ?, ?, ?, ?);
    """, (
        farmer.name,
        farmer.fpo_name or "Independent Farmer",
        farmer.phone,
        farmer.city,
        farmer.state or "India",
        farmer.address or "",
        farmer.rating or 4.8
    ))
    conn.commit()
    new_id = c.lastrowid
    conn.close()
    return {"message": "Farmer registered successfully!", "id": new_id, "name": farmer.name}

@app.get("/api/orders")
def list_orders():
    conn = get_db_connection()
    rows = conn.cursor().execute("SELECT * FROM orders ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.post("/api/orders", status_code=status.HTTP_201_CREATED)
def create_order(payload: OrderCreateSchema):
    conn = get_db_connection()
    c = conn.cursor()

    product = c.execute("SELECT * FROM products WHERE id = ?", (payload.product_id,)).fetchone()
    if not product:
        conn.close()
        raise HTTPException(status_code=404, detail="Selected product not found")

    if payload.quantity_kg > product["available_quantity_kg"]:
        conn.close()
        raise HTTPException(status_code=400, detail=f"Requested quantity ({payload.quantity_kg} kg) exceeds available stock ({product['available_quantity_kg']} kg)")

    total_amount = round(payload.quantity_kg * product["price_per_kg"], 2)
    order_num = f"ORD-{datetime.date.today().year}-{uuid.uuid4().hex[:6].upper()}"

    # Get farmer details
    farmer = c.execute("SELECT name FROM farmers WHERE id = ?", (product["farmer_id"],)).fetchone()
    farmer_name = farmer["name"] if farmer else "Local Farm Producer"

    # Insert order
    c.execute("""
    INSERT INTO orders (
        order_number, product_id, product_name, farmer_name, buyer_name,
        buyer_phone, buyer_email, delivery_address, delivery_city,
        quantity_kg, price_per_kg, total_amount, order_status,
        payment_status, payment_method, transaction_id
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Confirmed', 'Paid', ?, ?);
    """, (
        order_num, product["id"], product["crop_name"], farmer_name, payload.buyer_name,
        payload.buyer_phone, payload.buyer_email, payload.delivery_address, payload.delivery_city,
        payload.quantity_kg, product["price_per_kg"], total_amount,
        payload.payment_method, f"TXN-{uuid.uuid4().hex[:8].upper()}"
    ))

    # Update product inventory
    new_qty = product["available_quantity_kg"] - payload.quantity_kg
    c.execute("UPDATE products SET available_quantity_kg = ? WHERE id = ?", (new_qty, product["id"]))

    order_id = c.lastrowid

    # Automatically provision logistics shipment for this order!
    # Works for ALL farmers anywhere across India
    p_lat, p_lon = get_coordinates_for_city(product["location"])
    d_lat, d_lon = get_coordinates_for_city(payload.delivery_city)
    est_distance = max(25.0, round(haversine_distance(p_lat, p_lon, d_lat, d_lon), 1))

    # Select closest vehicle to the farmer's produce origin
    candidates = c.execute("SELECT * FROM vehicles WHERE status = 'Available'").fetchall()
    if not candidates:
        candidates = c.execute("SELECT * FROM vehicles").fetchall()

    vehicle = None
    min_veh_dist = float("inf")
    for v in candidates:
        v_dict = dict(v)
        v_lat = v_dict.get("lat") or p_lat
        v_lon = v_dict.get("lon") or p_lon
        dist = haversine_distance(p_lat, p_lon, v_lat, v_lon)
        if dist < min_veh_dist:
            min_veh_dist = dist
            vehicle = v_dict

    rate = vehicle["per_km_rate"] if vehicle else 22.0
    cost = round(est_distance * rate, 0)
    est_hours = max(1.5, round(est_distance / 45.0, 1))
    eta = (datetime.datetime.now() + datetime.timedelta(hours=est_hours)).strftime("%I:%M %p Tomorrow")

    cur_lat = round(p_lat * 0.7 + d_lat * 0.3, 4)
    cur_lon = round(p_lon * 0.7 + d_lon * 0.3, 4)
    cur_desc = f"Transit Corridor en route to {payload.delivery_city}"

    tracking_num = f"SHIP-IND-{uuid.uuid4().hex[:6].upper()}"
    c.execute("""
    INSERT INTO shipments (
        tracking_no, order_id, cargo_description, weight_kg,
        pickup_location, collection_center, delivery_location,
        vehicle_id, vehicle_no, driver_name, driver_phone,
        status, distance_km, estimated_hours, transport_cost, eta_timestamp,
        current_lat, current_lon, current_location_desc
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Scheduled', ?, ?, ?, ?, ?, ?, ?);
    """, (
        tracking_num, order_id, f"{payload.quantity_kg} kg {product['crop_name']}",
        payload.quantity_kg, f"Farmer Farm, {product['location']}",
        f"{product['location']} Agro Collection Center",
        f"{payload.delivery_address}, {payload.delivery_city}",
        vehicle["id"] if vehicle else 1,
        vehicle["vehicle_no"] if vehicle else "MH-12-PQ-8901",
        vehicle["driver_name"] if vehicle else "Santosh Shinde",
        vehicle["driver_phone"] if vehicle else "9890123987",
        est_distance, est_hours, cost, eta,
        cur_lat, cur_lon, cur_desc
    ))

    conn.commit()
    conn.close()

    return {
        "message": "Order successfully placed and logistics dispatch scheduled!",
        "order_id": order_id,
        "order_number": order_num,
        "tracking_number": tracking_num,
        "total_amount": total_amount,
        "remaining_stock_kg": new_qty
    }

# ----- 2. LOGISTICS SUPPORT & FLEET MANAGEMENT -----

@app.get("/api/vehicles")
def list_vehicles():
    conn = get_db_connection()
    rows = conn.cursor().execute("SELECT * FROM vehicles ORDER BY id ASC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.get("/api/shipments")
def list_shipments():
    conn = get_db_connection()
    rows = conn.cursor().execute("""
    SELECT s.*, o.farmer_name, o.product_name, o.buyer_name, o.buyer_phone, o.delivery_city
    FROM shipments s
    LEFT JOIN orders o ON s.order_id = o.id
    ORDER BY s.id DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.post("/api/shipments", status_code=status.HTTP_201_CREATED)
def create_shipment(payload: ShipmentCreateSchema):
    conn = get_db_connection()
    c = conn.cursor()

    vehicle = None
    if payload.vehicle_id:
        vehicle = c.execute("SELECT * FROM vehicles WHERE id = ?", (payload.vehicle_id,)).fetchone()

    p_lat, p_lon = get_coordinates_for_city(payload.pickup_location)
    d_lat, d_lon = get_coordinates_for_city(payload.delivery_location)
    dist_km = max(25.0, round(haversine_distance(p_lat, p_lon, d_lat, d_lon), 1))

    if not vehicle:
        # Find closest available vehicle to pickup location anywhere in India
        candidates = c.execute("SELECT * FROM vehicles WHERE status = 'Available'").fetchall()
        if not candidates:
            candidates = c.execute("SELECT * FROM vehicles").fetchall()
        min_v_dist = float("inf")
        for v in candidates:
            v_dict = dict(v)
            v_lat = v_dict.get("lat") or p_lat
            v_lon = v_dict.get("lon") or p_lon
            dist = haversine_distance(p_lat, p_lon, v_lat, v_lon)
            if dist < min_v_dist:
                min_v_dist = dist
                vehicle = v_dict

    rate = vehicle["per_km_rate"] if vehicle else 22.0
    transport_cost = round(dist_km * rate, 0)
    est_hours = max(1.5, round(dist_km / 45.0, 1))
    eta = (datetime.datetime.now() + datetime.timedelta(hours=est_hours)).strftime("%I:%M %p Today")
    tracking_no = f"SHIP-IND-{uuid.uuid4().hex[:6].upper()}"

    cur_lat = round(p_lat * 0.7 + d_lat * 0.3, 4)
    cur_lon = round(p_lon * 0.7 + d_lon * 0.3, 4)
    cur_desc = f"Transit Corridor en route to {payload.delivery_location.split(',')[0]}"

    c.execute("""
    INSERT INTO shipments (
        tracking_no, order_id, cargo_description, weight_kg,
        pickup_location, collection_center, delivery_location,
        vehicle_id, vehicle_no, driver_name, driver_phone,
        status, distance_km, estimated_hours, transport_cost, eta_timestamp,
        current_lat, current_lon, current_location_desc
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Scheduled', ?, ?, ?, ?, ?, ?, ?);
    """, (
        tracking_no, payload.order_id, payload.cargo_description, payload.weight_kg,
        payload.pickup_location, payload.collection_center, payload.delivery_location,
        vehicle["id"] if vehicle else 1,
        vehicle["vehicle_no"] if vehicle else "MH-15-EG-4412",
        vehicle["driver_name"] if vehicle else "Santosh Shinde",
        vehicle["driver_phone"] if vehicle else "9890123987",
        dist_km, est_hours, transport_cost, eta,
        cur_lat, cur_lon, cur_desc
    ))

    # Mark vehicle as On Route
    if vehicle and "id" in vehicle:
        c.execute("UPDATE vehicles SET status = 'On Route' WHERE id = ?", (vehicle["id"],))

    conn.commit()
    conn.close()
    return {"message": "Shipment successfully scheduled", "tracking_no": tracking_no, "transport_cost": transport_cost, "eta": eta}

@app.patch("/api/shipments/{shipment_id}/status")
def update_shipment_status(shipment_id: int, payload: ShipmentStatusUpdateSchema):
    valid_statuses = ["Scheduled", "Picked Up", "At Collection Center", "In Transit", "Delivered"]
    if payload.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Status must be one of: {valid_statuses}")

    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE shipments SET status = ? WHERE id = ?", (payload.status, shipment_id))
    
    if payload.status == "Delivered":
        # Free up assigned vehicle
        shipment = c.execute("SELECT vehicle_id FROM shipments WHERE id = ?", (shipment_id,)).fetchone()
        if shipment and shipment["vehicle_id"]:
            c.execute("UPDATE vehicles SET status = 'Available' WHERE id = ?", (shipment["vehicle_id"],))

    conn.commit()
    conn.close()
    return {"message": f"Shipment status updated to {payload.status}"}

# ----- 2B. GPS LOGISTICS TRACKING & BREAKDOWN RECOVERY -----

@app.get("/api/logistics/tracking/{shipment_id}")
def get_shipment_gps_tracking(shipment_id: str):
    """
    Returns live GPS telemetry, breakdown alert status, and backup vehicle details
    for ANY active farmer shipment across India (matching Problem Statement 26033).
    """
    conn = get_db_connection()
    c = conn.cursor()

    if shipment_id.isdigit():
        shipment = c.execute("SELECT * FROM shipments WHERE id = ?", (int(shipment_id),)).fetchone()
    else:
        shipment = c.execute("SELECT * FROM shipments WHERE tracking_no = ?", (shipment_id,)).fetchone()

    if not shipment:
        conn.close()
        raise HTTPException(status_code=404, detail="Shipment not found")

    s_dict = dict(shipment)

    # Dynamic pan-India coordinates resolution for ANY farmer & delivery city
    pickup_lat, pickup_lon = get_coordinates_for_city(s_dict.get("pickup_location") or "Nashik")
    dest_lat, dest_lon = get_coordinates_for_city(s_dict.get("delivery_location") or "Pune")

    stored_lat = s_dict.get("current_lat")
    stored_lon = s_dict.get("current_lon")

    # If stored is default/missing or outside the transit corridor, calculate dynamic transit position
    if not stored_lat or stored_lat == 0 or (abs(stored_lat - pickup_lat) > 4.5 and abs(stored_lat - dest_lat) > 4.5):
        cur_lat = round(pickup_lat * 0.6 + dest_lat * 0.4, 4)
        cur_lon = round(pickup_lon * 0.6 + dest_lon * 0.4, 4)
        dest_city_label = s_dict.get('delivery_location', 'Market Hub').split(',')[0].strip()
        cur_desc = f"Transit Corridor en route to {dest_city_label}"
    else:
        cur_lat = stored_lat
        cur_lon = stored_lon
        cur_desc = s_dict.get("current_location_desc") or "Transit Corridor"

    # Backup vehicle lookup if breakdown active
    backup_veh = None
    if s_dict.get("breakdown_status") == "BREAKDOWN" and s_dict.get("backup_vehicle_no"):
        b_veh = c.execute("SELECT * FROM vehicles WHERE vehicle_no = ?", (s_dict["backup_vehicle_no"],)).fetchone()
        b_lat = b_veh["lat"] if b_veh and "lat" in b_veh.keys() and b_veh["lat"] else (cur_lat + 0.1)
        b_lon = b_veh["lon"] if b_veh and "lon" in b_veh.keys() and b_veh["lon"] else (cur_lon + 0.1)
        backup_veh = {
            "id": s_dict.get("backup_vehicle_id"),
            "vehicle_no": s_dict.get("backup_vehicle_no"),
            "vehicle_type": s_dict.get("backup_vehicle_type"),
            "driver_name": s_dict.get("backup_driver_name"),
            "driver_phone": s_dict.get("backup_driver_phone"),
            "distance_km": s_dict.get("backup_distance_km"),
            "eta_mins": s_dict.get("backup_eta_mins"),
            "lat": b_lat,
            "lon": b_lon,
            "status": "Dispatched / Moving to Breakdown Site"
        }

    conn.close()

    return {
        "id": s_dict["id"],
        "tracking_no": s_dict["tracking_no"],
        "cargo_description": s_dict["cargo_description"],
        "weight_kg": s_dict["weight_kg"],
        "pickup_location": s_dict["pickup_location"],
        "collection_center": s_dict["collection_center"],
        "delivery_location": s_dict["delivery_location"],
        "status": s_dict["status"],
        "eta_timestamp": s_dict["eta_timestamp"],
        "vehicle_id": s_dict.get("vehicle_id"),
        "vehicle_no": s_dict.get("vehicle_no"),
        "driver_name": s_dict.get("driver_name"),
        "driver_phone": s_dict.get("driver_phone"),
        "current_lat": cur_lat,
        "current_lon": cur_lon,
        "current_location_desc": cur_desc,
        "pickup_lat": pickup_lat,
        "pickup_lon": pickup_lon,
        "destination_lat": dest_lat,
        "destination_lon": dest_lon,
        "breakdown_status": s_dict.get("breakdown_status") or "NORMAL",
        "breakdown_reason": s_dict.get("breakdown_reason") or "",
        "breakdown_lat": s_dict.get("breakdown_lat") or 0.0,
        "breakdown_lon": s_dict.get("breakdown_lon") or 0.0,
        "breakdown_timestamp": s_dict.get("breakdown_timestamp") or "",
        "backup_vehicle": backup_veh
    }

@app.post("/api/logistics/breakdown/{shipment_id}")
def trigger_vehicle_breakdown(shipment_id: str, payload: Optional[BreakdownTriggerSchema] = None):
    """
    Simulates / triggers a vehicle breakdown along transit for ANY farmer in India.
    1. Sets breakdown status and logs GPS location along the farmer's corridor.
    2. Searches fleet for nearest available backup vehicle across regional depots.
    3. Calculates real distance via Haversine formula and estimated arrival time.
    4. Dispatches the backup vehicle and updates telemetry.
    """
    reason = payload.reason if payload and payload.reason else "Mechanical Engine Failure along Transit Corridor"
    conn = get_db_connection()
    c = conn.cursor()

    if shipment_id.isdigit():
        shipment = c.execute("SELECT * FROM shipments WHERE id = ?", (int(shipment_id),)).fetchone()
    else:
        shipment = c.execute("SELECT * FROM shipments WHERE tracking_no = ?", (shipment_id,)).fetchone()

    if not shipment:
        conn.close()
        raise HTTPException(status_code=404, detail="Shipment not found")

    s_dict = dict(shipment)
    pickup_lat, pickup_lon = get_coordinates_for_city(s_dict.get("pickup_location") or "Nashik")
    dest_lat, dest_lon = get_coordinates_for_city(s_dict.get("delivery_location") or "Pune")

    if payload and payload.breakdown_lat is not None and payload.breakdown_lat != 0:
        b_lat = payload.breakdown_lat
        b_lon = payload.breakdown_lon or round(pickup_lon * 0.6 + dest_lon * 0.4, 4)
    elif s_dict.get("current_lat") and s_dict.get("current_lat") != 0 and not (abs(s_dict.get("current_lat") - pickup_lat) > 4.5 and abs(s_dict.get("current_lat") - dest_lat) > 4.5):
        b_lat = s_dict.get("current_lat")
        b_lon = s_dict.get("current_lon")
    else:
        b_lat = round(pickup_lat * 0.6 + dest_lat * 0.4, 4)
        b_lon = round(pickup_lon * 0.6 + dest_lon * 0.4, 4)

    timestamp = datetime.datetime.now().strftime("%I:%M %p, %d %b %Y")

    curr_veh_id = s_dict.get("vehicle_id")
    if curr_veh_id:
        c.execute("UPDATE vehicles SET status = 'Under Repair (Breakdown)' WHERE id = ?", (curr_veh_id,))

    # Find the nearest available backup vehicle anywhere in the nation
    candidates = c.execute("SELECT * FROM vehicles WHERE status = 'Available' AND id != ?", (curr_veh_id or 0,)).fetchall()
    if not candidates:
        candidates = c.execute("SELECT * FROM vehicles WHERE id != ?", (curr_veh_id or 0,)).fetchall()

    if not candidates:
        conn.close()
        raise HTTPException(status_code=500, detail="No backup vehicles found in fleet")

    best_candidate = None
    min_dist = float("inf")
    for cand in candidates:
        c_dict = dict(cand)
        c_lat = c_dict.get("lat") or 19.5761
        c_lon = c_dict.get("lon") or 74.2070
        dist = haversine_distance(b_lat, b_lon, c_lat, c_lon)
        if dist < min_dist:
            min_dist = dist
            best_candidate = c_dict

    eta_mins = max(10, int(round((min_dist / 45.0) * 60)))
    min_dist_rounded = round(min_dist, 1)

    c.execute("""
    UPDATE shipments SET
        breakdown_status = 'BREAKDOWN',
        breakdown_reason = ?,
        breakdown_lat = ?,
        breakdown_lon = ?,
        breakdown_timestamp = ?,
        backup_vehicle_id = ?,
        backup_vehicle_no = ?,
        backup_vehicle_type = ?,
        backup_driver_name = ?,
        backup_driver_phone = ?,
        backup_distance_km = ?,
        backup_eta_mins = ?
    WHERE id = ?;
    """, (
        reason, b_lat, b_lon, timestamp,
        best_candidate["id"], best_candidate["vehicle_no"], best_candidate["vehicle_type"],
        best_candidate["driver_name"], best_candidate["driver_phone"],
        min_dist_rounded, eta_mins, s_dict["id"]
    ))

    c.execute("UPDATE vehicles SET status = 'Dispatched (Recovery)' WHERE id = ?", (best_candidate["id"],))
    conn.commit()
    conn.close()

    return {
        "status": "BREAKDOWN_DETECTED",
        "message": f"Vehicle breakdown detected for shipment {s_dict['tracking_no']}! Nearest backup vehicle dispatched.",
        "shipment_id": s_dict["id"],
        "tracking_no": s_dict["tracking_no"],
        "cargo_description": s_dict["cargo_description"],
        "weight_kg": s_dict["weight_kg"],
        "breakdown_location": {
            "lat": b_lat,
            "lon": b_lon,
            "description": s_dict.get("current_location_desc") or f"Transit Corridor ({b_lat:.2f}, {b_lon:.2f})"
        },
        "reason": reason,
        "timestamp": timestamp,
        "backup_vehicle": {
            "id": best_candidate["id"],
            "vehicle_no": best_candidate["vehicle_no"],
            "vehicle_type": best_candidate["vehicle_type"],
            "driver_name": best_candidate["driver_name"],
            "driver_phone": best_candidate["driver_phone"],
            "current_location": best_candidate["current_location"],
            "lat": best_candidate.get("lat") or 19.5761,
            "lon": best_candidate.get("lon") or 74.2070,
            "distance_km": min_dist_rounded,
            "eta_mins": eta_mins,
            "eta_description": f"{eta_mins} mins (~{min_dist_rounded} km away)"
        }
    }

@app.post("/api/logistics/resolve-breakdown/{shipment_id}")
def resolve_vehicle_breakdown(shipment_id: str):
    """
    Transfers produce cargo to the arrived backup vehicle and resumes transit to destination.
    """
    conn = get_db_connection()
    c = conn.cursor()

    if shipment_id.isdigit():
        shipment = c.execute("SELECT * FROM shipments WHERE id = ?", (int(shipment_id),)).fetchone()
    else:
        shipment = c.execute("SELECT * FROM shipments WHERE tracking_no = ?", (shipment_id,)).fetchone()

    if not shipment:
        conn.close()
        raise HTTPException(status_code=404, detail="Shipment not found")

    s_dict = dict(shipment)
    backup_veh_id = s_dict.get("backup_vehicle_id")
    backup_veh_no = s_dict.get("backup_vehicle_no")

    if backup_veh_id and backup_veh_no:
        c.execute("""
        UPDATE shipments SET
            vehicle_id = ?,
            vehicle_no = ?,
            driver_name = ?,
            driver_phone = ?,
            breakdown_status = 'NORMAL',
            breakdown_reason = '',
            current_location_desc = 'Cargo Transferred to Backup Vehicle - Resumed Transit on NH-60'
        WHERE id = ?;
        """, (
            backup_veh_id, backup_veh_no,
            s_dict.get("backup_driver_name") or "Sunil Patil",
            s_dict.get("backup_driver_phone") or "9822334455",
            s_dict["id"]
        ))
        c.execute("UPDATE vehicles SET status = 'On Route' WHERE id = ?", (backup_veh_id,))
    else:
        c.execute("""
        UPDATE shipments SET
            breakdown_status = 'NORMAL',
            breakdown_reason = ''
        WHERE id = ?;
        """, (s_dict["id"],))

    conn.commit()
    conn.close()

    return {
        "status": "RESOLVED",
        "message": f"Breakdown resolved! Cargo transferred to {backup_veh_no or 'backup vehicle'} and transit resumed safely.",
        "shipment_id": s_dict["id"],
        "tracking_no": s_dict["tracking_no"]
    }

# ----- 3. AI DEMAND FORECASTING -----

@app.get("/api/forecast")
def get_ai_demand_forecast(
    crop: str = Query("Tomato", description="Crop name"),
    city: str = Query("Pune", description="Target market city"),
    horizon: int = Query(7, description="Forecast horizon in days (7, 14, 30)"),
    season: str = Query("Monsoon", description="Current season"),
    weather: str = Query("Moderate Rain", description="Weather condition"),
    festival: str = Query("Ganesh Chaturthi", description="Upcoming festival event"),
    price: float = Query(35.0, description="Current market price per kg"),
    base_demand: float = Query(1000.0, description="Base historical weekly demand in kg")
):
    """
    Returns AI demand forecasting analysis matching the problem statement:
    Takes previous sales, season, weather, festival, location, and price.
    Returns: Current Demand vs AI Forecast (e.g. 1,000 kg -> 1,500 kg) with charts and advisories.
    """
    result = calculate_forecast(
        crop_name=crop,
        city=city,
        horizon_days=horizon,
        season=season,
        weather=weather,
        festival=festival,
        current_price=price,
        base_demand_kg=base_demand
    )
    return result

# ----- 4. AI ROUTE OPTIMIZATION -----

@app.get("/api/route/waypoints")
def get_route_waypoints():
    conn = get_db_connection()
    rows = conn.cursor().execute("SELECT * FROM route_waypoints ORDER BY stop_order ASC").fetchall()
    conn.close()
    if rows:
        return [dict(r) for r in rows]
    return DEFAULT_WAYPOINTS

@app.post("/api/route/optimize")
def run_route_optimization(payload: Optional[RouteOptimizeRequest] = None):
    """
    Solves Multi-Stop Route Optimization for the 5 farmers scenario:
    Farmer A (Nashik), Farmer B (Sangamner), Farmer C (Ahmednagar), Farmer D (Pune), Farmer E (Satara).
    Minimizes: Distance + Fuel Cost + Delivery Time.
    """
    waypoints = payload.waypoints if payload and payload.waypoints and len(payload.waypoints) > 0 else DEFAULT_WAYPOINTS
    hub = payload.hub if payload and payload.hub else None
    result = solve_route_optimization(waypoints=waypoints, hub=hub)
    return result

@app.get("/api/network-info")
def get_network_info(request: Request):
    """Returns network / host info for smartphone/tablet access."""
    forwarded_host = request.headers.get("x-forwarded-host") or request.headers.get("host")
    forwarded_proto = request.headers.get("x-forwarded-proto", "https" if forwarded_host and "vercel.app" in forwarded_host else "http")

    if forwarded_host and "127.0.0.1" not in forwarded_host and "localhost" not in forwarded_host:
        public_url = f"{forwarded_proto}://{forwarded_host}"
        return {
            "local_ip": forwarded_host,
            "port": 443 if forwarded_proto == "https" else 80,
            "local_url": public_url,
            "mobile_url": public_url
        }

    import socket
    local_ip = "127.0.0.1"
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.4)
        s.connect(('8.8.8.8', 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        try:
            local_ip = socket.gethostbyname(socket.gethostname())
        except Exception:
            pass
    return {
        "local_ip": local_ip,
        "port": 8000,
        "local_url": "http://127.0.0.1:8000",
        "mobile_url": f"http://{local_ip}:8000"
    }

@app.get("/api/corridors")
def get_regional_corridors():
    """Returns regional pre-configured corridors across India."""
    try:
        from backend.route_optimizer import (
            CORRIDOR_MAHARASHTRA, CORRIDOR_NORTH_INDIA, CORRIDOR_CENTRAL_INDIA,
            CORRIDOR_GUJARAT, CORRIDOR_SOUTH_INDIA, REGIONAL_HUBS, CITY_COORDINATES
        )
    except ImportError:
        from route_optimizer import (
            CORRIDOR_MAHARASHTRA, CORRIDOR_NORTH_INDIA, CORRIDOR_CENTRAL_INDIA,
            CORRIDOR_GUJARAT, CORRIDOR_SOUTH_INDIA, REGIONAL_HUBS, CITY_COORDINATES
        )
    return {
        "corridors": {
            "maharashtra": {
                "name": "Maharashtra Western Corridor (Nashik - Sangamner - Ahmednagar - Pune - Satara)",
                "region": "Western India",
                "waypoints": CORRIDOR_MAHARASHTRA,
                "hub": REGIONAL_HUBS["Maharashtra"]
            },
            "north_india": {
                "name": "North India Granary Corridor (Amritsar - Jalandhar - Ludhiana - Karnal -> Delhi)",
                "region": "North India",
                "waypoints": CORRIDOR_NORTH_INDIA,
                "hub": REGIONAL_HUBS["North India"]
            },
            "central_india": {
                "name": "Central India Malwa Corridor (Ujjain - Indore - Dewas - Sehore -> Bhopal)",
                "region": "Central India",
                "waypoints": CORRIDOR_CENTRAL_INDIA,
                "hub": REGIONAL_HUBS["Central India"]
            },
            "gujarat": {
                "name": "Gujarat Agro Belt (Surat - Bharuch - Anand - Vadodara -> Ahmedabad)",
                "region": "Gujarat",
                "waypoints": CORRIDOR_GUJARAT,
                "hub": REGIONAL_HUBS["Gujarat"]
            },
            "south_india": {
                "name": "South India Spice & Fruit Corridor (Guntur - Kurnool - Anantapur -> Bengaluru)",
                "region": "South India",
                "waypoints": CORRIDOR_SOUTH_INDIA,
                "hub": REGIONAL_HUBS["South India"]
            }
        },
        "regional_hubs": REGIONAL_HUBS,
        "known_cities": list(CITY_COORDINATES.keys())
    }

# ----- 5. DATABASE RESET & SEED DATA HELPER -----

@app.post("/api/reset-data")
def reset_database_data():
    seed_all()
    return {"message": "Database reset to initial sample state successfully!"}

# Explicit root handler ensuring index.html is always returned without static mount ambiguity
@app.get("/", include_in_schema=False)
def get_dashboard_root():
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "Frontend index.html not found"}

# Serve frontend static files
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
