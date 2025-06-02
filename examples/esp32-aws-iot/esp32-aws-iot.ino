/*
 * Campo Vision - ESP32 AWS IoT Core Example
 * 
 * This sketch demonstrates how to connect an ESP32 to AWS IoT Core
 * using X.509 certificates for authentication and publish telemetry
 * data to the 'campo-vision/telemetry' topic every 5 minutes.
 * 
 * The certificates should be provisioned via the Android app.
 */

#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <SPIFFS.h>
#include <time.h>
#include <Preferences.h>

// WiFi credentials - will be set via BLE from Android app
char ssid[32];
char password[64];

// AWS IoT Core endpoint - will be set via BLE from Android app
char aws_iot_endpoint[128];

// Device ID - will be set via BLE from Android app
char device_id[32];

// Certificate file paths in SPIFFS
const char* cert_file = "/certificate.pem";
const char* key_file = "/private.key";
const char* root_ca_file = "/rootCA.pem";

// AWS IoT Core MQTT topic
const char* telemetry_topic = "campo-vision/telemetry";
const char* command_topic_prefix = "campo-vision/commands/";
char command_topic[128];

// NTP Server for time synchronization
const char* ntpServer = "pool.ntp.org";

// Telemetry send interval (5 minutes = 300,000 ms)
const unsigned long TELEMETRY_INTERVAL = 300000;
unsigned long lastTelemetrySend = 0;

// Reconnect interval (5 seconds = 5000 ms)
const unsigned long RECONNECT_INTERVAL = 5000;
unsigned long lastReconnectAttempt = 0;

// WiFi and MQTT clients
WiFiClientSecure wifiClient;
PubSubClient mqttClient(wifiClient);

// Preferences for storing configuration
Preferences preferences;

// Buffer for MQTT messages
char msg_buffer[512];

// Function prototypes
void connectToWiFi();
void connectToAWS();
void setupSPIFFS();
void loadCertificates();
void loadConfiguration();
void saveConfiguration();
void publishTelemetryData();
void callback(char* topic, byte* payload, unsigned int length);
float readTemperature();
void getGPSData(float &latitude, float &longitude);

void setup() {
  // Initialize serial communication
  Serial.begin(115200);
  delay(1000);
  Serial.println("Campo Vision - ESP32 AWS IoT Core Example");
  
  // Initialize SPIFFS
  setupSPIFFS();
  
  // Load configuration from preferences
  loadConfiguration();
  
  // Format the command topic
  sprintf(command_topic, "%s%s", command_topic_prefix, device_id);
  
  // Load certificates from SPIFFS
  loadCertificates();
  
  // Connect to WiFi
  connectToWiFi();
  
  // Configure time with NTP
  configTime(0, 0, ntpServer);
  
  // Set AWS IoT Core MQTT endpoint
  mqttClient.setServer(aws_iot_endpoint, 8883);
  mqttClient.setCallback(callback);
  
  // Connect to AWS IoT Core
  connectToAWS();
}

void loop() {
  // Check if WiFi is connected, reconnect if needed
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi connection lost, reconnecting...");
    connectToWiFi();
  }
  
  // Check if MQTT client is connected, reconnect if needed
  if (!mqttClient.connected()) {
    unsigned long now = millis();
    if (now - lastReconnectAttempt > RECONNECT_INTERVAL) {
      lastReconnectAttempt = now;
      Serial.println("MQTT connection lost, reconnecting...");
      if (connectToAWS()) {
        lastReconnectAttempt = 0;
      }
    }
  } else {
    // MQTT client is connected, process messages
    mqttClient.loop();
    
    // Check if it's time to send telemetry data
    unsigned long now = millis();
    if (now - lastTelemetrySend > TELEMETRY_INTERVAL || lastTelemetrySend == 0) {
      lastTelemetrySend = now;
      publishTelemetryData();
    }
  }
}

void setupSPIFFS() {
  if (!SPIFFS.begin(true)) {
    Serial.println("Failed to mount SPIFFS");
    return;
  }
  Serial.println("SPIFFS mounted successfully");
}

void loadConfiguration() {
  preferences.begin("campo-vision", false);
  
  // Load WiFi credentials
  String saved_ssid = preferences.getString("ssid", "");
  String saved_password = preferences.getString("password", "");
  String saved_endpoint = preferences.getString("endpoint", "");
  String saved_device_id = preferences.getString("device_id", "");
  
  if (saved_ssid.length() > 0 && saved_password.length() > 0) {
    saved_ssid.toCharArray(ssid, sizeof(ssid));
    saved_password.toCharArray(password, sizeof(password));
    Serial.println("Loaded WiFi credentials from preferences");
  } else {
    // Default values for testing (replace with your own)
    strcpy(ssid, "YourWiFiSSID");
    strcpy(password, "YourWiFiPassword");
    Serial.println("Using default WiFi credentials");
  }
  
  if (saved_endpoint.length() > 0) {
    saved_endpoint.toCharArray(aws_iot_endpoint, sizeof(aws_iot_endpoint));
    Serial.println("Loaded AWS IoT endpoint from preferences");
  } else {
    // Default endpoint for testing (replace with your own)
    strcpy(aws_iot_endpoint, "your-endpoint.iot.us-east-1.amazonaws.com");
    Serial.println("Using default AWS IoT endpoint");
  }
  
  if (saved_device_id.length() > 0) {
    saved_device_id.toCharArray(device_id, sizeof(device_id));
    Serial.println("Loaded device ID from preferences");
  } else {
    // Default device ID for testing (replace with your own)
    strcpy(device_id, "esp32-test-device");
    Serial.println("Using default device ID");
  }
  
  preferences.end();
}

