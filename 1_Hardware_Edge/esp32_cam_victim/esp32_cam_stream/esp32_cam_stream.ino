/*
 * esp32_cam_stream.ino
 * AI Thinker ESP32-CAM — MJPEG stream server + heartbeat to IDS dashboard
 *
 * Program via TTL: GPIO0 to GND during flash, remove after.
 * Board: "AI Thinker ESP32-CAM" in Arduino IDE
 *
 * Function:
 *   1. Connects to ESP32 DevKit AP (ESP32-IDS / ids12345)
 *   2. Serves MJPEG camera stream at http://192.168.4.2/stream
 *   3. POSTs heartbeat to Spring Boot /api/esp32/devices every 10s
 *      so dashboard shows ESP32-CAM as ONLINE
 *   4. When under attack (ICMP/UDP flood) stream naturally freezes/drops
 *      — ESP32-CAM WiFi stack gets overwhelmed, heartbeat stops
 *      — Dashboard sees no heartbeat > 45s → marks as OFFLINE/UNDER_ATTACK
 */

#include "esp_camera.h"
#include <WiFi.h>
#include <HTTPClient.h>
#include <WiFiClientSecure.h>
#include "esp_http_server.h"

// ── Network config ────────────────────────────────────────────────────────────
// Connect directly to phone hotspot (same as main ESP32)
// This lets CAM reach the laptop backend at 192.168.121.x
// Main ESP32 sniffer still captures CAM traffic (same channel)
const char* AP_SSID  = "Redmi Note 9 Pro";
const char* AP_PASS  = "asdfghjkl";
const char* BACKEND  = "ai-ids-iot-8y4f.onrender.com";  // Cloud Render URL

// ── AI Thinker ESP32-CAM pin map ─────────────────────────────────────────────
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

static httpd_handle_t camServer = NULL;

// ── MJPEG stream handler ──────────────────────────────────────────────────────
#define PART_BOUNDARY "123456789000000000000987654321"
static const char* STREAM_CT =
    "multipart/x-mixed-replace;boundary=" PART_BOUNDARY;
static const char* STREAM_BOUNDARY = "\r\n--" PART_BOUNDARY "\r\n";
static const char* STREAM_PART =
    "Content-Type: image/jpeg\r\nContent-Length: %u\r\n\r\n";

esp_err_t streamHandler(httpd_req_t* req) {
    camera_fb_t* fb = NULL;
    esp_err_t res = ESP_OK;
    char partBuf[64];

    httpd_resp_set_type(req, STREAM_CT);
    httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");

    while (true) {
        fb = esp_camera_fb_get();
        if (!fb) { res = ESP_FAIL; break; }

        httpd_resp_send_chunk(req, STREAM_BOUNDARY, strlen(STREAM_BOUNDARY));
        size_t hLen = snprintf(partBuf, sizeof(partBuf), STREAM_PART, fb->len);
        httpd_resp_send_chunk(req, partBuf, hLen);
        httpd_resp_send_chunk(req, (const char*)fb->buf, fb->len);

        esp_camera_fb_return(fb);
        if (res != ESP_OK) break;
    }
    return res;
}

void startCameraServer() {
    httpd_config_t config = HTTPD_DEFAULT_CONFIG();
    config.server_port = 80;

    httpd_uri_t streamUri = {
        .uri       = "/stream",
        .method    = HTTP_GET,
        .handler   = streamHandler,
        .user_ctx  = NULL
    };

    if (httpd_start(&camServer, &config) == ESP_OK) {
        httpd_register_uri_handler(camServer, &streamUri);
        Serial.println("[CAM] Stream server started at /stream");
    }
}

// ── Heartbeat: POST to dashboard every 10s ────────────────────────────────────
void sendHeartbeat() {
    if (WiFi.status() != WL_CONNECTED) return;
    WiFiClientSecure client;
    client.setInsecure();
    HTTPClient http;
    String url = "https://" + String(BACKEND) + "/api/esp32/devices";
    String body = "{\"devices\":[{\"id\":\"esp32-cam\",\"ip\":\"" +
                  WiFi.localIP().toString() + "\",\"status\":\"online\",\"last_seen\":0}]}";
    http.begin(client, url);
    http.addHeader("Content-Type", "application/json");
    http.setTimeout(1500);
    int code = http.POST(body);
    if (code > 0) Serial.printf("[CAM] Heartbeat sent: %d\n", code);
    else          Serial.printf("[CAM] Heartbeat failed: %s\n", http.errorToString(code).c_str());
    http.end();
}

// ── Setup ─────────────────────────────────────────────────────────────────────
void setup() {
    Serial.begin(115200);
    Serial.println("\n[CAM] ESP32-CAM IDS Node starting...");

    // Camera config
    camera_config_t config;
    config.ledc_channel = LEDC_CHANNEL_0;
    config.ledc_timer   = LEDC_TIMER_0;
    config.pin_d0       = Y2_GPIO_NUM;
    config.pin_d1       = Y3_GPIO_NUM;
    config.pin_d2       = Y4_GPIO_NUM;
    config.pin_d3       = Y5_GPIO_NUM;
    config.pin_d4       = Y6_GPIO_NUM;
    config.pin_d5       = Y7_GPIO_NUM;
    config.pin_d6       = Y8_GPIO_NUM;
    config.pin_d7       = Y9_GPIO_NUM;
    config.pin_xclk     = XCLK_GPIO_NUM;
    config.pin_pclk     = PCLK_GPIO_NUM;
    config.pin_vsync    = VSYNC_GPIO_NUM;
    config.pin_href     = HREF_GPIO_NUM;
    config.pin_sscb_sda = SIOD_GPIO_NUM;
    config.pin_sscb_scl = SIOC_GPIO_NUM;
    config.pin_pwdn     = PWDN_GPIO_NUM;
    config.pin_reset    = RESET_GPIO_NUM;
    config.xclk_freq_hz = 20000000;
    config.pixel_format = PIXFORMAT_JPEG;
    config.frame_size   = FRAMESIZE_VGA;   // 640x480
    config.jpeg_quality = 12;
    config.fb_count     = 2;

    if (esp_camera_init(&config) != ESP_OK) {
        Serial.println("[CAM] Camera init FAILED");
        return;
    }
    Serial.println("[CAM] Camera init OK");

    // Connect to ESP32 DevKit AP
    WiFi.begin(AP_SSID, AP_PASS);
    Serial.print("[CAM] Connecting to AP");
    while (WiFi.status() != WL_CONNECTED) {
        delay(500); Serial.print(".");
    }
    Serial.println("\n[CAM] Connected. IP: " + WiFi.localIP().toString());

    startCameraServer();

    Serial.println("[CAM] Ready. Stream: http://" + WiFi.localIP().toString() + "/stream");
}

// ── Loop ──────────────────────────────────────────────────────────────────────
unsigned long lastHeartbeat = 0;
void loop() {
    if (millis() - lastHeartbeat > 10000) {
        sendHeartbeat();
        lastHeartbeat = millis();
    }
    delay(100);
}
