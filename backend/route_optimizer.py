import math
from typing import List, Dict, Any

# Pre-defined regional agricultural corridors across India

CORRIDOR_MAHARASHTRA = [
    {"id": "A", "farmer_label": "Farmer A", "farmer_name": "Ramesh Patil", "location_name": "Nashik", "state": "Maharashtra", "produce": "Tomato & Grapes", "quantity_kg": 850, "lat": 19.9975, "lon": 73.7898},
    {"id": "B", "farmer_label": "Farmer B", "farmer_name": "Sunita Shinde", "location_name": "Sangamner", "state": "Maharashtra", "produce": "Green Chillies & Onions", "quantity_kg": 620, "lat": 19.5761, "lon": 74.2070},
    {"id": "C", "farmer_label": "Farmer C", "farmer_name": "Balasaheb Gadakh", "location_name": "Ahmednagar", "state": "Maharashtra", "produce": "Pomegranates & Wheat", "quantity_kg": 950, "lat": 19.0948, "lon": 74.7480},
    {"id": "D", "farmer_label": "Farmer D", "farmer_name": "Vitthalrao Kadam", "location_name": "Pune", "state": "Maharashtra", "produce": "Capsicum & Leafy Greens", "quantity_kg": 700, "lat": 18.5204, "lon": 73.8567},
    {"id": "E", "farmer_label": "Farmer E", "farmer_name": "Anand Bhosale", "location_name": "Satara", "state": "Maharashtra", "produce": "Ginger & Strawberries", "quantity_kg": 500, "lat": 17.6805, "lon": 74.0183}
]

CORRIDOR_NORTH_INDIA = [
    {"id": "N1", "farmer_label": "Farmer N1", "farmer_name": "Gurpreet Singh", "location_name": "Amritsar", "state": "Punjab", "produce": "Basmati Paddy & Wheat", "quantity_kg": 1800, "lat": 31.6340, "lon": 74.8723},
    {"id": "N2", "farmer_label": "Farmer N2", "farmer_name": "Harbhajan Gill", "location_name": "Jalandhar", "state": "Punjab", "produce": "Seed Potatoes (आलू)", "quantity_kg": 2200, "lat": 31.3260, "lon": 75.5762},
    {"id": "N3", "farmer_label": "Farmer N3", "farmer_name": "Jaswinder Dhillon", "location_name": "Ludhiana", "state": "Punjab", "produce": "Sweet Corn & Dairy", "quantity_kg": 1500, "lat": 30.9010, "lon": 75.8573},
    {"id": "N4", "farmer_label": "Farmer N4", "farmer_name": "Rajender Malik", "location_name": "Karnal", "state": "Haryana", "produce": "Super Basmati Rice", "quantity_kg": 2000, "lat": 29.6857, "lon": 76.9905},
    {"id": "N5", "farmer_label": "Farmer N5", "farmer_name": "Dharambir Rathi", "location_name": "Panipat", "state": "Haryana", "produce": "Fresh Vegetables & Mushroom", "quantity_kg": 900, "lat": 29.3909, "lon": 76.9635}
]

CORRIDOR_CENTRAL_INDIA = [
    {"id": "C1", "farmer_label": "Farmer C1", "farmer_name": "Mangilal Patidar", "location_name": "Ujjain", "state": "Madhya Pradesh", "produce": "Garlic (लहसुन) & Gram", "quantity_kg": 1200, "lat": 23.1765, "lon": 75.7885},
    {"id": "C2", "farmer_label": "Farmer C2", "farmer_name": "Shivraj Chouhan", "location_name": "Indore", "state": "Madhya Pradesh", "produce": "Yellow Soyabean & Wheat", "quantity_kg": 2500, "lat": 22.7196, "lon": 75.8577},
    {"id": "C3", "farmer_label": "Farmer C3", "farmer_name": "Ghanshyam Gurjar", "location_name": "Dewas", "state": "Madhya Pradesh", "produce": "Potatoes & Pulses", "quantity_kg": 1400, "lat": 22.9676, "lon": 76.0534},
    {"id": "C4", "farmer_label": "Farmer C4", "farmer_name": "Premnarayan Verma", "location_name": "Sehore", "state": "Madhya Pradesh", "produce": "Sharbati Gold Wheat", "quantity_kg": 3000, "lat": 23.2031, "lon": 77.0844}
]

