#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include "esp_camera.h"
#include "secrets.h"

// Pinagem exclusiva do módulo AI Thinker ESP32-CAM com OV2640.
WebServer server(80);
bool cameraReady = false;
const char *headerKeys[] = {"X-Camera-Key"};

bool authorized() {
  if (server.header("X-Camera-Key") != CAMERA_KEY) {
    server.send(401, "application/json", "{\"error\":\"unauthorized\"}");
    return false;
  }
  return true;
}

void capture() {
  if (!authorized()) return;
  if (!cameraReady) { server.send(503, "text/plain", "camera unavailable"); return; }
  // Descarta o quadro previamente armazenado para capturar uma imagem recente.
  camera_fb_t *oldFrame = esp_camera_fb_get();
  if (oldFrame) esp_camera_fb_return(oldFrame);
  camera_fb_t *frame = esp_camera_fb_get();
  if (!frame) { server.send(503, "text/plain", "capture failed"); return; }
  server.sendHeader("Cache-Control", "no-store");
  server.sendHeader("X-Content-Type-Options", "nosniff");
  server.setContentLength(frame->len);
  server.send(200, "image/jpeg", "");
  WiFiClient client = server.client();
  size_t offset = 0;
  unsigned long deadline = millis();
  while (offset < frame->len && client.connected() && millis() - deadline < 5000UL) {
    size_t length = min(static_cast<size_t>(1024), frame->len - offset);
    size_t written = client.write(frame->buf + offset, length);
    offset += written;
    delay(1);
  }
  esp_camera_fb_return(frame);
  client.stop();
}

void setup() {
  Serial.begin(115200);
  pinMode(4, OUTPUT); digitalWrite(4, LOW); // Flash desligado.
  if (strlen(CAMERA_KEY) < 32 || strstr(CAMERA_KEY, "SUBSTITUA") != nullptr) {
    Serial.println("Defina CAMERA_KEY aleatoria em secrets.h antes de usar.");
    while (true) delay(1000);
  }
  camera_config_t c = {};
  c.ledc_channel = LEDC_CHANNEL_0;
  c.ledc_timer = LEDC_TIMER_0;
  c.pin_d0 = 5; c.pin_d1 = 18; c.pin_d2 = 19; c.pin_d3 = 21;
  c.pin_d4 = 36; c.pin_d5 = 39; c.pin_d6 = 34; c.pin_d7 = 35;
  c.pin_xclk = 0; c.pin_pclk = 22; c.pin_vsync = 25; c.pin_href = 23;
  c.pin_sccb_sda = 26; c.pin_sccb_scl = 27;
  c.pin_pwdn = 32; c.pin_reset = -1;
  c.xclk_freq_hz = 20000000;
  c.pixel_format = PIXFORMAT_JPEG;
  c.frame_size = FRAMESIZE_VGA;
  c.jpeg_quality = 12;
  c.fb_count = 1;
  c.fb_location = psramFound() ? CAMERA_FB_IN_PSRAM : CAMERA_FB_IN_DRAM;
  c.grab_mode = CAMERA_GRAB_WHEN_EMPTY;
  cameraReady = esp_camera_init(&c) == ESP_OK;
  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(true);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  server.collectHeaders(headerKeys, 1);
  server.on("/capture", HTTP_GET, capture);
  server.on("/health", HTTP_GET, []() {
    if (!authorized()) return;
    server.send(cameraReady ? 200 : 503, "application/json", cameraReady ? "{\"status\":\"ok\"}" : "{\"status\":\"camera_error\"}");
  });
  server.onNotFound([]() { server.send(404, "text/plain", "not found"); });
  server.begin();
}

void loop() {
  static bool announced = false;
  if (WiFi.status() == WL_CONNECTED) {
    if (!announced) { Serial.print("IP local: "); Serial.println(WiFi.localIP()); announced = true; }
    server.handleClient();
  } else announced = false;
  delay(5);
}
