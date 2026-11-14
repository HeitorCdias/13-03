#include <Arduino.h>
#include <DHT.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>

// UNO: nenhum sinal é conectado diretamente ao ESP32.
constexpr uint8_t DHT_PIN = 2, PIR_PIN = 3, LED_PIN = 9, LDR_PIN = A0;
DHT dht(DHT_PIN, DHT22);
char input[100];
uint8_t used = 0;
bool discardLine = false, automatic = true;
uint8_t requested = 0, applied = 0;
unsigned long lastSample = 0, lastMotion = 0, lastCommand = 0;
int lightValue = 0;

// Protocolo propositalmente pequeno. Não usa String para não fragmentar a RAM.
bool extractInt(const char *json, const char *field, long &value) {
  const char *position = strstr(json, field);
  if (!position) return false;
  position = strchr(position, ':');
  if (!position) return false;
  char *end;
  value = strtol(position + 1, &end, 10);
  if (end == position + 1) return false;
  while (*end == ' ') ++end;
  return *end == ',' || *end == '}';
}

void command(const char *json) {
  if (!strstr(json, "\"light\"") || !strstr(json, "\"cmd\"")) return;
  long value;
  if (!extractInt(json, "\"value\"", value) || value < 0 || value > 255) return;
  const char *mode = strstr(json, "\"mode\"");
  if (!mode) return;
  if (strstr(mode, "\"manual\"")) automatic = false;
  else if (strstr(mode, "\"auto\"")) automatic = true;
  else return;
  requested = static_cast<uint8_t>(value);
  lastCommand = millis();
}

void setup() {
  pinMode(PIR_PIN, INPUT);
  pinMode(LED_PIN, OUTPUT);
  analogWrite(LED_PIN, 0);
  Serial.begin(115200);
  dht.begin();
  // PIR precisa de aproximadamente 60 segundos para estabilizar.
}

void loop() {
  const unsigned long now = millis();
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n') {
      if (!discardLine) { input[used] = '\0'; command(input); }
      used = 0; discardLine = false;
    } else if (c != '\r' && !discardLine) {
      if (used < sizeof(input) - 1) input[used++] = c;
      else { used = 0; discardLine = true; }
    }
  }
  bool motion = digitalRead(PIR_PIN) == HIGH && now > 60000UL;
  if (motion) lastMotion = now;
  // Não deixa iluminação manual ligada indefinidamente se o servidor parar.
  if (!automatic && now - lastCommand > 900000UL) automatic = true;
  lightValue = analogRead(LDR_PIN);
  if (automatic) {
    bool present = lastMotion != 0 && now - lastMotion < 60000UL;
    // LDR ligado a 5V e resistor de 10k a GND: escuro -> leitura baixa.
    applied = present ? constrain(map(lightValue, 80, 800, 210, 30), 30, 210) : 0;
  } else applied = requested;
  analogWrite(LED_PIN, applied);

  if (now - lastSample >= 2000UL) {
    lastSample = now;
    float temperature = dht.readTemperature(), humidity = dht.readHumidity();
    Serial.print(F("{\"type\":\"telemetry\",\"temp_c\":"));
    if (isnan(temperature)) Serial.print(F("null")); else Serial.print(temperature, 1);
    Serial.print(F(",\"humidity\":"));
    if (isnan(humidity)) Serial.print(F("null")); else Serial.print(humidity, 1);
    Serial.print(F(",\"presence\":")); Serial.print(motion ? F("true") : F("false"));
    Serial.print(F(",\"light_raw\":")); Serial.print(lightValue);
    Serial.print(F(",\"led\":")); Serial.print(applied);
    Serial.print(F(",\"mode\":\"")); Serial.print(automatic ? F("auto") : F("manual"));
    Serial.print(F("\",\"uptime_ms\":")); Serial.print(now);
    Serial.println('}');
  }
  delay(10);
}