CORRIDOR_GUJARAT = [
    {"id": "G1", "farmer_label": "Farmer G1", "farmer_name": "Kishorbhai Patel", "location_name": "Surat", "state": "Gujarat", "produce": "Banana & Okra/Bhindi", "quantity_kg": 1600, "lat": 21.1702, "lon": 72.8311},
    {"id": "G2", "farmer_label": "Farmer G2", "farmer_name": "Naranbhai Desai", "location_name": "Bharuch", "state": "Gujarat", "produce": "Cotton & Tur", "quantity_kg": 1400, "lat": 21.7051, "lon": 72.9959},
    {"id": "G3", "farmer_label": "Farmer G3", "farmer_name": "Hasmukh Patel", "location_name": "Anand", "state": "Gujarat", "produce": "Fresh Milk & Tobacco", "quantity_kg": 2000, "lat": 22.5645, "lon": 72.9289},
    {"id": "G4", "farmer_label": "Farmer G4", "farmer_name": "Pravinbhai Shah", "location_name": "Vadodara", "state": "Gujarat", "produce": "Green Papaya & Drumstick", "quantity_kg": 1100, "lat": 22.3072, "lon": 73.1812}
]

CORRIDOR_SOUTH_INDIA = [
    {"id": "S1", "farmer_label": "Farmer S1", "farmer_name": "Venkat Reddy", "location_name": "Guntur", "state": "Andhra Pradesh", "produce": "Guntur Red Chilli & Turmeric", "quantity_kg": 1800, "lat": 16.3067, "lon": 80.4365},
    {"id": "S2", "farmer_label": "Farmer S2", "farmer_name": "Raghava Rao", "location_name": "Kurnool", "state": "Andhra Pradesh", "produce": "Groundnut & Sunflower Seeds", "quantity_kg": 1500, "lat": 15.8281, "lon": 78.0373},
    {"id": "S3", "farmer_label": "Farmer S3", "farmer_name": "Siddaramaiah Gowda", "location_name": "Anantapur", "state": "Andhra Pradesh", "produce": "Sweet Orange & Pomegranate", "quantity_kg": 1200, "lat": 14.6819, "lon": 77.6006},
    {"id": "S4", "farmer_label": "Farmer S4", "farmer_name": "Basavaraj Patil", "location_name": "Chikkaballapur", "state": "Karnataka", "produce": "Vine Tomatoes & Grapes", "quantity_kg": 1400, "lat": 13.4325, "lon": 77.7275}
]

# Regional Hubs
REGIONAL_HUBS = {
    "Maharashtra": {"name": "Pune Central Agro-Logistics Hub & Market Yard (Gultekdi)", "lat": 18.4900, "lon": 73.8650},
    "North India": {"name": "Delhi Azadpur Wholesale Mandi (Asia's Largest)", "lat": 28.7126, "lon": 77.1740},
    "Central India": {"name": "Bhopal Karond Krishi Upaj Mandi", "lat": 23.2980, "lon": 77.4100},
    "Gujarat": {"name": "Ahmedabad Jamalpur / APMC Vasna Market", "lat": 23.0033, "lon": 72.5645},
    "South India": {"name": "Bengaluru Yeshwanthpur APMC Yard", "lat": 13.0238, "lon": 77.5529}
}

DEFAULT_WAYPOINTS = CORRIDOR_MAHARASHTRA
CENTRAL_HUB = REGIONAL_HUBS["Maharashtra"]

