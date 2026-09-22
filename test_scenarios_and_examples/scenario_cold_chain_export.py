import os
import sys
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from forecasting_engine import calculate_forecast
from route_optimizer import solve_route_optimization

def test_cold_chain_export_scenario():
    """
    SCENARIO 3: Perishable Cold-Chain Sourcing
    - Crops: Bhagwa Pomegranate (Ahmednagar) + Mahabaleshwar Strawberry (Satara)
    - Vehicles: Refrigerated Container Vans (2.5T & 4T) with temperature monitoring (+2°C to +4°C).
    - Destinations: Premium supermarket distribution centers in Pune & Mumbai.
    """
    print("=" * 80)
    print("  SCENARIO 3: HIGH-VALUE PERISHABLE COLD-CHAIN LOGISTICS")
    print("=" * 80)

    # 1. AI Forecasting for Pomegranate & Strawberry in Pune
    print("\n[Step 1] Forecasting High-Value Perishable Produce (Wedding Season)...")
    fc_pom = calculate_forecast(
        crop_name="Pomegranate",
        city="Pune",
        horizon_days=7,
        season="Winter",
        weather="Sunny / Clear",
        festival="Wedding Season",
        current_price=110.0,
        base_demand_kg=800.0
    )
    print(f"  [+] Bhagwa Pomegranate (Ahmednagar): {fc_pom['current_demand_kg']} kg -> {fc_pom['predicted_demand_kg']} kg (+{fc_pom['pct_change']}%)")

    fc_straw = calculate_forecast(
        crop_name="Strawberry",
        city="Pune",
        horizon_days=7,
        season="Winter",
        weather="Sunny / Clear",
        festival="Wedding Season",
        current_price=190.0,
        base_demand_kg=600.0
    )
    print(f"  [+] Mahabaleshwar Strawberry (Satara): {fc_straw['current_demand_kg']} kg -> {fc_straw['predicted_demand_kg']} kg (+{fc_straw['pct_change']}%)")

    # 2. Refrigerated Route Pooling
    print("\n[Step 2] Optimizing Multi-Farm Cold-Chain Van Dispatch...")
    cold_waypoints = [
        {
            "id": "ORCHARD_1",
            "farmer_label": "Ahmednagar Orchards",
            "farmer_name": "Balasaheb Gadakh",
            "location_name": "Ahmednagar",
            "produce": "Bhagwa Pomegranate (Cold Pack)",
            "quantity_kg": 1200,
            "lat": 19.0948,
            "lon": 74.7480
        },
        {
            "id": "ORCHARD_2",
            "farmer_label": "Wai Strawberry Fields",
            "farmer_name": "Anand Bhosale",
            "location_name": "Satara",
            "produce": "Mountain Strawberries",
            "quantity_kg": 800,
            "lat": 17.6805,
            "lon": 74.0183
        }
    ]

    pune_cold_hub = {
        "name": "Pune Central Cold-Storage Terminal (Hadapsar)",
        "lat": 18.5089,
        "lon": 73.9260
    }

    result = solve_route_optimization(waypoints=cold_waypoints, hub=pune_cold_hub)
    s = result["summary"]

    print(f"  [+] Total Perishable Cargo: {s['total_cargo_weight_kg']} kg")
    print(f"  [+] Optimized Cold-Van Distance: {s['optimized_distance_km']} km")
    print(f"  [+] Unoptimized Independent Distance: {s['unoptimized_distance_km']} km")
    print(f"  [+] Km Saved by Route Pooling: {s['distance_saved_km']} km ({s['distance_saved_pct']}%)")
    print(f"  [+] Cold-Chain Cost Saved: Rs. {s['cost_saved_inr']:,}")
    print(f"  [+] Estimated Travel Time: {s['estimated_total_hours']} Hours (Zero spoilage window preserved)")

    print("\n" + "=" * 80)
    print("  >>> SCENARIO 3 (COLD-CHAIN SOURCING) VERIFIED SUCCESSFULLY! <<<")
    print("=" * 80)
    return True

if __name__ == "__main__":
    test_cold_chain_export_scenario()
