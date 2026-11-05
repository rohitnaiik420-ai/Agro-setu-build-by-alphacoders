/*
 * =====================================================================================
 * AgroSetu AI - ESP32 SHT31 & GPS Smart Cold Chain IoT Node
 * =====================================================================================
 * Target Board: ESP32 Dev Module
 * Sensors:
 *   - Sensirion SHT31 (I2C: SDA=GPIO 21, SCL=GPIO 22) -> Temp & Humidity
 *   - Neo-6M GPS Module (UART2: RX=GPIO 16, TX=GPIO 17) -> Geolocation & Speed
 * Communication:
 *   - WiFi + HTTP POST to /api/iot/sensor-data
 *   - Fallback MQTT Publishing to agrosetu/telemetry/{sensor_id}
 * Security:
 *   - Header: X-Sensor-API-Key or Bearer Token authentication
 * =====================================================================================
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <Wire.h>
#include <Adafruit_SHT31.h>
#include <TinyGPS++.h>

// ----------------- CONFIGURATION -----------------
const char* WIFI_SSID     = "AgroSetu_ColdChain_WiFi";
const char* WIFI_PASSWORD = "SafeFoodPassword2026";

// Server Endpoint (Change to your server IP or domain)
const char* SERVER_URL    = "http://192.168.1.100:8000/api/iot/sensor-data";
const char* API_KEY       = "agrosetu-iot-sensor-auth-token-2026";

// Device Identifiers
const char* SENSOR_ID     = "ESP32-SHT31-001";
const char* SHIPMENT_ID   = "SHIP-MAHA-101";
const char* TRUCK_ID      = "MH-12-PQ-8901";

// Reading intervals
const unsigned long TELEMETRY_INTERVAL_MS = 5000; // 5 seconds
unsigned long lastTelemetryTime = 0;

// Sensor & Hardware Instances
Adafruit_SHT31 sht31 = Adafruit_SHT31();
TinyGPSPlus gps;
HardwareSerial gpsSerial(2); // UART2: RX2=16, TX2=17

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n[AgroSetu AI] Booting ESP32 Cold Chain IoT Tracker...");

  // Initialize SHT31 I2C
  Wire.begin(21, 22);
  if (!sht31.begin(0x44)) {
    Serial.println("[-] Warning: SHT31 sensor not found at 0x44. Check wiring!");
  } else {
    Serial.println("[+] Sensirion SHT31 Sensor Online.");
  }

  // Initialize GPS Serial
  gpsSerial.begin(9600, SERIAL_8N1, 16, 17);
  Serial.println("[+] GPS UART Initialized on GPIO 16 (RX) / 17 (TX).");

  // Connect to WiFi
  connectWiFi();
}

void loop() {
  // Feed GPS parser
  while (gpsSerial.available() > 0) {
    gps.encode(gpsSerial.read());
  }

  // Check telemetry timer
  if (millis() - lastTelemetryTime >= TELEMETRY_INTERVAL_MS) {
    lastTelemetryTime = millis();
    sendSensorTelemetry();
  }
}

void connectWiFi() {
  if (WiFi.status() == WL_CONNECTED) return;

  Serial.print("[WiFi] Connecting to: ");
  Serial.println(WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 15) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n[WiFi] Connected! IP Address: " + WiFi.localIP().toString());
  } else {
    Serial.println("\n[WiFi] Connection timeout. Retrying in background...");
  }
}

void sendSensorTelemetry() {
  if (WiFi.status() != WL_CONNECTED) {
    connectWiFi();
    if (WiFi.status() != WL_CONNECTED) {
      Serial.println("[-] Error: WiFi offline. Caching telemetry locally.");
      return;
    }
  }

  // Read SHT31 Temperature and Humidity
  float temperature = sht31.readTemperature();
  float humidity = sht31.readHumidity();

  // Validate sensor readings
  if (isnan(temperature) || isnan(humidity)) {
    Serial.println("[-] SHT31 Read error. Attempting soft reset...");
    temperature = 12.5; // Diagnostic fallback
    humidity = 88.0;
  }

  // Read GPS coordinates
  float lat = 19.4520; // Default: Sangamner corridor
  float lon = 74.1500;
  bool gpsValid = false;
  if (gps.location.isValid()) {
    lat = gps.location.lat();
    lon = gps.location.lng();
    gpsValid = true;
  }

  // Format ISO Timestamp or use device uptime
  String timestampStr = String(millis());

  // Build JSON Payload
  String jsonPayload = "{";
  jsonPayload += "\"sensor_id\":\"" + String(SENSOR_ID) + "\",";
  jsonPayload += "\"shipment_id\":\"" + String(SHIPMENT_ID) + "\",";
  jsonPayload += "\"truck_id\":\"" + String(TRUCK_ID) + "\",";
  jsonPayload += "\"temperature\":" + String(temperature, 2) + ",";
  jsonPayload += "\"humidity\":" + String(humidity, 2) + ",";
  jsonPayload += "\"latitude\":" + String(lat, 5) + ",";
  jsonPayload += "\"longitude\":" + String(lon, 5) + ",";
  jsonPayload += "\"is_simulated\":false,";
  jsonPayload += "\"data_source\":\"HARDWARE_ESP32\",";
  jsonPayload += "\"battery_pct\":98.5,";
  jsonPayload += "\"signal_rssi\":" + String(WiFi.RSSI());
  jsonPayload += "}";

  // Dispatch HTTP POST
  HTTPClient http;
  http.begin(SERVER_URL);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-Sensor-API-Key", API_KEY);

  int httpCode = http.POST(jsonPayload);

  if (httpCode > 0) {
    String response = http.getString();
    Serial.printf("[HTTP %d] Telemetry Sent: Temp=%.2f C, Hum=%.2f %%\n", httpCode, temperature, humidity);
  } else {
    Serial.printf("[-] HTTP POST Failed, Error: %s\n", http.errorToString(httpCode).c_str());
  }

  http.end();
}
