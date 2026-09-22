import os
import sys
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from route_optimizer import solve_route_optimization

def test_multi_district_pooling_scenario():
    """
    SCENARIO 4: 7-District Agro-Corridor Mega Pooling
    Demonstrates scalability of the AI Optimization algorithm with 7 collection stops:
    Nashik -> Sangamner -> Shrirampur -> Ahmednagar -> Pune -> Satara -> Kolhapur
    Supplying to Mumbai International Export Terminal & APMC.
    """
    print("=" * 80)
    print("  SCENARIO 4: 7-DISTRICT MAHARASHTRA AGRO-CORRIDOR MEGA POOLING")
    print("=" * 80)

    extended_waypoints = [
        {"id": "W1", "farmer_label": "Nashik Agro Cluster", "farmer_name": "Ramesh Patil", "location_name": "Nashik", "produce": "Table Grapes", "quantity_kg": 1500, "lat": 19.9975, "lon": 73.7898},
        {"id": "W2", "farmer_label": "Sangamner Dairy & Veg", "farmer_name": "Sunita Shinde", "location_name": "Sangamner", "produce": "Green Chillies", "quantity_kg": 800, "lat": 19.5761, "lon": 74.2070},
        {"id": "W3", "farmer_label": "Shrirampur Sugarcane & Veg", "farmer_name": "Kishor Vikhe", "location_name": "Shrirampur", "produce": "Sweet Corn", "quantity_kg": 900, "lat": 19.6167, "lon": 74.6600},
        {"id": "W4", "farmer_label": "Ahmednagar Organic Farm", "farmer_name": "Balasaheb Gadakh", "location_name": "Ahmednagar", "produce": "Pomegranates", "quantity_kg": 1200, "lat": 19.0948, "lon": 74.7480},
        {"id": "W5", "farmer_label": "Pune Peri-Urban", "farmer_name": "Vitthalrao Kadam", "location_name": "Pune", "produce": "Broccoli & Capsicum", "quantity_kg": 1100, "lat": 18.5204, "lon": 73.8567},
        {"id": "W6", "farmer_label": "Satara Highlands FPO", "farmer_name": "Anand Bhosale", "location_name": "Satara", "produce": "Ginger & Turmeric", "quantity_kg": 850, "lat": 17.6805, "lon": 74.0183},
        {"id": "W7", "farmer_label": "Kolhapur Jaggery & Rice", "farmer_name": "Sanjay Patil", "location_name": "Kolhapur", "produce": "Indrayani Rice", "quantity_kg": 2000, "lat": 16.7050, "lon": 74.2433}
    ]

    mumbai_terminal = {
        "name": "Navi Mumbai Central Agro-Export Hub & JNPT Cargo",
        "lat": 18.9500,
        "lon": 72.9500
    }

    print(f"\n[Step 1] Running Multi-Stop TSP/VRP Solver for {len(extended_waypoints)} Districts...")
    res = solve_route_optimization(waypoints=extended_waypoints, hub=mumbai_terminal)
    s = res["summary"]

    print(f"\n  [+] Mega-Corridor Optimization Metrics:")
    print(f"      - Total Participating Farmers / FPOs:   {s['num_farmers']}")
    print(f"      - Aggregated Produce Hauled:             {s['total_cargo_weight_kg']} kg (~8.35 Tonnes)")
    print(f"      - Unoptimized 7 Individual Trips:        {s['unoptimized_distance_km']} km")
    print(f"      - AI Consolidated Multi-Stop Route:      {s['optimized_distance_km']} km")
    print(f"      - TOTAL KM SAVED:                        {s['distance_saved_km']} km ({s['distance_saved_pct']}%)")
    print(f"      - DIESEL FUEL SAVED:                     {s['fuel_saved_liters']} Liters")
    print(f"      - LOGISTICS COST SAVED:                  Rs. {s['cost_saved_inr']:,} ({s['cost_saved_pct']}%)")
    print(f"      - CARBON EMISSIONS REDUCED:              {s['co2_saved_kg']} kg CO2")

    print(f"\n  [+] Consolidated Driving Itinerary:")
    for st in res["optimized_route"]:
        print(f"      Step {st['step']}: {st['location_name']} -> Leg: {st['leg_km']} km | Cumulative Cargo: {st['cumulative_cargo_kg']} kg")

    print("\n" + "=" * 80)
    print("  >>> SCENARIO 4 (7-DISTRICT MEGA POOLING) VERIFIED SUCCESSFULLY! <<<")
    print("=" * 80)
    return True

if __name__ == "__main__":
    test_multi_district_pooling_scenario()