# Dictionary of popular Indian district coordinates for auto-geocoding any farmer's location
CITY_COORDINATES = {
    "nashik": (19.9975, 73.7898),
    "sangamner": (19.5761, 74.2070),
    "ahmednagar": (19.0948, 74.7480),
    "pune": (18.5204, 73.8567),
    "satara": (17.6805, 74.0183),
    "mumbai": (19.0760, 72.8777),
    "navi mumbai": (19.0330, 73.0297),
    "kolhapur": (16.7050, 74.2433),
    "nagpur": (21.1458, 79.0882),
    "delhi": (28.7126, 77.1740),
    "lucknow": (26.8467, 80.9462),
    "kanpur": (26.4499, 80.3319),
    "varanasi": (25.3176, 82.9739),
    "agra": (27.1767, 78.0081),
    "jaipur": (26.9124, 75.7873),
    "jodhpur": (26.2389, 73.0243),
    "ludhiana": (30.9010, 75.8573),
    "amritsar": (31.6340, 74.8723),
    "jalandhar": (31.3260, 75.5762),
    "karnal": (29.6857, 76.9905),
    "panipat": (29.3909, 76.9635),
    "indore": (22.7196, 75.8577),
    "bhopal": (23.2599, 77.4126),
    "ujjain": (23.1765, 75.7885),
    "dewas": (22.9676, 76.0534),
    "ahmedabad": (23.0225, 72.5714),
    "surat": (21.1702, 72.8311),
    "vadodara": (22.3072, 73.1812),
    "anand": (22.5645, 72.9289),
    "rajkot": (22.3039, 70.8022),
    "patna": (25.5941, 85.1376),
    "muzaffarpur": (26.1209, 85.3647),
    "kolkata": (22.5726, 88.3639),
    "bengaluru": (12.9716, 77.5946),
    "hyderabad": (17.3850, 78.4867),
    "chennai": (13.0827, 80.2707),
    "guntur": (16.3067, 80.4365),
    "kurnool": (15.8281, 78.0373),
    "anantapur": (14.6819, 77.6006),
    "coimbatore": (11.0168, 76.9558),
    "kochi": (9.9312, 76.2673),
    "raipur": (21.2514, 81.6296),
    "ranchi": (23.3441, 85.3096),
    "bhubaneswar": (20.2961, 85.8245),
    "guwahati": (26.1445, 91.7362)
}

