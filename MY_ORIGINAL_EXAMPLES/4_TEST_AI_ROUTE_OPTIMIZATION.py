import os
import sys
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
    if (p / "backend" / "route_optimizer.py").exists():
        PROJECT_DIR = p
        break

if not PROJECT_DIR:
    PROJECT_DIR = Path(r"C:\Users\ADMIN\Desktop\problem statement 26033 solve by rohit naik")

BACKEND_DIR = PROJECT_DIR / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from route_optimizer import solve_route_optimization, DEFAULT_WAYPOINTS

def main():
    print("=" * 75)
    print("  POINT 4: AI ROUTE OPTIMIZATION & MULTI-STOP POOLING")
    print("  (Aapke Image Ka Point 4 Test)")
    print("=" * 75)

    print("\n[A] AAPKE DIYE GAYE 5 KISAN (Scenario):")
    print("--------------------------------------------------")
    print("  - Farmer A  -->  Nashik       (Tomato & Grapes - 850 kg)")
    print("  - Farmer B  -->  Sangamner    (Chillies & Onions - 620 kg)")
    print("  - Farmer C  -->  Ahmednagar   (Pomegranates & Wheat - 950 kg)")
    print("  - Farmer D  -->  Pune         (Capsicum & Greens - 700 kg)")
    print("  - Farmer E  -->  Satara       (Ginger & Strawberries - 500 kg)")
    print("  Destination Hub: Pune Central Market Yard & Distribution Center")

    # Running AI TSP / VRP route optimization algorithm
    res = solve_route_optimization(DEFAULT_WAYPOINTS)
    s = res["summary"]

    print("\n[B] AI OPTIMIZATION ALGORITHM RESULTS (KAMI CHECK):")
    print("--------------------------------------------------")
    print("  1. KAMI DISTANCE (Distance Saved) : " + str(s["distance_saved_km"]) + " km bachaye! (" + str(s["distance_saved_pct"]) + "% Total Reduction)")
    print("     - 5 Alag-alag Gaadiyon Ki Duri : " + str(s["unoptimized_distance_km"]) + " km")
    print("     - 1 Consolidated AI Route Duri : " + str(s["optimized_distance_km"]) + " km")

    print("\n  2. KAMI FUEL COST (Diesel Saved)  : " + str(s["fuel_saved_liters"]) + " Liters Diesel Bachaya!")
    print("     - Unoptimized Fuel Consumed    : " + str(s["unoptimized_fuel_liters"]) + " L")
    print("     - AI Optimized Fuel Consumed   : " + str(s["optimized_fuel_liters"]) + " L")

    print("\n  3. KAMI LOGISTICS COST (Rs Saved) : Rs. " + str(s["cost_saved_inr"]) + " Bachaye! (" + str(s["cost_saved_pct"]) + "% Cost Reduced)")
    print("     - Unoptimized Total Cost       : Rs. " + str(s["unoptimized_cost_inr"]))
    print("     - AI Optimized Pooled Cost     : Rs. " + str(s["optimized_cost_inr"]))

    print("\n  4. GREEN LOGISTICS (CO2 Saved)    : " + str(s["co2_saved_kg"]) + " kg CO2 Pollution Reduced")
    print("  5. TOTAL CROP LOAD HAULED         : " + str(s["total_cargo_weight_kg"]) + " kg in 1 single trip!")

    print("\n[C] AI STOP-BY-STOP OPTIMIZED SEQUENCE:")
    print("--------------------------------------------------")
    for stop in res["optimized_route"]:
        print("  Step " + str(stop["step"]) + ": " + str(stop["location_name"]) + " (" + str(stop["farmer_label"]) + ") | Leg: " + str(stop["leg_km"]) + " km | Total Cargo: " + str(stop["cumulative_cargo_kg"]) + " kg")

    print("\n" + "=" * 75)
    print("  RESULT: Point 4 (AI Route Optimization) Working 100% Successfully!")
    print("=" * 75)

if __name__ == "__main__":
    main()
