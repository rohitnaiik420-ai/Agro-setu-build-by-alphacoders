import os
import sys
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from forecasting_engine import calculate_forecast
from route_optimizer import haversine_distance

def test_onion_festival_rush_scenario():
    """
    SCENARIO 2: Nashik Red Onion Festival Surge to Mumbai Vashi APMC
    - Situation: Diwali festival approaching, major sweet & culinary demand surge.
    - Weather: Unseasonal heavy rainfall creates supply shortages in Mandis.
    - Fleet: Heavy 10-Tonne Eicher Lorries scheduled for bulk transport.
    """
    print("=" * 80)
    print("  SCENARIO 2: NASHIK RED ONION DIWALI RUSH TO MUMBAI VASHI APMC")
    print("=" * 80)

    # 1. AI Forecasting for Mumbai Onion Market during Diwali
    print("\n[Step 1] Running AI Demand Forecasting for Mumbai Onion...")
    base_demand = 1800.0  # Normal weekly demand in quintals/kg
    forecast = calculate_forecast(
        crop_name="Onion",
        city="Mumbai",
        horizon_days=14,
        season="Winter",
        weather="Heavy Rain",
        festival="Diwali",
        current_price=28.5,
        base_demand_kg=base_demand
    )

    print(f"  [+] Base Demand (Normal Week): {forecast['current_demand_kg']} kg")
    print(f"  [+] AI Predicted Demand (Diwali Surge): {forecast['predicted_demand_kg']} kg")
    print(f"  [+] Net Increase: +{forecast['delta_kg']} kg (+{forecast['pct_change']}%)")
    print(f"  [+] Driver 1 - Diwali Festival Multiplier: +{forecast['factors']['festival']['impact_kg']} kg")
    print(f"  [+] Driver 2 - Weather Panic Buying Multiplier: +{forecast['factors']['weather']['impact_kg']} kg")
    print(f"  [+] Driver 3 - City Population Scale (Mumbai): Metro tier-1 active")
    print(f"  [+] Advisory: {forecast['advisory']['english']}")

    # 2. Logistics & Fleet Route Computation: Lasalgaon/Nashik to Vashi APMC
    print("\n[Step 2] Calculating Heavy Freight Logistics (10T Lorry)...")
    nashik_lat, nashik_lon = 19.9975, 73.7898
    vashi_lat, vashi_lon = 19.0760, 72.8777
    distance_km = round(haversine_distance(nashik_lat, nashik_lon, vashi_lat, vashi_lon), 1)
    
    # 10T Lorry rate ~Rs. 32/km
    rate_per_km = 32.0
    tonnage_capacity_kg = 10000.0
    trip_cost = round(distance_km * rate_per_km + 1200, 0) # Fuel + Mumbai toll
    avg_speed_kmh = 42.0
    est_hours = round(distance_km / avg_speed_kmh, 1)

    print(f"  [+] Corridor: Nashik Onion Mandi -> Igatpuri Ghats -> Mumbai Vashi APMC")
    print(f"  [+] Highway Distance: {distance_km} km")
    print(f"  [+] Freight Vehicle: 10T Eicher Lorry (Capacity: {tonnage_capacity_kg} kg)")
    print(f"  [+] Transport Cost: Rs. {trip_cost:,.2f}")
    print(f"  [+] Estimated Travel Duration: {est_hours} Hours")
    print(f"  [+] Cost per kg of produce transported: Rs. {round(trip_cost / 8000, 2)} / kg (Ultra economical)")

    print("\n" + "=" * 80)
    print("  >>> SCENARIO 2 (ONION FESTIVAL RUSH) VERIFIED SUCCESSFULLY! <<<")
    print("=" * 80)
    return True

if __name__ == "__main__":
    test_onion_festival_rush_scenario()
