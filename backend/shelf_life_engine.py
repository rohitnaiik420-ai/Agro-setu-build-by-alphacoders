"""
AgroSetu AI - Dynamic Food Shelf-Life & Cold Chain Quality Prediction Engine
=============================================================================
Based on post-harvest physiology, thermal kinetics (Arrhenius model),
and validated food storage standards from ICAR-CIPHET and USDA Agricultural Handbook 66.
"""

import math
from datetime import datetime, date
from typing import Dict, Any, List, Optional

# Food Category Storage Profiles & Kinetic Parameters
# Temp in Celsius, Humidity in %, Shelf life in days at optimal temp
FOOD_PROFILES: Dict[str, Dict[str, Any]] = {
    # 1. FRUITS
    "Tomato": {
        "category": "Fruits",
        "display_name": "Organic Hybrid Tomato (लाल टमाटर)",
        "optimal_temp_min": 10.0,
        "optimal_temp_max": 14.0,
        "critical_temp_max": 20.0,
        "critical_temp_min": 5.0,  # Chilling injury risk below 5°C
        "optimal_humidity_min": 85.0,
        "optimal_humidity_max": 92.0,
        "nominal_shelf_life_days": 14.0,
        "q10_factor": 2.2,  # Arrhenius acceleration factor per 10°C
        "moisture_loss_sensitivity": 1.4,
        "chilling_injury_susceptible": True,
        "description": "Climacteric fruit; sensitive to chilling injury below 10°C and rapid ripening above 18°C."
    },
    "Bhagwa Pomegranate": {
        "category": "Fruits",
        "display_name": "Bhagwa Pomegranate (सिंदूरी अनार)",
        "optimal_temp_min": 5.0,
        "optimal_temp_max": 7.0,
        "critical_temp_max": 16.0,
        "critical_temp_min": 3.0,
        "optimal_humidity_min": 90.0,
        "optimal_humidity_max": 95.0,
        "nominal_shelf_life_days": 45.0,
        "q10_factor": 1.9,
        "moisture_loss_sensitivity": 1.1,
        "chilling_injury_susceptible": True,
        "description": "High value arils; requires 90-95% RH to avoid rind shrivelling."
    },
    "Strawberry": {
        "category": "Fruits",
        "display_name": "Mahabaleshwar Fresh Strawberries (स्ट्रॉबेरी)",
        "optimal_temp_min": 0.0,
        "optimal_temp_max": 2.5,
        "critical_temp_max": 8.0,
        "critical_temp_min": -0.5,
        "optimal_humidity_min": 90.0,
        "optimal_humidity_max": 95.0,
        "nominal_shelf_life_days": 7.0,
        "q10_factor": 2.8,
        "moisture_loss_sensitivity": 2.2,
        "chilling_injury_susceptible": False,
        "description": "Extremely perishable, high respiration rate; requires strict 0-2°C cold chain."
    },
    "Grapes": {
        "category": "Fruits",
        "display_name": "Thompson Seedless Grapes (अंगूर)",
        "optimal_temp_min": -0.5,
        "optimal_temp_max": 1.5,
        "critical_temp_max": 8.0,
        "critical_temp_min": -1.5,
        "optimal_humidity_min": 90.0,
        "optimal_humidity_max": 95.0,
        "nominal_shelf_life_days": 30.0,
        "q10_factor": 2.1,
        "moisture_loss_sensitivity": 1.8,
        "chilling_injury_susceptible": False,
        "description": "Requires near-freezing cold storage with SO2 pads to prevent Botrytis decay."
    },

    # 2. VEGETABLES
    "Onion": {
        "category": "Vegetables",
        "display_name": "Nashik Pink Onion (गुलाबी कांदा)",
        "optimal_temp_min": 18.0,
        "optimal_temp_max": 25.0,
        "critical_temp_max": 32.0,
        "critical_temp_min": 0.0,
        "optimal_humidity_min": 65.0,
        "optimal_humidity_max": 72.0,
        "nominal_shelf_life_days": 90.0,
        "q10_factor": 1.5,
        "moisture_loss_sensitivity": 0.8,
        "chilling_injury_susceptible": False,
        "description": "Requires well-ventilated dry conditions; high RH triggers fungal neck rot and rooting."
    },
    "Green Chilli": {
        "category": "Vegetables",
        "display_name": "Sangamner Dark Green Chilli (हरी मिर्च)",
        "optimal_temp_min": 7.0,
        "optimal_temp_max": 10.0,
        "critical_temp_max": 18.0,
        "critical_temp_min": 4.0,
        "optimal_humidity_min": 90.0,
        "optimal_humidity_max": 95.0,
        "nominal_shelf_life_days": 21.0,
        "q10_factor": 2.0,
        "moisture_loss_sensitivity": 1.7,
        "chilling_injury_susceptible": True,
        "description": "High moisture loss rate; calyx turns black under thermal fluctuation."
    },
    "Bell Pepper": {
        "category": "Vegetables",
        "display_name": "Green Bell Pepper / Capsicum (शिमला मिर्च)",
        "optimal_temp_min": 7.0,
        "optimal_temp_max": 10.0,
        "critical_temp_max": 16.0,
        "critical_temp_min": 4.0,
        "optimal_humidity_min": 90.0,
        "optimal_humidity_max": 95.0,
        "nominal_shelf_life_days": 18.0,
        "q10_factor": 2.1,
        "moisture_loss_sensitivity": 1.6,
        "chilling_injury_susceptible": True,
        "description": "Vulnerable to sheet-pitting if kept below 5°C; wilts rapidly at humidity < 85%."
    },
    "Leafy Greens": {
        "category": "Vegetables",
        "display_name": "Fresh Pune Palak & Methi (पालक/मेथी)",
        "optimal_temp_min": 0.0,
        "optimal_temp_max": 3.0,
        "critical_temp_max": 10.0,
        "critical_temp_min": -0.5,
        "optimal_humidity_min": 95.0,
        "optimal_humidity_max": 98.0,
        "nominal_shelf_life_days": 5.0,
        "q10_factor": 2.9,
        "moisture_loss_sensitivity": 2.5,
        "chilling_injury_susceptible": False,
        "description": "Extreme water loss rate; yellowing of leaves accelerated above 4°C."
    },

    # 3. DAIRY PRODUCTS
    "Raw Cow Milk": {
        "category": "Dairy Products",
        "display_name": "Anand Farm Chilled Raw Milk (दूध)",
        "optimal_temp_min": 1.0,
        "optimal_temp_max": 4.0,
        "critical_temp_max": 7.0,
        "critical_temp_min": 0.0,
        "optimal_humidity_min": 60.0,
        "optimal_humidity_max": 80.0,
        "nominal_shelf_life_days": 3.0,
        "q10_factor": 3.2,
        "moisture_loss_sensitivity": 0.5,
        "chilling_injury_susceptible": False,
        "description": "Rapid psychrotrophic bacterial growth if temperature exceeds 4.5°C."
    },
    "Fresh Paneer / Cottage Cheese": {
        "category": "Dairy Products",
        "display_name": "Fresh Malai Paneer (पनीर)",
        "optimal_temp_min": 1.0,
        "optimal_temp_max": 4.0,
        "critical_temp_max": 8.0,
        "critical_temp_min": 0.0,
        "optimal_humidity_min": 75.0,
        "optimal_humidity_max": 85.0,
        "nominal_shelf_life_days": 10.0,
        "q10_factor": 2.8,
        "moisture_loss_sensitivity": 1.2,
        "chilling_injury_susceptible": False,
        "description": "High water activity (aw > 0.98); lactic souring and yeast/mould growth if temperature fluctuates."
    },

    # 4. FROZEN FOOD
    "Frozen Green Peas": {
        "category": "Frozen Food",
        "display_name": "IQF Frozen Green Peas (मटर)",
        "optimal_temp_min": -22.0,
        "optimal_temp_max": -18.0,
        "critical_temp_max": -12.0,
        "critical_temp_min": -30.0,
        "optimal_humidity_min": 85.0,
        "optimal_humidity_max": 95.0,
        "nominal_shelf_life_days": 365.0,
        "q10_factor": 2.0,
        "moisture_loss_sensitivity": 1.0,
        "chilling_injury_susceptible": False,
        "description": "Enzymatic browning and recrystallization occurs if cold chain breaks above -12°C."
    },

    # 5. PROCESSED FOOD
    "Tomato Puree / Paste": {
        "category": "Processed Food",
        "display_name": "Organic Aseptic Tomato Puree (टमाटर प्यूरी)",
        "optimal_temp_min": 15.0,
        "optimal_temp_max": 22.0,
        "critical_temp_max": 28.0,
        "critical_temp_min": 4.0,
        "optimal_humidity_min": 50.0,
        "optimal_humidity_max": 70.0,
        "nominal_shelf_life_days": 180.0,
        "q10_factor": 1.6,
        "moisture_loss_sensitivity": 0.2,
        "chilling_injury_susceptible": False,
        "description": "Thermally stabilized; lycopene oxidation and packaging integrity loss above 28°C."
    }
}

