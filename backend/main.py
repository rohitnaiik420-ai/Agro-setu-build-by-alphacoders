import os
import uuid
import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

import sys
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from database import get_db_connection, init_db
from forecasting_engine import calculate_forecast
from route_optimizer import solve_route_optimization, DEFAULT_WAYPOINTS, haversine_distance
from seed_data import seed_all

# Directory setup
BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
FRONTEND_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="Agro-Logistics & Marketplace Platform (Problem Statement 26033)",
    description="Integrated Farmer-Buyer Marketplace, Logistics & Fleet Tracking, AI Demand Forecasting, and Multi-stop Route Optimization",
    version="1.0.0"
)

# Enable CORS for local dev flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure DB initialized on startup
@app.on_event("startup")
def startup_event():
    init_db()

# ==================== PYDANTIC SCHEMAS ====================

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
    # e.g., Farmer Location -> Collection Center -> Buyer Delivery City
    vehicle = c.execute("SELECT * FROM vehicles WHERE status = 'Available' LIMIT 1").fetchone()
    if not vehicle:
        vehicle = c.execute("SELECT * FROM vehicles LIMIT 1").fetchone()

    # Calculate distance heuristic
    est_distance = round(haversine_distance(19.9975, 73.7898, 18.5204, 73.8567), 1) # Nashik to Pune ~210km baseline
    rate = vehicle["per_km_rate"] if vehicle else 20.0
    cost = round(est_distance * rate, 0)
    eta = (datetime.datetime.now() + datetime.timedelta(hours=4.5)).strftime("%I:%M %p Tomorrow")

    tracking_num = f"SHIP-MAHA-{uuid.uuid4().hex[:5].upper()}"
    c.execute("""
    INSERT INTO shipments (
        tracking_no, order_id, cargo_description, weight_kg,
        pickup_location, collection_center, delivery_location,
        vehicle_id, vehicle_no, driver_name, driver_phone,
        status, distance_km, estimated_hours, transport_cost, eta_timestamp
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Scheduled', ?, 4.5, ?, ?);
    """, (
        tracking_num, order_id, f"{payload.quantity_kg} kg {product['crop_name']}",
        payload.quantity_kg, f"Farmer Farm, {product['location']}",
        f"{product['location']} Agro Collection Center",
        f"{payload.delivery_address}, {payload.delivery_city}",
        vehicle["id"] if vehicle else 1,
        vehicle["vehicle_no"] if vehicle else "MH-12-PQ-8901",
        vehicle["driver_name"] if vehicle else "Santosh Shinde",
        vehicle["driver_phone"] if vehicle else "9890123987",
        est_distance, cost, eta
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
    rows = conn.cursor().execute("SELECT * FROM shipments ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.post("/api/shipments", status_code=status.HTTP_201_CREATED)
def create_shipment(payload: ShipmentCreateSchema):
    conn = get_db_connection()
    c = conn.cursor()

    vehicle = None
    if payload.vehicle_id:
        vehicle = c.execute("SELECT * FROM vehicles WHERE id = ?", (payload.vehicle_id,)).fetchone()
    if not vehicle:
        vehicle = c.execute("SELECT * FROM vehicles WHERE status = 'Available' LIMIT 1").fetchone()
    if not vehicle:
        vehicle = c.execute("SELECT * FROM vehicles LIMIT 1").fetchone()

    # Estimate distance based on keywords or baseline
    dist_km = 185.0
    if "nashik" in payload.pickup_location.lower() and "pune" in payload.delivery_location.lower():
        dist_km = 212.0
    elif "sangamner" in payload.pickup_location.lower():
        dist_km = 148.0
    elif "ahmednagar" in payload.pickup_location.lower():
        dist_km = 125.0
    elif "satara" in payload.pickup_location.lower():
        dist_km = 112.0

    rate = vehicle["per_km_rate"] if vehicle else 22.0
    transport_cost = round(dist_km * rate, 0)
    est_hours = round(dist_km / 45.0, 1)
    eta = (datetime.datetime.now() + datetime.timedelta(hours=est_hours)).strftime("%I:%M %p Today")
    tracking_no = f"SHIP-MAHA-{uuid.uuid4().hex[:5].upper()}"

    c.execute("""
    INSERT INTO shipments (
        tracking_no, order_id, cargo_description, weight_kg,
        pickup_location, collection_center, delivery_location,
        vehicle_id, vehicle_no, driver_name, driver_phone,
        status, distance_km, estimated_hours, transport_cost, eta_timestamp
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Scheduled', ?, ?, ?, ?);
    """, (
        tracking_no, payload.order_id, payload.cargo_description, payload.weight_kg,
        payload.pickup_location, payload.collection_center, payload.delivery_location,
        vehicle["id"] if vehicle else 1,
        vehicle["vehicle_no"] if vehicle else "MH-15-EG-4412",
        vehicle["driver_name"] if vehicle else "Santosh Shinde",
        vehicle["driver_phone"] if vehicle else "9890123987",
        dist_km, est_hours, transport_cost, eta
    ))

    # Mark vehicle as On Route
    if vehicle:
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
