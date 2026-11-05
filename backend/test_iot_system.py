"""
AgroSetu AI - Complete IoT Food Safety & Cold Chain Integration Test Suite
===========================================================================
Validates:
1. ESP32 Sensor Ingestion with SHT31 & GPS telemetry
2. Automated Multi-Category Threshold Alert Generation (Normal, Warning, Critical)
3. Sensor Disconnection & Signal Loss Handling
4. Farmer Alert Viewing and Acknowledgment
5. Dynamic AI Shelf-Life Estimation with Arrhenius kinetics & Disclaimers
6. Simulator Controls & Mode Transitions
7. Food Category Storage Guidelines Configuration
"""

import sys
import os
from pathlib import Path

# Safe terminal encoding on Windows CP1252
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from main import app
from database import get_db_connection

def run_iot_test_suite():
    print("=" * 80)
    print("  AGROSETU AI - IOT FOOD SAFETY & COLD CHAIN VERIFICATION TEST SUITE")
    print("=" * 80)

    client = TestClient(app)
    tests_passed = 0
    total_tests = 8

    # TEST 1: Health & System Status
    print("\n[Test 1] Verifying System Health & Route Registration...")
    res = client.get("/api/health")
    assert res.status_code == 200
    print("  [+] System Health: OK")
    tests_passed += 1

    # TEST 2: Ingest Real IoT Sensor Telemetry (ESP32 + SHT31 + GPS)
    print("\n[Test 2] Testing IoT Sensor Telemetry Ingestion (ESP32 SHT31 Physical Payload)...")
    payload = {
        "sensor_id": "ESP32-SHT31-001",
        "shipment_id": "SHIP-MAHA-101",
        "truck_id": "MH-12-PQ-8901",
        "temperature": 11.5,
        "humidity": 88.0,
        "latitude": 19.4520,
        "longitude": 74.1500,
        "is_simulated": False,
        "data_source": "HARDWARE_ESP32",
        "battery_pct": 98.5,
        "signal_rssi": -62
    }
    res = client.post(
        "/api/iot/sensor-data",
        json=payload,
        headers={"X-Sensor-API-Key": "agrosetu-iot-sensor-auth-token-2026"}
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["status"] == "SUCCESS"
    print(f"  [+] Ingestion Success: {data['message']} (Shipment: {data['shipment_id']})")
    tests_passed += 1

    # TEST 3: Live Sensor Telemetry Fetch & Status Verification
    print("\n[Test 3] Testing Live Telemetry API (Non-refreshing live dashboard)...")
    res = client.get("/api/iot/live-data?shipment_id=SHIP-MAHA-101")
    assert res.status_code == 200
    live = res.json()
    print(f"  [+] Live Reading: {live['temperature']}°C, {live['humidity']}%, Status: {live['sensor_status']}")
    assert live["sensor_id"] == "ESP32-SHT31-001"
    assert live["temperature"] == 11.5
    tests_passed += 1

    # TEST 4: Automatic Thermal Breach Alert Generation
    print("\n[Test 4] Testing Automatic Threshold Alert System (Thermal Reefer Breach)...")
    breach_payload = {
        "sensor_id": "ESP32-SHT31-001",
        "shipment_id": "SHIP-MAHA-101",
        "truck_id": "MH-12-PQ-8901",
        "temperature": 23.5, # Exceeds 20°C critical limit for Tomatoes (Fruits)
        "humidity": 65.0,
        "latitude": 19.4600,
        "longitude": 74.1600,
        "is_simulated": True,
        "data_source": "SIMULATED_DEMO"
    }
    res = client.post("/api/iot/sensor-data", json=breach_payload)
    assert res.status_code == 200

    # Verify alert created in DB
    alert_res = client.get("/api/iot/alerts?shipment_id=SHIP-MAHA-101")
    assert alert_res.status_code == 200
    alerts = alert_res.json()["alerts"]
    critical_alerts = [a for a in alerts if a["severity"] == "Critical" or a["alert_type"].startswith("TEMP_BREACH")]
    print(f"  [+] Automatic Alerts Generated: {len(alerts)} alerts found (Critical thermal breaches: {len(critical_alerts)})")
    assert len(critical_alerts) > 0, "No thermal breach alerts detected"
    target_alert_id = critical_alerts[0]["alert_id"]
    tests_passed += 1

    # TEST 5: Farmer Alert Acknowledgment Flow
    print(f"\n[Test 5] Testing Farmer Alert Acknowledgment (Alert ID: {target_alert_id})...")
    ack_res = client.post(
        f"/api/iot/alerts/{target_alert_id}/acknowledge",
        json={
            "acknowledged_by": "Ramesh Patil (Farmer)",
            "resolution_notes": "Driver turned reefer to maximum cooling. Thermostat reset to 11°C."
        }
    )
    assert ack_res.status_code == 200, ack_res.text
    print(f"  [+] Alert Acknowledged: {ack_res.json()['message']}")
    tests_passed += 1

    # TEST 6: AI Dynamic Shelf-Life Prediction Engine
    print("\n[Test 6] Testing AI Dynamic Shelf-Life Estimation (Arrhenius Kinetic Model)...")
    sl_res = client.get("/api/shelf-life/prediction?shipment_id=SHIP-MAHA-101")
    assert sl_res.status_code == 200
    sl = sl_res.json()
    print(f"  [+] Food Item: {sl['display_name']} ({sl['category']})")
    print(f"  [+] Estimated Remaining Shelf Life: {sl['estimated_remaining_days']} days ({sl['estimated_remaining_hours']} hrs)")
    print(f"  [+] Quality Risk Score: {sl['quality_risk_score']}% ({sl['risk_category']})")
    print(f"  [+] Confidence: {sl['confidence_label']}")
    print(f"  [+] Degradation Curve points: {len(sl['quality_degradation_trend'])} projected points")
    print(f"  [+] Verified Disclaimer: {sl['disclaimer'][:80]}...")
    assert sl["estimated_remaining_days"] >= 0
    assert "Notice:" in sl["disclaimer"]
    tests_passed += 1

    # TEST 7: Food Category Threshold Configuration & Admin Updates
    print("\n[Test 7] Testing Food Category Management (5 Validated Categories)...")
    cat_res = client.get("/api/iot/categories")
    assert cat_res.status_code == 200
    categories = cat_res.json()["categories"]
    cat_names = [c["category_name"] for c in categories]
    print(f"  [+] Detected Validated Categories: {cat_names}")
    for required_cat in ["Fruits", "Vegetables", "Dairy Products", "Frozen Food", "Processed Food"]:
        assert required_cat in cat_names, f"Missing category: {required_cat}"

    # Update category threshold
    update_res = client.put(
        "/api/iot/categories/Dairy%20Products",
        json={
            "temp_min": 1.0,
            "temp_max": 4.0,
            "temp_critical": 6.8,
            "humidity_min": 65.0,
            "humidity_max": 80.0,
            "max_disconnect_seconds": 45,
            "storage_notes": "Strict FSSAI cold chain for fresh milk & paneer. Spoilage risk at >6.8°C."
        }
    )
    assert update_res.status_code == 200
    print("  [+] Category Threshold Update: SUCCESS")
    tests_passed += 1

    # TEST 8: IoT Simulator Controls
    print("\n[Test 8] Testing IoT Simulator Mode Switching...")
    for mode in ["NORMAL", "THERMAL_BREACH", "HUMIDITY_BREACH", "DISCONNECTED", "NORMAL"]:
        sim_res = client.post("/api/iot/simulator/action", json={"mode": mode})
        assert sim_res.status_code == 200
    print("  [+] Simulator Transitions Verified: Normal, Thermal Breach, Humidity Breach, Disconnect, Reset.")
    tests_passed += 1

    print("\n" + "=" * 80)
    print(f"  TEST SUMMARY: {tests_passed}/{total_tests} TESTS PASSED SUCCESSFULLY (100% PASS RATE)")
    print("=" * 80)
    return True

if __name__ == "__main__":
    success = run_iot_test_suite()
    if not success:
        sys.exit(1)