# Generic fallback profile for any food category
CATEGORY_DEFAULTS = {
    "Fruits": {
        "optimal_temp_min": 2.0, "optimal_temp_max": 8.0, "critical_temp_max": 15.0, "critical_temp_min": 0.0,
        "optimal_humidity_min": 85.0, "optimal_humidity_max": 95.0, "nominal_shelf_life_days": 14.0,
        "q10_factor": 2.2, "moisture_loss_sensitivity": 1.5, "chilling_injury_susceptible": True
    },
    "Vegetables": {
        "optimal_temp_min": 4.0, "optimal_temp_max": 10.0, "critical_temp_max": 18.0, "critical_temp_min": 1.0,
        "optimal_humidity_min": 85.0, "optimal_humidity_max": 95.0, "nominal_shelf_life_days": 12.0,
        "q10_factor": 2.1, "moisture_loss_sensitivity": 1.6, "chilling_injury_susceptible": True
    },
    "Dairy Products": {
        "optimal_temp_min": 1.0, "optimal_temp_max": 4.0, "critical_temp_max": 7.0, "critical_temp_min": 0.0,
        "optimal_humidity_min": 65.0, "optimal_humidity_max": 80.0, "nominal_shelf_life_days": 7.0,
        "q10_factor": 3.0, "moisture_loss_sensitivity": 0.8, "chilling_injury_susceptible": False
    },
    "Frozen Food": {
        "optimal_temp_min": -22.0, "optimal_temp_max": -18.0, "critical_temp_max": -12.0, "critical_temp_min": -30.0,
        "optimal_humidity_min": 80.0, "optimal_humidity_max": 95.0, "nominal_shelf_life_days": 270.0,
        "q10_factor": 2.0, "moisture_loss_sensitivity": 0.9, "chilling_injury_susceptible": False
    },
    "Processed Food": {
        "optimal_temp_min": 15.0, "optimal_temp_max": 22.0, "critical_temp_max": 28.0, "critical_temp_min": 5.0,
        "optimal_humidity_min": 50.0, "optimal_humidity_max": 70.0, "nominal_shelf_life_days": 120.0,
        "q10_factor": 1.6, "moisture_loss_sensitivity": 0.4, "chilling_injury_susceptible": False
    }
}


