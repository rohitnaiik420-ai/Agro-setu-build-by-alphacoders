"""
AgroSetu AI - Real-Time IoT Cold Chain & Food Safety Management Service
========================================================================
Manages IoT sensors (ESP32 + SHT31 + GPS), telemetry ingestion, automated
category-specific threshold alerting, connection heartbeats, and realistic
sensor simulation.
"""

import time
import math
import random
import threading
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

try:
    from backend.database import get_db_connection
    from backend.shelf_life_engine import calculate_dynamic_shelf_life, resolve_food_profile, CATEGORY_DEFAULTS
except ImportError:
    from database import get_db_connection
    from shelf_life_engine import calculate_dynamic_shelf_life, resolve_food_profile, CATEGORY_DEFAULTS

# Expected IoT API Key for hardware authentication
DEFAULT_IOT_API_KEY = "agrosetu-iot-sensor-auth-token-2026"

# In-memory fast cache for live sensor states and simulation thread state
class IoTStateManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(IoTStateManager, cls).__new__(cls)
                cls._instance._init_state()
            return cls._instance

    def _init_state(self):
        self.live_telemetry: Dict[str, Dict[str, Any]] = {}  # keyed by shipment_id or sensor_id
        self.active_alerts: List[Dict[str, Any]] = []
        self.simulation_enabled = True
        self.simulation_mode = "NORMAL"  # "NORMAL", "THERMAL_BREACH", "HUMIDITY_BREACH", "DISCONNECTED"
        self.last_sim_step = time.time()
        self._sim_thread = None
        self._stop_sim = False
        self._start_background_simulator()

    def _start_background_simulator(self):
        """Starts a lightweight periodic thread to keep demo data alive if enabled."""
        def sim_worker():
            while not self._stop_sim:
                try:
                    if self.simulation_enabled:
                        self.tick_simulator_step()
                except Exception as e:
                    print(f"[IoT Simulator Worker Note]: {e}")
                time.sleep(3.0)

        self._sim_thread = threading.Thread(target=sim_worker, daemon=True)
        self._sim_thread.start()

    def tick_simulator_step(self):
        """Generates realistic telemetry steps for all active monitored shipments."""
        with self._lock:
            mode = self.simulation_mode

            # We update default active monitored shipments
            targets = [
                {
                    "shipment_id": "SHIP-MAHA-101",
                    "sensor_id": "ESP32-SHT31-001",
                    "truck_id": "MH-12-PQ-8901",
                    "food_name": "Organic Hybrid Tomato",
                    "category": "Fruits",
                    "base_temp": 11.8,
                    "base_hum": 88.5,
                    "lat": 19.4520,
                    "lon": 74.1500
                },
                {
                    "shipment_id": "SHIP-MAHA-102",
                    "sensor_id": "ESP32-SHT31-002",
                    "truck_id": "MH-15-EG-4412",
                    "food_name": "Bhagwa Pomegranate",
                    "category": "Fruits",
                    "base_temp": 5.8,
                    "base_hum": 91.2,
                    "lat": 19.1240,
                    "lon": 74.5200
                },
                {
                    "shipment_id": "SHIP-DAIRY-301",
                    "sensor_id": "ESP32-SHT31-003",
                    "truck_id": "MH-11-DF-2299",
                    "food_name": "Raw Cow Milk",
                    "category": "Dairy Products",
                    "base_temp": 3.4,
                    "base_hum": 70.0,
                    "lat": 18.6200,
                    "lon": 73.8100
                }
            ]

            now_iso = datetime.now().isoformat()

            for tgt in targets:
                shipment_id = tgt["shipment_id"]
                sensor_id = tgt["sensor_id"]

                # If disconnected mode, simulate missing packet for primary shipment
                if mode == "DISCONNECTED" and shipment_id == "SHIP-MAHA-101":
                    # Do not generate new reading; let last_heartbeat age
                    continue

                # Compute realistic temperature & humidity with natural drift or stress injection
                noise_t = random.uniform(-0.25, 0.25)
                noise_h = random.uniform(-0.6, 0.6)

                if mode == "THERMAL_BREACH" and shipment_id == "SHIP-MAHA-101":
                    # Severe reefer malfunction: temperature spikes to 23.5°C
                    curr_entry = self.live_telemetry.get(shipment_id, {})
                    prev_temp = curr_entry.get("temperature", tgt["base_temp"])
                    temp = round(min(24.5, prev_temp + 1.2 + noise_t), 2)
                    hum = round(max(60.0, tgt["base_hum"] - 8.0 + noise_h), 1)
                elif mode == "HUMIDITY_BREACH" and shipment_id == "SHIP-MAHA-101":
                    temp = round(tgt["base_temp"] + noise_t, 2)
                    hum = round(min(99.0, 97.5 + noise_h), 1) # Excessive condensation risk
                else:
                    # Normal stable cold chain
                    curr_entry = self.live_telemetry.get(shipment_id, {})
                    prev_temp = curr_entry.get("temperature", tgt["base_temp"])
                    # Slowly gravitate back to base_temp
                    temp = round(prev_temp + (tgt["base_temp"] - prev_temp) * 0.25 + noise_t, 2)
                    hum = round(tgt["base_hum"] + noise_h, 1)

                reading_payload = {
                    "sensor_id": sensor_id,
                    "shipment_id": shipment_id,
                    "truck_id": tgt["truck_id"],
                    "temperature": temp,
                    "humidity": hum,
                    "latitude": round(tgt["lat"] + random.uniform(-0.005, 0.005), 5),
                    "longitude": round(tgt["lon"] + random.uniform(-0.005, 0.005), 5),
                    "is_simulated": True,
                    "data_source": "SIMULATED_DEMO",
                    "battery_pct": 96.0,
                    "signal_rssi": -68,
                    "timestamp": now_iso
                }

                # Ingest directly without lock recursion
                self._record_telemetry_internal(reading_payload, food_name=tgt["food_name"], category=tgt["category"])

    def _record_telemetry_internal(self, payload: Dict[str, Any], food_name: str = "Organic Hybrid Tomato", category: str = "Fruits"):
        """Internal telemetry processor and alert evaluator."""
        sensor_id = payload["sensor_id"]
        shipment_id = payload["shipment_id"]
        temp = float(payload["temperature"])
        hum = float(payload["humidity"])
        now_ts = payload.get("timestamp", datetime.now().isoformat())
        is_simulated = bool(payload.get("is_simulated", False))
        data_source = payload.get("data_source", "SIMULATED_DEMO" if is_simulated else "HARDWARE_ESP32")

        # Update Live cache
        self.live_telemetry[shipment_id] = {
            **payload,
            "status": "ONLINE",
            "last_seen_epoch": time.time(),
            "food_name": food_name,
            "category": category
        }
        self.live_telemetry[sensor_id] = self.live_telemetry[shipment_id]

        # Check threshold limits
        limits = get_category_limits(category)
        alerts_to_generate = []

        # Temperature breach check
        if temp > limits["temp_critical"]:
            alerts_to_generate.append({
                "alert_type": "TEMP_BREACH_CRITICAL_HIGH",
                "severity": "Critical",
                "parameter": "Temperature",
                "recorded_value": temp,
                "threshold_value": limits["temp_critical"],
                "message": f"CRITICAL: Cargo temperature reached {temp}°C (Critical Limit: {limits['temp_critical']}°C) for {category} ({food_name})!"
            })
        elif temp > limits["temp_max"]:
            alerts_to_generate.append({
                "alert_type": "TEMP_BREACH_HIGH",
                "severity": "Warning",
                "parameter": "Temperature",
                "recorded_value": temp,
                "threshold_value": limits["temp_max"],
                "message": f"WARNING: Temperature {temp}°C exceeded maximum recommended limit of {limits['temp_max']}°C for {category}."
            })
        elif temp < limits.get("temp_min", -99.0):
            alerts_to_generate.append({
                "alert_type": "TEMP_BREACH_LOW",
                "severity": "Warning",
                "parameter": "Temperature",
                "recorded_value": temp,
                "threshold_value": limits["temp_min"],
                "message": f"WARNING: Temperature {temp}°C below minimum safe storage limit of {limits['temp_min']}°C (Chilling Injury Risk)."
            })

        # Humidity breach check
        if hum > limits["humidity_max"]:
            alerts_to_generate.append({
                "alert_type": "HUMIDITY_BREACH_HIGH",
                "severity": "Warning",
                "parameter": "Humidity",
                "recorded_value": hum,
                "threshold_value": limits["humidity_max"],
                "message": f"WARNING: High humidity {hum}% exceeded upper threshold {limits['humidity_max']}%. Risk of fungal pathogen growth & condensation."
            })
        elif hum < limits["humidity_min"]:
            alerts_to_generate.append({
                "alert_type": "HUMIDITY_BREACH_LOW",
                "severity": "Warning",
                "parameter": "Humidity",
                "recorded_value": hum,
                "threshold_value": limits["humidity_min"],
                "message": f"WARNING: Low humidity {hum}% below {limits['humidity_min']}%. Transpirational water loss and weight shrink risk."
            })

        # Persist reading and alerts to SQLite
        try:
            conn = get_db_connection()
            c = conn.cursor()

            # Insert into Sensor_Readings
            c.execute("""
            INSERT INTO sensor_readings (
                sensor_id, shipment_id, truck_id, temperature, humidity,
                latitude, longitude, is_simulated, data_source, battery_pct, signal_rssi, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                sensor_id, shipment_id, payload.get("truck_id", ""),
                temp, hum, payload.get("latitude", 0.0), payload.get("longitude", 0.0),
                1 if is_simulated else 0, data_source,
                payload.get("battery_pct", 95.0), payload.get("signal_rssi", -65), now_ts
            ))

            # Update or register sensor record in iot_sensors
            c.execute("""
            INSERT INTO iot_sensors (sensor_id, hardware_type, status, last_heartbeat, battery_pct, is_simulator)
            VALUES (?, 'ESP32 + SHT31 + GPS', 'ONLINE', ?, ?, ?)
            ON CONFLICT(sensor_id) DO UPDATE SET
                status = 'ONLINE',
                last_heartbeat = excluded.last_heartbeat,
                battery_pct = excluded.battery_pct,
                is_simulator = excluded.is_simulator;
            """, (sensor_id, now_ts, payload.get("battery_pct", 95.0), 1 if is_simulated else 0))

            # Insert alerts if any (avoid duplicate alert spam within 2 minutes)
            for alt in alerts_to_generate:
                alert_id = f"ALT-{uuid.uuid4().hex[:8].upper()}"
                
                # Check recent active alert of same type within last 120 seconds
                recent = c.execute("""
                SELECT id FROM food_safety_alerts 
                WHERE shipment_id = ? AND alert_type = ? AND acknowledged = 0 
                AND datetime(timestamp) >= datetime('now', '-2 minutes');
                """, (shipment_id, alt["alert_type"])).fetchone()

                if not recent:
                    c.execute("""
                    INSERT INTO food_safety_alerts (
                        alert_id, shipment_id, sensor_id, truck_id, food_name, category,
                        alert_type, severity, parameter, recorded_value, threshold_value,
                        message, timestamp, acknowledged
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0);
                    """, (
                        alert_id, shipment_id, sensor_id, payload.get("truck_id", ""),
                        food_name, category, alt["alert_type"], alt["severity"], alt["parameter"],
                        alt["recorded_value"], alt["threshold_value"], alt["message"], now_ts
                    ))

            conn.commit()
            conn.close()
        except Exception as db_err:
            print(f"[IoT DB Ingest Error]: {db_err}")


# Helper to get category limits from DB or fallback
def get_category_limits(category: str) -> Dict[str, Any]:
    try:
        conn = get_db_connection()
        row = conn.cursor().execute("""
        SELECT category_name, temp_min, temp_max, temp_critical, humidity_min, humidity_max, max_disconnect_seconds, storage_notes
        FROM food_category_thresholds WHERE category_name = ?;
        """, (category,)).fetchone()
        conn.close()
        if row:
            return dict(row)
    except Exception:
        pass

    defaults = CATEGORY_DEFAULTS.get(category, CATEGORY_DEFAULTS["Vegetables"])
    return {
        "category_name": category,
        "temp_min": defaults["optimal_temp_min"],
        "temp_max": defaults["optimal_temp_max"],
        "temp_critical": defaults["critical_temp_max"],
        "humidity_min": defaults["optimal_humidity_min"],
        "humidity_max": defaults["optimal_humidity_max"],
        "max_disconnect_seconds": 60,
        "storage_notes": "Standard cold-chain storage parameters."
    }


def ingest_sensor_reading(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Public method called by POST /api/iot/sensor-data."""
    state = IoTStateManager()
    shipment_id = payload.get("shipment_id", "SHIP-MAHA-101")
    
    # Lookup food name & category from database if available
    food_name = "Organic Hybrid Tomato"
    category = "Fruits"
    try:
        conn = get_db_connection()
        row = conn.cursor().execute("""
        SELECT food_name, category FROM food_shipments WHERE shipment_id = ? OR shipment_id = (SELECT id FROM shipments WHERE tracking_no = ?);
        """, (shipment_id, shipment_id)).fetchone()
        if row:
            food_name = row["food_name"]
            category = row["category"]
        else:
            # Check shipments table cargo_description
            s_row = conn.cursor().execute("SELECT cargo_description FROM shipments WHERE tracking_no = ?;", (shipment_id,)).fetchone()
            if s_row:
                desc = s_row["cargo_description"]
                if "Tomato" in desc:
                    food_name, category = "Organic Hybrid Tomato", "Fruits"
                elif "Pomegranate" in desc:
                    food_name, category = "Bhagwa Pomegranate", "Fruits"
                elif "Milk" in desc:
                    food_name, category = "Raw Cow Milk", "Dairy Products"
                elif "Onion" in desc:
                    food_name, category = "Nashik Pink Onion", "Vegetables"
        conn.close()
    except Exception:
        pass

    state._record_telemetry_internal(payload, food_name=food_name, category=category)
    return {"status": "SUCCESS", "message": "Telemetry received and analyzed.", "shipment_id": shipment_id}


def get_live_data(shipment_id: Optional[str] = None) -> Dict[str, Any]:
    """Retrieves live sensor telemetry, sensor status, alerts, and threshold state."""
    state = IoTStateManager()
    target_id = shipment_id or "SHIP-MAHA-101"

    cached = state.live_telemetry.get(target_id)
    now_epoch = time.time()

    # Determine connection status (timeout after 45s)
    if not cached:
        # Check DB for latest reading
        try:
            conn = get_db_connection()
            row = conn.cursor().execute("""
            SELECT * FROM sensor_readings WHERE shipment_id = ? ORDER BY id DESC LIMIT 1;
            """, (target_id,)).fetchone()
            conn.close()
            if row:
                cached = dict(row)
                cached["last_seen_epoch"] = now_epoch - 15.0
            else:
                cached = {
                    "sensor_id": "ESP32-SHT31-001",
                    "shipment_id": target_id,
                    "truck_id": "MH-12-PQ-8901",
                    "temperature": 12.2,
                    "humidity": 88.0,
                    "latitude": 19.4520,
                    "longitude": 74.1500,
                    "is_simulated": True,
                    "data_source": "SIMULATED_DEMO",
                    "battery_pct": 98.0,
                    "signal_rssi": -65,
                    "timestamp": datetime.now().isoformat(),
                    "last_seen_epoch": now_epoch
                }
        except Exception:
            pass

    last_seen_epoch = cached.get("last_seen_epoch", now_epoch)
    elapsed_seconds = int(now_epoch - last_seen_epoch)

    # Disconnection detection
    is_offline = (state.simulation_mode == "DISCONNECTED" and target_id == "SHIP-MAHA-101") or elapsed_seconds > 45
    sensor_status = "OFFLINE" if is_offline else ("DEGRADED" if elapsed_seconds > 20 else "ONLINE")

    # If sensor disconnected, insert critical disconnect alert if not existing
    if is_offline:
        try:
            conn = get_db_connection()
            c = conn.cursor()
            existing_disc = c.execute("""
            SELECT id FROM food_safety_alerts 
            WHERE shipment_id = ? AND alert_type = 'SENSOR_DISCONNECTED' AND acknowledged = 0;
            """, (target_id,)).fetchone()
            if not existing_disc:
                alert_id = f"ALT-{uuid.uuid4().hex[:8].upper()}"
                c.execute("""
                INSERT INTO food_safety_alerts (
                    alert_id, shipment_id, sensor_id, truck_id, food_name, category,
                    alert_type, severity, parameter, recorded_value, threshold_value,
                    message, timestamp, acknowledged
                ) VALUES (?, ?, ?, ?, 'Cold Chain Cargo', 'Perishables', 'SENSOR_DISCONNECTED', 'Critical', 'Connectivity',
                          0, 45, 'CRITICAL: Sensor disconnected or signal lost! No telemetry received for > 45 seconds.', ?, 0);
                """, (alert_id, target_id, cached.get("sensor_id", "ESP32-SHT31-001"), cached.get("truck_id", ""), datetime.now().isoformat()))
                conn.commit()
            conn.close()
        except Exception:
            pass

    # Food info & thresholds
    category = cached.get("category", "Fruits")
    food_name = cached.get("food_name", "Organic Hybrid Tomato")
    limits = get_category_limits(category)

    # Compute status of current temp and humidity
    curr_t = float(cached.get("temperature", 12.0))
    curr_h = float(cached.get("humidity", 88.0))

    if curr_t > limits["temp_critical"]:
        t_status = "CRITICAL_HIGH"
    elif curr_t > limits["temp_max"]:
        t_status = "WARNING_HIGH"
    elif curr_t < limits.get("temp_min", -99.0):
        t_status = "WARNING_LOW"
    else:
        t_status = "OPTIMAL"

    if curr_h > limits["humidity_max"]:
        h_status = "WARNING_HIGH"
    elif curr_h < limits["humidity_min"]:
        h_status = "WARNING_LOW"
    else:
        h_status = "OPTIMAL"

    # Fetch active alerts for this shipment
    alerts = []
    try:
        conn = get_db_connection()
        rows = conn.cursor().execute("""
        SELECT * FROM food_safety_alerts 
        WHERE shipment_id = ? ORDER BY id DESC LIMIT 5;
        """, (target_id,)).fetchall()
        alerts = [dict(r) for r in rows]
        conn.close()
    except Exception:
        pass

    return {
        "shipment_id": target_id,
        "sensor_id": cached.get("sensor_id", "ESP32-SHT31-001"),
        "truck_id": cached.get("truck_id", "MH-12-PQ-8901"),
        "food_name": food_name,
        "category": category,
        "temperature": curr_t,
        "humidity": curr_h,
        "temp_status": t_status,
        "humidity_status": h_status,
        "latitude": cached.get("latitude", 19.4520),
        "longitude": cached.get("longitude", 74.1500),
        "sensor_status": sensor_status,
        "is_simulated": bool(cached.get("is_simulated", True)),
        "data_source": cached.get("data_source", "SIMULATED_DEMO"),
        "simulation_mode": state.simulation_mode,
        "battery_pct": cached.get("battery_pct", 96.0),
        "signal_rssi": cached.get("signal_rssi", -68),
        "last_updated": cached.get("timestamp", datetime.now().isoformat()),
        "seconds_since_last_packet": elapsed_seconds,
        "category_limits": limits,
        "active_alerts_count": len([a for a in alerts if not a.get("acknowledged")]),
        "recent_alerts": alerts
    }


def get_telemetry_history(shipment_id: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
    """Fetches historical temperature and humidity data for charts."""
    target_id = shipment_id or "SHIP-MAHA-101"
    try:
        conn = get_db_connection()
        rows = conn.cursor().execute("""
        SELECT id, sensor_id, shipment_id, truck_id, temperature, humidity,
               latitude, longitude, is_simulated, data_source, timestamp
        FROM sensor_readings
        WHERE shipment_id = ?
        ORDER BY id DESC LIMIT ?;
        """, (target_id, limit)).fetchall()
        conn.close()
        records = [dict(r) for r in reversed(rows)]
    except Exception:
        records = []

    # If empty, create initial realistic series so the charts have rich data
    if not records:
        base_t = 11.5
        base_h = 88.0
        now = datetime.now()
        for i in range(20):
            t_offset = now - timedelta(minutes=(20 - i) * 5)
            records.append({
                "id": i + 1,
                "sensor_id": "ESP32-SHT31-001",
                "shipment_id": target_id,
                "truck_id": "MH-12-PQ-8901",
                "temperature": round(base_t + math.sin(i / 3.0) * 0.8 + random.uniform(-0.2, 0.2), 2),
                "humidity": round(base_h + math.cos(i / 4.0) * 1.5 + random.uniform(-0.5, 0.5), 1),
                "is_simulated": 1,
                "data_source": "SIMULATED_DEMO",
                "timestamp": t_offset.strftime("%H:%M:%S")
            })

    temps = [r["temperature"] for r in records]
    hums = [r["humidity"] for r in records]

    return {
        "shipment_id": target_id,
        "count": len(records),
        "readings": records,
        "stats": {
            "min_temperature": min(temps) if temps else 0.0,
            "max_temperature": max(temps) if temps else 0.0,
            "avg_temperature": round(sum(temps) / len(temps), 2) if temps else 0.0,
            "min_humidity": min(hums) if hums else 0.0,
            "max_humidity": max(hums) if hums else 0.0,
            "avg_humidity": round(sum(hums) / len(hums), 2) if hums else 0.0
        }
    }


def get_all_alerts(shipment_id: Optional[str] = None, acknowledged: Optional[bool] = None) -> List[Dict[str, Any]]:
    """Returns alerts with optional filters."""
    try:
        conn = get_db_connection()
        query = "SELECT * FROM food_safety_alerts WHERE 1=1"
        params = []
        if shipment_id:
            query += " AND shipment_id = ?"
            params.append(shipment_id)
        if acknowledged is not None:
            query += " AND acknowledged = ?"
            params.append(1 if acknowledged else 0)
        query += " ORDER BY id DESC LIMIT 100;"

        rows = conn.cursor().execute(query, params).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception:
        return []


def acknowledge_alert(alert_id: str, acknowledged_by: str = "Farmer Ramesh Patil", resolution_notes: str = "") -> bool:
    """Marks an alert as acknowledged."""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("""
        UPDATE food_safety_alerts
        SET acknowledged = 1,
            acknowledged_by = ?,
            acknowledged_at = ?,
            resolution_notes = ?
        WHERE alert_id = ? OR id = ?;
        """, (acknowledged_by, datetime.now().isoformat(), resolution_notes, alert_id, alert_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"[Acknowledge Alert Error]: {e}")
        return False
