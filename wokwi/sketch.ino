#include <WiFi.h>
#include <PubSubClient.h>

const int BUTTON_PIN = 4;
const int LED_PIN = 2;
const char *MQTT_TOPIC = "focus/lab5/7e4af1c93b8d451f/reaction";

WiFiClient wifiClient;
PubSubClient mqtt(wifiClient);

enum State { IDLE, WAITING, READY };
State state = IDLE;
unsigned long waitStarted = 0;
unsigned long waitTime = 0;
unsigned long signalStarted = 0;
unsigned long lastConnectionAttempt = 0;
unsigned long lastWifiAttempt = 0;
unsigned long buttonChanged = 0;
bool lastReading = HIGH;
bool buttonState = HIGH;
bool wifiReported = false;

void connectNetwork() {
  if (WiFi.status() != WL_CONNECTED) {
    wifiReported = false;
    if (millis() - lastWifiAttempt >= 60000) {
      lastWifiAttempt = millis();
      Serial.println("Reconnecting to Wi-Fi...");
      WiFi.reconnect();
    }
    return;
  }
  if (millis() - lastConnectionAttempt < 5000) return;
  lastConnectionAttempt = millis();
  if (!mqtt.connected()) {
    if (!wifiReported) {
      Serial.println("Wi-Fi connected.");
      wifiReported = true;
    }
    String clientId = "focus-esp32-" + String((uint32_t)esp_random(), HEX);
    Serial.println(mqtt.connect(clientId.c_str()) ? "MQTT connected." : "MQTT connection failed.");
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(true);
  Serial.println("Connecting to Wi-Fi...");
  WiFi.begin("Wokwi-GUEST", "", 6);
  lastWifiAttempt = millis();
  mqtt.setServer("test.mosquitto.org", 1883);
  mqtt.setSocketTimeout(1);
  mqtt.setKeepAlive(120);
  lastConnectionAttempt = millis() - 5000;
  Serial.println("Press the button to start.");
}

void loop() {
  delay(1);
  unsigned long now = millis();
  bool reading = digitalRead(BUTTON_PIN);
  if (reading != lastReading) buttonChanged = now;
  if (now - buttonChanged >= 30 && reading != buttonState) {
    buttonState = reading;
    if (buttonState == LOW) {
      if (state == IDLE) {
        if (WiFi.status() != WL_CONNECTED || !mqtt.connected()) {
          Serial.println("Wait for Wi-Fi and MQTT connection before starting.");
        } else {
          state = WAITING;
          waitStarted = now;
          waitTime = random(1000, 3001);
          Serial.println("Training started. Wait for the light.");
        }
      } else if (state == WAITING) {
        state = IDLE;
        Serial.println("Too early. Press the button to try again.");
      } else {
        unsigned long reactionTime = buttonChanged - signalStarted;
        digitalWrite(LED_PIN, LOW);
        state = IDLE;
        Serial.printf("Reaction: %lu ms\n", reactionTime);
        if (reactionTime >= 1 && reactionTime <= 60000) {
          char payload[64];
          snprintf(payload, sizeof(payload), "{\"mode\":\"reaction\",\"reaction_time_ms\":%lu}", reactionTime);
          bool sent = mqtt.connected() && mqtt.publish(MQTT_TOPIC, payload, false);
          Serial.println(sent ? "Result sent." : "Could not send result.");
        } else {
          Serial.println("Result is outside the allowed range.");
        }
      }
    }
  }
  lastReading = reading;

  if (state == WAITING && now - waitStarted >= waitTime && reading == HIGH &&
      buttonState == HIGH && now - buttonChanged >= 30) {
    digitalWrite(LED_PIN, HIGH);
    signalStarted = now;
    state = READY;
    Serial.println("Press now!");
  } else if (state == READY && now - signalStarted > 60000) {
    digitalWrite(LED_PIN, LOW);
    state = IDLE;
    Serial.println("Time expired. Try again.");
  }

  if (state == IDLE) {
    if (WiFi.status() == WL_CONNECTED && mqtt.connected()) mqtt.loop();
    else connectNetwork();
  }
}