void saveConfiguration(const char* new_ssid, const char* new_password, 
                      const char* new_endpoint, const char* new_device_id) {
  preferences.begin("campo-vision", false);
  
  preferences.putString("ssid", new_ssid);
  preferences.putString("password", new_password);
  preferences.putString("endpoint", new_endpoint);
  preferences.putString("device_id", new_device_id);
  
  preferences.end();
  
  // Update current values
  strcpy(ssid, new_ssid);
  strcpy(password, new_password);
  strcpy(aws_iot_endpoint, new_endpoint);
  strcpy(device_id, new_device_id);
  
  // Update command topic
  sprintf(command_topic, "%s%s", command_topic_prefix, device_id);
  
  Serial.println("Configuration saved to preferences");
}

void loadCertificates() {
  // Load certificate
  if (SPIFFS.exists(cert_file)) {
    File cert = SPIFFS.open(cert_file, "r");
    if (cert) {
      String certStr = cert.readString();
      wifiClient.setCertificate(certStr.c_str());
      cert.close();
      Serial.println("Certificate loaded");
    }
  } else {
    Serial.println("Certificate file not found");
  }
  
  // Load private key
  if (SPIFFS.exists(key_file)) {
    File key = SPIFFS.open(key_file, "r");
    if (key) {
      String keyStr = key.readString();
      wifiClient.setPrivateKey(keyStr.c_str());
      key.close();
      Serial.println("Private key loaded");
    }
  } else {
    Serial.println("Private key file not found");
  }
  
  // Load root CA
  if (SPIFFS.exists(root_ca_file)) {
    File root_ca = SPIFFS.open(root_ca_file, "r");
    if (root_ca) {
      String rootCAStr = root_ca.readString();
      wifiClient.setCACert(rootCAStr.c_str());
      root_ca.close();
      Serial.println("Root CA loaded");
    }
  } else {
    Serial.println("Root CA file not found");
  }
}

void connectToWiFi() {
  Serial.println("Connecting to WiFi...");
  
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  
  unsigned long startAttemptTime = millis();
  
  while (WiFi.status() != WL_CONNECTED && 
         millis() - startAttemptTime < 10000) {
    Serial.print(".");
    delay(100);
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println();
    Serial.print("Connected to WiFi. IP address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println();
    Serial.println("Failed to connect to WiFi");
  }
}

bool connectToAWS() {
  if (!mqttClient.connected()) {
    Serial.print("Connecting to AWS IoT Core...");
    
    if (mqttClient.connect(device_id)) {
      Serial.println("connected!");
      
      // Subscribe to command topic
      if (mqttClient.subscribe(command_topic)) {
        Serial.print("Subscribed to ");
        Serial.println(command_topic);
      } else {
        Serial.print("Failed to subscribe to ");
        Serial.println(command_topic);
      }
      
      return true;
    } else {
      Serial.print("failed, rc=");
      Serial.print(mqttClient.state());
      Serial.println(" trying again in 5 seconds");
      return false;
    }
  }
  return true;
}

void publishTelemetryData() {
  // Read sensor data
  float temperature = readTemperature();
  float latitude, longitude;
  getGPSData(latitude, longitude);
  
  // Create JSON document
  StaticJsonDocument<256> doc;
  doc["deviceId"] = device_id;
  doc["latitude"] = latitude;
  doc["longitude"] = longitude;
  doc["temperature"] = temperature;
  
  // Add battery level if available
  // doc["batteryLevel"] = readBatteryLevel();
  
  // Serialize JSON to string
  size_t messageSize = serializeJson(doc, msg_buffer);
  
  // Publish to AWS IoT Core
  Serial.println("Publishing telemetry data...");
  if (mqttClient.publish(telemetry_topic, msg_buffer, messageSize)) {
    Serial.println("Telemetry data published successfully");
  } else {
    Serial.println("Failed to publish telemetry data");
  }
}

void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Message received on topic: ");
  Serial.println(topic);
  
  // Convert payload to string
  char message[length + 1];
  memcpy(message, payload, length);
  message[length] = '\0';
  
  Serial.print("Message: ");
  Serial.println(message);
  
  // Parse JSON command
  StaticJsonDocument<256> doc;
  DeserializationError error = deserializeJson(doc, message);
  
  if (error) {
    Serial.print("deserializeJson() failed: ");
    Serial.println(error.c_str());
    return;
  }
  
  // Process command
  const char* command = doc["command"];
  
  if (strcmp(command, "restart") == 0) {
    Serial.println("Restart command received, restarting ESP32...");
    ESP.restart();
  } else if (strcmp(command, "send_telemetry") == 0) {
    Serial.println("Send telemetry command received");
    publishTelemetryData();
  } else if (strcmp(command, "update_config") == 0) {
    Serial.println("Update config command received");
    
    // Check if all required fields are present
    if (doc.containsKey("ssid") && doc.containsKey("password") && 
        doc.containsKey("endpoint") && doc.containsKey("device_id")) {
      
      const char* new_ssid = doc["ssid"];
      const char* new_password = doc["password"];
      const char* new_endpoint = doc["endpoint"];
      const char* new_device_id = doc["device_id"];
      
      // Save new configuration
      saveConfiguration(new_ssid, new_password, new_endpoint, new_device_id);
      
      Serial.println("Configuration updated, restarting...");
      delay(1000);
      ESP.restart();
    } else {
      Serial.println("Missing required configuration fields");
    }
  }
}

// Simulated sensor functions - replace with actual sensor code
float readTemperature() {
  // Simulate temperature reading (replace with actual sensor code)
  return 25.5 + (random(0, 20) - 10) / 10.0;
}

void getGPSData(float &latitude, float &longitude) {
  // Simulate GPS data (replace with actual GPS code)
  latitude = -34.6037;
  longitude = -58.3816;
}