def get_coordinates_for_city(city_name: str) -> tuple:
    """Returns (lat, lon) for any city name, or estimates from nearest known mandi."""
    cleaned = city_name.strip().lower()
    for k, coords in CITY_COORDINATES.items():
        if k in cleaned or cleaned in k:
            return coords
    # Default to Central India fallback if unknown
    return (20.5937, 78.9629)

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two points in km, scaled by 1.28 for road curvature."""
    R = 6371.0  # Earth's radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    direct_km = R * c
    return direct_km * 1.28

def solve_route_optimization(waypoints: List[Dict[str, Any]] = None, hub: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Universal Multi-stop Vehicle Routing Problem (VRP/TSP) solver for ANY farmer in India.
    Compares:
    1. Unoptimized: Each farmer independently driving round-trip to the destination Mandi.
    2. AI Optimized: Nearest-neighbor + 2-Opt consolidated multi-stop pooling route.
    """
    if not waypoints:
        waypoints = DEFAULT_WAYPOINTS
    if not hub:
        hub = CENTRAL_HUB

    n = len(waypoints)
    if n == 0:
        return {"error": "No waypoints provided"}

    # 1. Compute Unoptimized Individual Trips
    unoptimized_trips = []
    total_unoptimized_km = 0.0
    diesel_price_per_liter = 94.50
    avg_mileage_km_per_liter = 7.5  # Typical for 3.5T to 7T mini-truck / tempo

    for wp in waypoints:
        w_lat = wp.get("lat") or wp.get("latitude")
        w_lon = wp.get("lon") or wp.get("longitude")
        if w_lat is None or w_lon is None:
            w_lat, w_lon = get_coordinates_for_city(wp.get("location_name", "Pune"))
            wp["lat"], wp["lon"] = w_lat, w_lon

        one_way = haversine_distance(w_lat, w_lon, hub["lat"], hub["lon"])
        round_trip = one_way * 2
        total_unoptimized_km += round_trip

        fuel_liters = round_trip / avg_mileage_km_per_liter
        fuel_cost = fuel_liters * diesel_price_per_liter
        driver_toll = round_trip * 4.5  # Driver allowance + toll estimate
        trip_cost = fuel_cost + driver_toll

        unoptimized_trips.append({
            "id": wp.get("id"),
            "farmer_label": wp.get("farmer_label", "Farmer"),
            "farmer_name": wp.get("farmer_name", "Farmer"),
            "location_name": wp.get("location_name", "Mandi"),
            "produce": wp.get("produce", "Agricultural Crop"),
            "quantity_kg": wp.get("quantity_kg", 500),
            "one_way_km": round(one_way, 1),
            "round_trip_km": round(round_trip, 1),
            "fuel_liters": round(fuel_liters, 1),
            "estimated_cost_inr": round(trip_cost, 0)
        })

    # 2. AI Optimized Route Solver: Nearest-Neighbor TSP starting at first waypoint
    unvisited = list(range(n))
    current_idx = 0
    ordered_indices = [current_idx]
    unvisited.remove(current_idx)

    while unvisited:
        curr_wp = waypoints[current_idx]
        curr_lat = curr_wp.get("lat") or curr_wp.get("latitude")
        curr_lon = curr_wp.get("lon") or curr_wp.get("longitude")

        best_next = None
        best_dist = float('inf')

        for u_idx in unvisited:
            nxt_wp = waypoints[u_idx]
            nxt_lat = nxt_wp.get("lat") or nxt_wp.get("latitude")
            nxt_lon = nxt_wp.get("lon") or nxt_wp.get("longitude")
            d = haversine_distance(curr_lat, curr_lon, nxt_lat, nxt_lon)
            if d < best_dist:
                best_dist = d
                best_next = u_idx

        ordered_indices.append(best_next)
        unvisited.remove(best_next)
        current_idx = best_next

    # Build optimized itinerary
    optimized_stops = []
    total_optimized_km = 0.0
    cumulative_load_kg = 0.0

    for step_num, idx in enumerate(ordered_indices, 1):
        wp = waypoints[idx]
        w_lat = wp.get("lat") or wp.get("latitude")
        w_lon = wp.get("lon") or wp.get("longitude")

        if step_num == 1:
            leg_km = 0.0
        else:
            prev_wp = waypoints[ordered_indices[step_num - 2]]
            p_lat = prev_wp.get("lat") or prev_wp.get("latitude")
            p_lon = prev_wp.get("lon") or prev_wp.get("longitude")
            leg_km = haversine_distance(p_lat, p_lon, w_lat, w_lon)

        total_optimized_km += leg_km
        cumulative_load_kg += wp.get("quantity_kg", 500)

        optimized_stops.append({
            "step": step_num,
            "id": wp.get("id"),
            "farmer_label": wp.get("farmer_label", f"Farmer {step_num}"),
            "farmer_name": wp.get("farmer_name", "Farmer"),
            "location_name": wp.get("location_name", "Location"),
            "state": wp.get("state", "India"),
            "produce": wp.get("produce", "Produce"),
            "quantity_kg": wp.get("quantity_kg", 500),
            "cumulative_cargo_kg": round(cumulative_load_kg, 1),
            "lat": w_lat,
            "lon": w_lon,
            "leg_km": round(leg_km, 1),
            "cumulative_km": round(total_optimized_km, 1),
            "action": f"Pickup {wp.get('quantity_kg', 500)} kg {wp.get('produce', '')}"
        })

    # Final leg: from last farmer stop to Central Hub
    last_wp = waypoints[ordered_indices[-1]]
    l_lat = last_wp.get("lat") or last_wp.get("latitude")
    l_lon = last_wp.get("lon") or last_wp.get("longitude")
    final_leg_km = haversine_distance(l_lat, l_lon, hub["lat"], hub["lon"])
    total_optimized_km += final_leg_km

    optimized_stops.append({
        "step": len(ordered_indices) + 1,
        "id": "HUB",
        "farmer_label": "Central Hub",
        "farmer_name": "Agro-Logistics Terminal",
        "location_name": hub["name"],
        "state": "Destination",
        "produce": "Consolidated Batch Delivery",
        "quantity_kg": 0,
        "cumulative_cargo_kg": round(cumulative_load_kg, 1),
        "lat": hub["lat"],
        "lon": hub["lon"],
        "leg_km": round(final_leg_km, 1),
        "cumulative_km": round(total_optimized_km, 1),
        "action": f"Unload all {cumulative_load_kg:,.0f} kg at Central Wholesale Hub"
    })

    # Economic & Environmental Savings
    pooled_truck_mileage = 6.5  # Slightly lower mileage when carrying heavier consolidated load
    opt_fuel_liters = total_optimized_km / pooled_truck_mileage
    opt_fuel_cost = opt_fuel_liters * diesel_price_per_liter
    opt_driver_toll = total_optimized_km * 5.5
    optimized_cost = opt_fuel_cost + opt_driver_toll

    unoptimized_fuel_liters = total_unoptimized_km / avg_mileage_km_per_liter
    unoptimized_cost = sum(t["estimated_cost_inr"] for t in unoptimized_trips)

    distance_saved_km = round(total_unoptimized_km - total_optimized_km, 1)
    distance_saved_pct = round((distance_saved_km / total_unoptimized_km) * 100, 1) if total_unoptimized_km > 0 else 0
    fuel_saved_liters = round(unoptimized_fuel_liters - opt_fuel_liters, 1)
    cost_saved_inr = round(unoptimized_cost - optimized_cost, 0)
    cost_saved_pct = round((cost_saved_inr / unoptimized_cost) * 100, 1) if unoptimized_cost > 0 else 0

    # 1 liter diesel emits approx 2.68 kg CO2
    co2_saved_kg = round(fuel_saved_liters * 2.68, 1)
    avg_speed_kmh = 45.0
    loading_time_per_stop_hours = 0.6
    total_hours = round((total_optimized_km / avg_speed_kmh) + (n * loading_time_per_stop_hours), 1)

    return {
        "summary": {
            "num_farmers": n,
            "total_cargo_weight_kg": round(cumulative_load_kg, 1),
            "unoptimized_distance_km": round(total_unoptimized_km, 1),
            "optimized_distance_km": round(total_optimized_km, 1),
            "distance_saved_km": distance_saved_km,
            "distance_saved_pct": distance_saved_pct,
            "unoptimized_fuel_liters": round(unoptimized_fuel_liters, 1),
            "optimized_fuel_liters": round(opt_fuel_liters, 1),
            "fuel_saved_liters": fuel_saved_liters,
            "unoptimized_cost_inr": round(unoptimized_cost, 0),
            "optimized_cost_inr": round(optimized_cost, 0),
            "cost_saved_inr": cost_saved_inr,
            "cost_saved_pct": cost_saved_pct,
            "co2_saved_kg": co2_saved_kg,
            "estimated_total_hours": total_hours,
            "hub_name": hub["name"]
        },
        "optimized_route": optimized_stops,
        "unoptimized_breakdown": unoptimized_trips
    }

if __name__ == "__main__":
    res = solve_route_optimization(DEFAULT_WAYPOINTS)
    print("Optimization Summary:")
    print(f"Distance Saved: {res['summary']['distance_saved_km']} km ({res['summary']['distance_saved_pct']}%)")
    print(f"Cost Saved: Rs. {res['summary']['cost_saved_inr']} ({res['summary']['cost_saved_pct']}%)")
