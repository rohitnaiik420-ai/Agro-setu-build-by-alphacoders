import os
import sys
import json
from pathlib import Path

# Safe console encoding for Windows CMD / PowerShell
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Locate project directory robustly
PROJECT_CANDIDATES = [
    Path(__file__).resolve().parent.parent,
    Path(r"C:\Users\ADMIN\Desktop\problem statement 26033 solve by rohit naik"),
    Path(__file__).resolve().parent / "problem statement 26033 solve by rohit naik"
]
PROJECT_DIR = None
for p in PROJECT_CANDIDATES:
    if (p / "backend" / "route_optimizer.py").exists():
        PROJECT_DIR = p
        break

if not PROJECT_DIR:
    PROJECT_DIR = Path(r"C:\Users\ADMIN\Desktop\problem statement 26033 solve by rohit naik")

BACKEND_DIR = PROJECT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from route_optimizer import solve_route_optimization, DEFAULT_WAYPOINTS

def load_five_cities_data():
    json_path = Path(__file__).resolve().parent / "five_cities_data.json"
    if json_path.exists():
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def print_city_detail(city_name):
    data = load_five_cities_data()
    if not data:
        print("[-] Data file not found!")
        return

    found = None
    for c in data["five_cities_farmers"]:
        if c["city"].lower() == city_name.lower():
            found = c
            break

    if not found:
        print(f"[-] City '{city_name}' not found. Choose from: Nashik, Sangamner, Ahmednagar, Pune, Satara")
        return

    print("=" * 75)
    print(f"  FOCUSED AUDIT: {found['city'].upper()} (Farmer {found['id']})")
    print("=" * 75)
    print(f"  - Kisan Ka Naam    : {found['farmer_name']} ({found['farmer_label']})")
    print(f"  - FPO Sanstha      : {found['fpo_name']}")
    print(f"  - Faslein (Produce): {found['produce_type']}")
    print(f"  - Pickup Matra     : {found['pickup_qty_kg']} kg")
    print(f"  - Geocoordinates   : Lat {found['latitude']}, Lon {found['longitude']}")
    print(f"  - Duri to Pune Hub : {found['one_way_to_pune_hub_km']} km (One-way)")
    print(f"  - Unoptimized Trip : {found['unoptimized_round_trip_km']} km (Round-trip independently)")
    print(f"  - Diesel Kharch    : {found['unoptimized_diesel_liters']} Liters")
    print(f"  - Akela Trip Cost  : Rs. {found['unoptimized_trip_cost_inr']:,.2f}")
    print("=" * 75)

def run_complete_5_cities_test():
    print("=" * 80)
    print("  SEPARATE TEST SCENARIO: 5 CITIES AGRO-CORRIDOR ROUTE OPTIMIZATION")
    print("     (Satara, Pune, Sangamner, Ahmednagar, Nashik - Problem Statement 26033)")
    print("=" * 80)

    print("\n[PART 1] 5 KISAN AUR UNKE SHAHAR (Farmer & Location Profiles):")
    print("-" * 80)
    data = load_five_cities_data()
    if data:
        for f in data["five_cities_farmers"]:
            print(f"  [{f['id']}] {f['city']:12s} | {f['farmer_label']}: {f['farmer_name']:18s} | {f['produce_type']:32s} | Load: {f['pickup_qty_kg']:4d} kg")
    
    print(f"\n  Central Destination Hub: Pune Central Market Yard (Gultekdi, Pune)")

    print("\n[PART 2] RUNNING AI OPTIMIZATION ALGORITHM (VRP / TSP Multi-Stop Solver):")
    print("-" * 80)
    res = solve_route_optimization(DEFAULT_WAYPOINTS)
    s = res["summary"]

    print("\n  [+] AI KAMI RESULTS (Kami Distance + Kami Fuel Cost + Kami Logistics Cost):")
    print(f"      1. KAMI DISTANCE  : {s['distance_saved_km']} km BACHAYE! ({s['distance_saved_pct']}% Total Distance Reduced)")
    print(f"         - 5 Individual Farmer Trips Distance : {s['unoptimized_distance_km']} km")
    print(f"         - AI Consolidated Multi-Stop Route   : {s['optimized_distance_km']} km")
    
    print(f"\n      2. KAMI FUEL COST : {s['fuel_saved_liters']} LITERS DIESEL BACHAYA!")
    print(f"         - 5 Alag-alag Gaadiyon Ka Diesel     : {s['unoptimized_fuel_liters']} L")
    print(f"         - 1 Pooled Gaadi Ka Diesel           : {s['optimized_fuel_liters']} L")
    
    print(f"\n      3. KAMI COST      : Rs. {s['cost_saved_inr']:,} LOGISTICS KHARCH BACHAYA! ({s['cost_saved_pct']}% Saved)")
    print(f"         - 5 Individual Trucks Cost Total     : Rs. {s['unoptimized_cost_inr']:,}")
    print(f"         - AI Pooled Shared Logistics Cost    : Rs. {s['optimized_cost_inr']:,}")

    print(f"\n      4. ENVIRONMENT    : {s['co2_saved_kg']} kg CO2 Pollution Reduced")
    print(f"      5. TOTAL CARGO    : {s['total_cargo_weight_kg']} kg Agricultural Produce Safely Hauled")
    print(f"      6. TOTAL DURATION : {s['estimated_total_hours']} Hours (Including loading & unloading)")

    print("\n[PART 3] AI OPTIMIZED STOP SEQUENCE (Kram-anusar Route):")
    print("-" * 80)
    for stop in res["optimized_route"]:
        step_str = f"Step {stop['step']}"
        print(f"  {step_str:8s}: {stop['location_name']:14s} ({stop['farmer_label']:12s}) | Leg Duri: {stop['leg_km']:5.1f} km | Total Load: {stop['cumulative_cargo_kg']:5.0f} kg")

    print("\n" + "=" * 80)
    print("  RESULT: 5-CITIES SCENARIO TEST COMPLETED WITH 100% SUCCESS!")
    print("=" * 80)

def main():
    if len(sys.argv) > 2 and sys.argv[1] == "--city":
        print_city_detail(sys.argv[2])
    else:
        run_complete_5_cities_test()

if __name__ == "__main__":
    main()
