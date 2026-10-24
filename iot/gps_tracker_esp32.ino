/**
 * IoT-GPS-01 - ESP32 GPS Tracker for Field Practice Excursions
 * Hardware: ESP32 DevKit + NEO-6M GPS Module
 * Communication: WiFi + HTTP REST API
 * 
 * Course compliance:
 * - IoT Fundamentals: Sensors (GPS), Controller (ESP32)
 * - Communication: WiFi, HTTP REST
 * - Protocol: Custom JSON over HTTP (MQTT optional upgrade)
 * - Power: USB/5V (Battery with solar panel optional)
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <TinyGPS++.h>
#include <ArduinoJson.h>

// ============ CONFIGURATION ============
const char* WIFI_SSID = "SIPAM_NETWORK";           // WiFi Network
const char* WIFI_PASSWORD = "sipam2024secure";      // WiFi Password

// SIPAM Backend API
const char* API_BASE_URL = "http://18.222.152.152:8000/api/v1";
const char* API_KEY = "iot_device_key_12345";       // Device authentication

// Pin definitions for ESP32
#define GPS_RX_PIN 34          // GPS Module TX -> ESP32 GPIO34 (RX)
#define GPS_TX_PIN 12          // GPS Module RX -> ESP32 GPIO12 (TX)
#define LED_STATUS 2           // Built-in LED for status
#define BUTTON_SEND 0          // BOOT button for manual trigger

// Timing
#define SEND_INTERVAL 30000  // Send every 30 seconds
#define WIFI_TIMEOUT 10000     // WiFi connection timeout (10s)

// ============ GLOBALS ============
TinyGPSPlus gps;
HardwareSerial gpsSerial(1);
unsigned long lastSendTime = 0;
bool deviceActive = true;

// Practice session ID (configured at startup)
String practiceId = "PRAC_001";
String deviceId = "ESP32_GPS_001";

// ============ SETUP ============
void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("\n========================================");
  Serial.println("  SIPAM GPS Tracker - IoT Module");
  Serial.println("  ESP32 + NEO-6M GPS");
  Serial.println("========================================\n");
  
  // Initialize pins
  pinMode(LED_STATUS, OUTPUT);
  pinMode(BUTTON_SEND, INPUT_PULLUP);
  
  // Initialize GPS serial (UART1)
  gpsSerial.begin(9600, SERIAL_8N1, GPS_RX_PIN, GPS_TX_PIN);
  Serial.println("[GPS] Serial initialized at 9600 baud");
  
  // Connect to WiFi
  connectWiFi();
  
  // LED blink: Ready
  blinkLED(3, 200);
  Serial.println("[SYSTEM] Setup complete. Tracking started.\n");
}

// ============ MAIN LOOP ============
void loop() {
  // Read GPS data
  while (gpsSerial.available() > 0) {
    gps.encode(gpsSerial.read());
  }
  
  // Check manual trigger (BOOT button)
  if (digitalRead(BUTTON_SEND) == LOW) {
    Serial.println("[BUTTON] Manual send triggered");
    sendLocation();
    delay(500); // Debounce
  }
  
  // Automatic send interval
  if (millis() - lastSendTime > SEND_INTERVAL) {
    if (gps.location.isValid()) {
      sendLocation();
    } else {
      Serial.println("[GPS] No valid fix yet...");
      blinkLED(2, 100); // Error blink
    }
    lastSendTime = millis();
  }
  
  // Status LED: Blink every second when active
  digitalWrite(LED_STATUS, (millis() / 1000) % 2);
}

// ============ FUNCTIONS ============

void connectWiFi() {
  Serial.print("[WiFi] Connecting to ");
  Serial.println(WIFI_SSID);
  
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  
  unsigned long startAttempt = millis();
  while (WiFi.status() != WL_CONNECTED && 
         millis() - startAttempt < WIFI_TIMEOUT) {
    delay(500);
    Serial.print(".");
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n[WiFi] Connected!");
    Serial.print("[WiFi] IP: ");
    Serial.println(WiFi.localIP());
    blinkLED(2, 200);
  } else {
    Serial.println("\n[WiFi] Connection failed!");
    blinkLED(5, 100); // Error
  }
}

void sendLocation() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[ERROR] WiFi not connected!");
    connectWiFi();
    return;
  }
  
  // Prepare JSON payload
  StaticJsonDocument<512> doc;
  
  doc["device_id"] = deviceId;
  doc["practice_id"] = practiceId;
  doc["timestamp"] = millis();
  
  // GPS Data
  if (gps.location.isValid()) {
    doc["latitude"] = gps.location.lat();
    doc["longitude"] = gps.location.lng();
    doc["altitude"] = gps.altitude.meters();
    doc["speed_kmh"] = gps.speed.kmph();
    doc["course"] = gps.course.deg();
    
    // GPS Quality
    doc["satellites"] = gps.satellites.value();
    doc["hdop"] = gps.hdop.value();
  } else {
    doc["latitude"] = nullptr;
    doc["longitude"] = nullptr;
    doc["error"] = "GPS_NO_FIX";
  }
  
  // Date/Time (if available)
  if (gps.date.isValid() && gps.time.isValid()) {
    char datetime[30];
    sprintf(datetime, "%04d-%02d-%02dT%02d:%02d:%02dZ",
            gps.date.year(), gps.date.month(), gps.date.day(),
            gps.time.hour(), gps.time.minute(), gps.time.second());
    doc["datetime_gps"] = datetime;
  }
  
  // Device status
  doc["battery_voltage"] = readBatteryVoltage();
  doc["wifi_rssi"] = WiFi.RSSI();
  doc["uptime_seconds"] = millis() / 1000;
  
  // Serialize JSON
  String jsonPayload;
  serializeJson(doc, jsonPayload);
  
  // Send HTTP POST
  HTTPClient http;
  String endpoint = String(API_BASE_URL) + "/iot/tracking/";
  
  http.begin(endpoint);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-API-Key", API_KEY);
  
  Serial.println("[HTTP] Sending location data...");
  Serial.print("[HTTP] URL: ");
  Serial.println(endpoint);
  Serial.print("[HTTP] Payload: ");
  Serial.println(jsonPayload);
  
  int httpCode = http.POST(jsonPayload);
  
  if (httpCode > 0) {
    String response = http.getString();
    Serial.print("[HTTP] Response code: ");
    Serial.println(httpCode);
    Serial.print("[HTTP] Response: ");
    Serial.println(response);
    
    if (httpCode == 200 || httpCode == 201) {
      blinkLED(1, 500); // Success
    } else {
      blinkLED(3, 100); // Warning
    }
  } else {
    Serial.print("[HTTP] Error: ");
    Serial.println(http.errorToString(httpCode));
    blinkLED(5, 100); // Error
  }
  
  http.end();
  Serial.println();
}

float readBatteryVoltage() {
  // Read battery voltage from ADC (if voltage divider connected)
  // For now, return dummy value
  return 4.2; // 4.2V = fully charged LiPo
}

void blinkLED(int times, int duration) {
  for (int i = 0; i < times; i++) {
    digitalWrite(LED_STATUS, HIGH);
    delay(duration);
    digitalWrite(LED_STATUS, LOW);
    delay(duration);
  }
}

// ============ COURSE COMPLIANCE NOTES ============
/**
 * This code demonstrates:
 * 
 * 1. IoT FUNDAMENTALS:
 *    - Sensor: GPS NEO-6M
 *    - Controller: ESP32
 *    - Actuator: LED status indicator
 * 
 * 2. COMMUNICATION:
 *    - WiFi (IEEE 802.11)
 *    - HTTP/REST API
 *    - JSON data format
 * 
 * 3. PROTOCOLS:
 *    - HTTP over TCP/IP
 *    - NMEA 0183 (GPS serial protocol)
 *    
 * 4. POWER:
 *    - USB 5V power (can be upgraded to solar+battery)
 * 
 * 5. ADDITIONAL FEATURES:
 *    - JSON serialization (ArduinoJson library)
 *    - Error handling
 *    - LED status indicators
 *    - Manual trigger button
 *    - WiFi reconnection logic
 */