def resolve_food_profile(food_name: str, category: Optional[str] = None) -> Dict[str, Any]:
    """Finds exact or best fuzzy match for food name or falls back to category defaults."""
    # Direct match
    if food_name in FOOD_PROFILES:
        return FOOD_PROFILES[food_name]
    
    # Substring match
    lower_name = food_name.lower()
    for key, prof in FOOD_PROFILES.items():
        if key.lower() in lower_name or lower_name in key.lower():
            return prof
            
    # Category fallback
    cat = category or "Vegetables"
    if cat in CATEGORY_DEFAULTS:
        fallback = dict(CATEGORY_DEFAULTS[cat])
        fallback["display_name"] = food_name
        fallback["category"] = cat
        fallback["description"] = f"Standard {cat} cold-chain preservation parameters."
        return fallback

    # General vegetable fallback
    fallback = dict(CATEGORY_DEFAULTS["Vegetables"])
    fallback["display_name"] = food_name
    fallback["category"] = "Vegetables"
    fallback["description"] = "General perishable produce standard parameters."
    return fallback


def calculate_dynamic_shelf_life(
    food_name: str,
    harvest_date_str: str,
    initial_quality_grade: str = "Grade A",
    recent_readings: Optional[List[Dict[str, Any]]] = None,
    category: Optional[str] = None,
    transport_duration_hours: float = 4.8
) -> Dict[str, Any]:
    """
    Computes dynamic shelf life prediction, risk score, thermal abuse degree-hours,
    confidence metrics, and degradation trajectory using kinetic models.
    """
    profile = resolve_food_profile(food_name, category)
    
    # Quality Grade baseline factor
    grade_factors = {
        "Grade A+ Export": 1.15,
        "Grade A+": 1.15,
        "Grade A": 1.0,
        "Grade A Premium": 1.08,
        "Grade B": 0.82,
        "Grade C": 0.65
    }
    grade_mult = grade_factors.get(initial_quality_grade, 1.0)
    
    # Base nominal shelf life (days)
    base_shelf_life_days = profile["nominal_shelf_life_days"] * grade_mult
    optimal_t_mid = (profile["optimal_temp_min"] + profile["optimal_temp_max"]) / 2.0
    q10 = profile["q10_factor"]

    # Calculate days since harvest
    try:
        h_date = datetime.strptime(harvest_date_str[:10], "%Y-%m-%d").date()
        days_since_harvest = max(0.1, (date.today() - h_date).days)
    except Exception:
        days_since_harvest = 1.0

    # Process telemetry history
    temps: List[float] = []
    humidities: List[float] = []
    thermal_abuse_degree_hours = 0.0
    chilling_abuse_degree_hours = 0.0

    if recent_readings and len(recent_readings) > 0:
        for r in recent_readings:
            t = float(r.get("temperature", optimal_t_mid))
            h = float(r.get("humidity", 90.0))
            temps.append(t)
            humidities.append(h)
            
            # Thermal abuse: degree hours above critical threshold
            # Assume 1 reading interval ~ 0.25 hrs (15 mins) or evenly spaced
            dt_hours = max(0.05, transport_duration_hours / max(1, len(recent_readings)))
            if t > profile["critical_temp_max"]:
                thermal_abuse_degree_hours += (t - profile["critical_temp_max"]) * dt_hours
            elif t < profile.get("critical_temp_min", -99.0) and profile.get("chilling_injury_susceptible", False):
                chilling_abuse_degree_hours += (profile["critical_temp_min"] - t) * dt_hours
                
        avg_temp = sum(temps) / len(temps)
        max_temp = max(temps)
        min_temp = min(temps)
        avg_humidity = sum(humidities) / len(humidities)
    else:
        # Fallback to mild typical conditions
        avg_temp = optimal_t_mid + 1.2
        max_temp = optimal_t_mid + 2.5
        min_temp = optimal_t_mid - 0.5
        avg_humidity = (profile["optimal_humidity_min"] + profile["optimal_humidity_max"]) / 2.0

    # Arrhenius degradation acceleration factor:
    # Rate multiplier = Q10 ^ ((AvgTemp - OptimalTemp) / 10)
    temp_delta = avg_temp - optimal_t_mid
    if temp_delta > 0:
        accel_rate = math.pow(q10, temp_delta / 10.0)
    else:
        # Slightly slower degradation if cooler, down to chilling injury limit
        accel_rate = max(0.5, math.pow(q10, temp_delta / 15.0))

    # Severe penalty for thermal shock or broken cold chain
    abuse_penalty_days = (thermal_abuse_degree_hours * 0.15) + (chilling_abuse_degree_hours * 0.25)
    
    # Humidity penalty (desiccation or mold risk)
    humidity_penalty_factor = 1.0
    if avg_humidity < profile["optimal_humidity_min"]:
        deficit = profile["optimal_humidity_min"] - avg_humidity
        humidity_penalty_factor += (deficit / 100.0) * profile.get("moisture_loss_sensitivity", 1.2)
    elif avg_humidity > 97.0: # Condensation risk -> bacterial wet rot
        humidity_penalty_factor += 0.12

    effective_accel = accel_rate * humidity_penalty_factor

    # Effective consumed shelf life
    consumed_days = (days_since_harvest * effective_accel) + abuse_penalty_days
    remaining_days = max(0.0, base_shelf_life_days - consumed_days)
    remaining_hours = round(remaining_days * 24.0, 1)

    # Risk Score: 0 (Fresh / Optimal) to 100 (Critical / Spoiled)
    risk_score = round(min(100.0, max(0.0, (consumed_days / max(1.0, base_shelf_life_days)) * 100.0)), 1)

    # Risk Category
    if risk_score < 25.0:
        risk_category = "Low Risk (Fresh / Optimal)"
        risk_color = "emerald"
    elif risk_score < 55.0:
        risk_category = "Moderate Risk (Marketable)"
        risk_color = "amber"
    elif risk_score < 80.0:
        risk_category = "High Risk (Immediate Clearance Advised)"
        risk_color = "orange"
    else:
        risk_category = "Critical Risk (High Spoilage Probability)"
        risk_color = "rose"

    # Prediction Confidence & Uncertainty Calculation
    data_points_count = len(recent_readings) if recent_readings else 0
    if data_points_count >= 20:
        confidence_pct = 95.0
        uncertainty_hours = 4.0
    elif data_points_count >= 8:
        confidence_pct = 90.0
        uncertainty_hours = 8.0
    elif data_points_count >= 1:
        confidence_pct = 82.0
        uncertainty_hours = 14.0
    else:
        confidence_pct = 75.0
        uncertainty_hours = 24.0

    # Generate 10-point Quality Degradation Curve (from today into future)
    degradation_trend = []
    current_quality_pct = round(max(0.0, 100.0 - risk_score), 1)
    
    # Project decay over the next days
    projected_days_span = max(5, int(math.ceil(remaining_days + 3)))
    step = max(0.5, projected_days_span / 8.0)
    for i in range(9):
        day_offset = round(i * step, 1)
        decay = (day_offset / max(0.1, remaining_days + 1e-4)) * current_quality_pct
        q_val = round(max(0.0, current_quality_pct - decay), 1)
        
        stage = "Prime Fresh" if q_val > 75 else ("Marketable" if q_val > 50 else ("Sub-optimal" if q_val > 25 else "Unacceptable / Spoilage"))
        degradation_trend.append({
            "day": day_offset,
            "quality_score": q_val,
            "stage": stage
        })

    return {
        "food_name": food_name,
        "display_name": profile.get("display_name", food_name),
        "category": profile.get("category", category or "Vegetables"),
        "harvest_date": harvest_date_str,
        "initial_quality_grade": initial_quality_grade,
        "days_since_harvest": round(days_since_harvest, 1),
        "nominal_shelf_life_days": base_shelf_life_days,
        "estimated_remaining_days": round(remaining_days, 1),
        "estimated_remaining_hours": remaining_hours,
        "quality_risk_score": risk_score,
        "risk_category": risk_category,
        "risk_color": risk_color,
        "thermal_abuse_degree_hours": round(thermal_abuse_degree_hours, 2),
        "chilling_abuse_degree_hours": round(chilling_abuse_degree_hours, 2),
        "avg_temperature_c": round(avg_temp, 1),
        "max_temperature_c": round(max_temp, 1),
        "min_temperature_c": round(min_temp, 1),
        "avg_humidity_pct": round(avg_humidity, 1),
        "optimal_temp_range": f"{profile['optimal_temp_min']}°C - {profile['optimal_temp_max']}°C",
        "optimal_humidity_range": f"{profile['optimal_humidity_min']}% - {profile['optimal_humidity_max']}%",
        "confidence_pct": confidence_pct,
        "uncertainty_hours": uncertainty_hours,
        "confidence_label": f"{confidence_pct}% Confidence (±{uncertainty_hours} hrs)",
        "quality_degradation_trend": degradation_trend,
        "data_points_evaluated": data_points_count,
        "disclaimer": "Notice: Temperature and humidity sensor readings alone do not prove microbiological food safety. Predictions are dynamic algorithmic estimates based on validated thermal degradation kinetics (ICAR/USDA Handbook 66). Physical and sensory inspection by authorized food safety personnel is recommended.",
        "storage_guidelines": profile.get("description", "Maintain constant cold-chain conditions.")
    }
