"""
AgroSetu AI - MQTT Cold Chain IoT Gateway Bridge
=================================================
Listens for telemetry published over MQTT topics (e.g. from ESP32 gateways)
and routes messages into the AgroSetu IoT ingestion service.
"""

import json
import os
import threading
from typing import Optional

try:
    import paho.mqtt.client as mqtt
    PAHO_AVAILABLE = True
except ImportError:
    PAHO_AVAILABLE = False

try:
    from backend.iot_manager import ingest_sensor_reading
except ImportError:
    from iot_manager import ingest_sensor_reading

MQTT_BROKER = os.environ.get("MQTT_BROKER", "broker.hivemq.com")
MQTT_PORT = int(os.environ.get("MQTT_PORT", 1883))
MQTT_TOPIC_TELEMETRY = "agrosetu/telemetry/#"

class MQTTColdChainBridge:
    def __init__(self, broker: str = MQTT_BROKER, port: int = MQTT_PORT):
        self.broker = broker
        self.port = port
        self.client: Optional[Any] = None
        self.connected = False
        self._thread: Optional[threading.Thread] = None

    def start(self):
        if not PAHO_AVAILABLE:
            print("[MQTT Bridge] Note: paho-mqtt not available or skipped.")
            return

        def run():
            try:
                # Use CallbackAPIVersion if available in paho 2.x
                if hasattr(mqtt, "CallbackAPIVersion"):
                    self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="AgroSetu_Backend_Gateway")
                else:
                    self.client = mqtt.Client(client_id="AgroSetu_Backend_Gateway")

                self.client.on_connect = self._on_connect
                self.client.on_message = self._on_message
                self.client.connect_async(self.broker, self.port, 60)
                self.client.loop_start()
                print(f"[MQTT Bridge] Started background client connecting to {self.broker}:{self.port}")
            except Exception as e:
                print(f"[MQTT Bridge Note]: Connection could not be established: {e}")

        self._thread = threading.Thread(target=run, daemon=True)
        self._thread.start()

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            self.connected = True
            print(f"[MQTT Bridge] Connected successfully to MQTT Broker: {self.broker}")
            client.subscribe(MQTT_TOPIC_TELEMETRY)
        else:
            print(f"[MQTT Bridge] Connection failed with code {rc}")

    def _on_message(self, client, userdata, msg):
        try:
            payload_str = msg.payload.decode('utf-8', errors='ignore')
            data = json.loads(payload_str)
            ingest_sensor_reading(data)
        except Exception as e:
            print(f"[MQTT Ingest Error]: {e}")

# Global instance
mqtt_bridge = MQTTColdChainBridge()

def start_mqtt_bridge():
    """Initializes the background MQTT listener."""
    mqtt_bridge.start()
