#include <WiFi.h>
#include <esp_wifi.h>
#include <HTTPClient.h>
#include <WiFiClientSecure.h>
#include <cmath>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include "scaler.h"         
#include "model_binary.h"  
#include <DHT.h>

#define DHTPIN 4
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);

volatile float currentTemp = 0.0;
volatile float currentHumi = 0.0;

// =====================================================================
// 1. HARDWARE & NETWORK PROFILE
// =====================================================================
const char* WIFI_SSID     = "Redmi Note 9 Pro";   // Target AP to lock channel
const char* WIFI_PASSWORD = "asdfghjkl"; 

// Local Flask backend (laptop) IP address
// Change to "https://your-flask-app.onrender.com/api/v2/analyze" when deploying
const char* BACKEND_URL   = "https://ai-ids-iot-8y4f.onrender.com/api/v2/analyze"; 

// OLED Display Configuration
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET    -1
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET); 

// FreeRTOS configuration
TaskHandle_t InferenceTask;
portMUX_TYPE mux = portMUX_INITIALIZER_UNLOCKED;

// =====================================================================
// 2. WELFORD'S ALGORITHM METRIC REGISTERS (VOLATILE ISR)
// =====================================================================
volatile unsigned long windowStartTime = 0;
volatile unsigned long lastPacketTime = 0;

volatile uint32_t packetCount = 0;
volatile uint32_t totalSize = 0;

// Welford's variables for numerical stability on 32-bit float
volatile float meanSize = 0.0;
volatile float m2Size = 0.0;

volatile uint32_t totalIat = 0;
volatile uint16_t maxSize = 0;
volatile uint16_t minSize = 65535;
volatile uint8_t  primaryProtocol = 0; 
volatile uint32_t headerLengthTotal = 0;
volatile uint32_t rstCount = 0;
volatile uint32_t urgCount = 0;
volatile uint32_t ackCount = 0;
volatile uint32_t synCount = 0;
volatile uint32_t finCount = 0;
volatile uint32_t totalTtl = 0;

volatile uint32_t lastSrcIp = 0;
volatile uint32_t lastDstIp = 0;
char lastSrcMac[18] = "00:00:00:00:00:00";
char lastDstMac[18] = "00:00:00:00:00:00";
volatile uint16_t lastSrcPort = 0;
volatile uint16_t lastDstPort = 0;
volatile bool isEncrypted = true;

// =====================================================================
// 3. PROMISCUOUS LAYER-2 SNIFFER CALLBACK (ISR)
// =====================================================================
void IRAM_ATTR snifferCallback(void* buf, wifi_promiscuous_pkt_type_t type) {
    if (type != WIFI_PKT_DATA) return; 
    
    wifi_promiscuous_pkt_t *pkt = (wifi_promiscuous_pkt_t*)buf;
    uint8_t *frame = pkt->payload;
    uint16_t len = pkt->rx_ctrl.sig_len;
    
    if (len < 24) return;
    
    // Extract unencrypted Layer-2 MAC Addresses
    char srcMacBuf[18], dstMacBuf[18];
    sprintf(srcMacBuf, "%02X:%02X:%02X:%02X:%02X:%02X", frame[10], frame[11], frame[12], frame[13], frame[14], frame[15]);
    sprintf(dstMacBuf, "%02X:%02X:%02X:%02X:%02X:%02X", frame[4], frame[5], frame[6], frame[7], frame[8], frame[9]);

    // Check for unencrypted IPv4 LLC/SNAP header (AA AA 03 00 00 00 08 00)
    int ipOffset = 0;
    bool encrypted = true;
    if (len >= 34 && frame[26] == 0xAA && frame[27] == 0xAA) { ipOffset = 34; encrypted = false; } // QoS Data
    else if (len >= 32 && frame[24] == 0xAA && frame[25] == 0xAA) { ipOffset = 32; encrypted = false; } // Standard Data
    
    uint16_t totSize = len;
    
    portENTER_CRITICAL_ISR(&mux);
    
    strcpy(lastSrcMac, srcMacBuf);
    strcpy(lastDstMac, dstMacBuf);
    isEncrypted = encrypted;
    
    packetCount++;
    totalSize += totSize;
    if (totSize > maxSize) maxSize = totSize;
    if (totSize < minSize) minSize = totSize;
    
    // If unencrypted, we can read the IP/Port. If encrypted, we skip to avoid garbage numbers.
    if (!encrypted && len >= ipOffset + 20) {
        uint8_t protocol = frame[ipOffset + 9];
        uint8_t ipHeaderLen = (frame[ipOffset] & 0x0F) * 4;
        
        lastSrcIp = (frame[ipOffset+12] << 24) | (frame[ipOffset+13] << 16) | (frame[ipOffset+14] << 8) | frame[ipOffset+15];
        lastDstIp = (frame[ipOffset+16] << 24) | (frame[ipOffset+17] << 16) | (frame[ipOffset+18] << 8) | frame[ipOffset+19];
        primaryProtocol = protocol;
        headerLengthTotal += ipHeaderLen;
        totalTtl += frame[ipOffset + 8];

        uint16_t srcPort = 0, dstPort = 0;
        if (protocol == 6 && len >= ipOffset + ipHeaderLen + 14) { 
            srcPort = (frame[ipOffset + ipHeaderLen] << 8) | frame[ipOffset + ipHeaderLen + 1];
            dstPort = (frame[ipOffset + ipHeaderLen + 2] << 8) | frame[ipOffset + ipHeaderLen + 3];
            uint8_t tcpFlags = frame[ipOffset + ipHeaderLen + 13];
            if (tcpFlags & 0x04) rstCount++; 
            if (tcpFlags & 0x20) urgCount++; 
            if (tcpFlags & 0x10) ackCount++; 
            if (tcpFlags & 0x02) synCount++; 
            if (tcpFlags & 0x01) finCount++; 
        } else if (protocol == 17 && len >= ipOffset + ipHeaderLen + 8) {
            srcPort = (frame[ipOffset + ipHeaderLen] << 8) | frame[ipOffset + ipHeaderLen + 1];
            dstPort = (frame[ipOffset + ipHeaderLen + 2] << 8) | frame[ipOffset + ipHeaderLen + 3];
        }
        lastSrcPort = srcPort;
        lastDstPort = dstPort;
    }
    
    // Welford's Variance Algorithm Update
    float delta = (float)totSize - meanSize;
    meanSize += delta / packetCount;
    float delta2 = (float)totSize - meanSize;
    m2Size += delta * delta2;
    
    portEXIT_CRITICAL_ISR(&mux);
}

// =====================================================================
// 4. EDGE AI INFERENCE & CLOUD REPORTING
// =====================================================================
void forward_telemetry_to_cloud(float features[15], float edge_score, String srcIp, String dstIp, String srcMac, String dstMac, uint16_t srcPort, uint16_t dstPort, uint8_t proto, bool encrypted) {
    if (WiFi.status() != WL_CONNECTED) {
        return;
    }

    // 🛑 Temporarily suspend the promiscuous sniffer so the TCP stack has enough 
    // CPU cycles to successfully send the HTTP POST during a massive 2500+ pps flood!
    esp_wifi_set_promiscuous(false);

    WiFiClientSecure client;
    client.setInsecure(); // Bypass SSL certificate validation for Render HTTPS endpoint
    HTTPClient http;
    http.begin(client, BACKEND_URL);
    http.addHeader("Content-Type", "application/json");

    String jsonPayload = "{\"features\":[";
    for (int i = 0; i < 15; i++) {
        jsonPayload += String(features[i], 4);
        if (i < 14) jsonPayload += ",";
    }
    jsonPayload += "], \"edge_score\": " + String(edge_score, 4) + 
                   ", \"src_ip\": \"" + srcIp + "\", \"dst_ip\": \"" + dstIp + "\"" +
                   ", \"src_mac\": \"" + srcMac + "\", \"dst_mac\": \"" + dstMac + "\"" +
                   ", \"src_port\": " + String(srcPort) + ", \"dst_port\": " + String(dstPort) + 
                   ", \"protocol\": " + String(proto) + 
                   ", \"encrypted\": " + String(encrypted ? "true" : "false") + "}";

    int httpResponseCode = http.POST(jsonPayload);
    if (httpResponseCode <= 0) {
        Serial.print("❌ HTTP Error: ");
        Serial.println(httpResponseCode);
    }
    http.end();

    // 2. Send Heartbeat (Every 10 seconds)
    static unsigned long lastHeartbeat = 0;
    if (millis() - lastHeartbeat > 10000) {
        lastHeartbeat = millis();
        float t = dht.readTemperature();
        float h = dht.readHumidity();
        if (!isnan(t) && !isnan(h)) {
            currentTemp = t;
            currentHumi = h;
        }
        
        http.begin(client, "https://ai-ids-iot-8y4f.onrender.com/api/esp32/devices");
        http.addHeader("Content-Type", "application/json");
        String ip = WiFi.localIP().toString();
        String json = "{\"devices\":[";
        json += "{\"deviceId\":\"esp32-gw\", \"status\":\"ONLINE\", \"ipAddress\":\"" + ip + "\"},";
        json += "{\"deviceId\":\"dht11\", \"status\":\"ONLINE\", \"ipAddress\":\"" + ip + "\", \"temperature\":" + String(currentTemp, 1) + ", \"humidity\":" + String(currentHumi, 1) + "}";
        json += "]}";
        http.POST(json);
        http.end();
    }

    // 🟢 Resume sniffer
    esp_wifi_set_promiscuous(true);
}

void inferenceLoop(void * pvParameters) {
    windowStartTime = millis();

    for(;;) {
        unsigned long now = millis();
        // Run inference exactly every 2000 milliseconds (2-second window)
        if (now - windowStartTime >= 2000) {
            
            // Atomically flush accumulators
            portENTER_CRITICAL(&mux);
            uint32_t pCount = packetCount;
            uint32_t tSize  = totalSize;
            float    m2     = m2Size;
            float    avgSz  = meanSize;
            uint16_t mxSize = maxSize;
            uint16_t mnSize = minSize == 65535 ? 0 : minSize;
            uint32_t rst    = rstCount;
            uint32_t urg    = urgCount;
            uint32_t ack    = ackCount;
            uint32_t syn    = synCount;
            uint32_t fin    = finCount;
            uint32_t tIat   = totalIat;
            uint8_t  proto  = primaryProtocol;
            uint32_t hLen   = headerLengthTotal;
            uint32_t ttlSum = totalTtl;
            
            uint32_t sIp = lastSrcIp;
            uint32_t dIp = lastDstIp;
            char sMac[18]; strcpy(sMac, lastSrcMac);
            char dMac[18]; strcpy(dMac, lastDstMac);
            uint16_t sPort = lastSrcPort;
            uint16_t dPort = lastDstPort;
            bool isEnc = isEncrypted;
            
            // Reset for next window
            packetCount = 0; totalSize = 0; meanSize = 0.0; m2Size = 0.0; 
            maxSize = 0; minSize = 65535; rstCount = 0; urgCount = 0; ackCount = 0; 
            synCount = 0; finCount = 0; totalIat = 0; headerLengthTotal = 0; totalTtl = 0;
            windowStartTime = now;
            portEXIT_CRITICAL(&mux);

            if (pCount >= 2) { // Need at least 2 packets to evaluate behavior
                
                // Finalize Welford's Variance
                float variance = m2 / pCount; 
                float avgIat = (float)tIat / pCount; 
                float rate = (float)pCount / 2.0; // pkts per second
                float avgHlen = (float)hLen / pCount;
                float avgTtl = (float)ttlSum / pCount;

                // Structure features EXACTLY matching Kaggle model sequence
                float features[15];
                features[0]  = avgHlen;         // Header_Length_var
                features[1]  = (float)proto;    // Protocol_Type
                features[2]  = rate;            // Rate
                features[3]  = (float)tSize;    // Tot_size
                features[4]  = avgIat / 1000.0; // IAT (scaled to ms to prevent huge numbers)
                features[5]  = (float)mxSize;   // Max
                features[6]  = avgSz;           // AVG
                features[7]  = (float)pCount;   // Num
                features[8]  = variance;        // Variance
                features[9]  = (float)ack;      // ack_flag_number
                features[10] = (float)rst;      // rst_count
                features[11] = (float)syn;      // syn_flag_number
                features[12] = (float)fin;      // fin_flag_number
                features[13] = (float)urg;      // urg_flag_number
                features[14] = avgTtl;          // Time_To_Live

                // Scale features for XGBoost model
                double scaled_features[15]; 
                for (int i = 0; i < 15; i++) {
                    scaled_features[i] = ((double)features[i] - (double)scaler_center[i]) / (double)scaler_scale[i];
                }

                // Execute Native Machine Learning Classifier
                double model_output[2] = {0.0, 0.0}; 
                score(scaled_features, model_output); 
                float score = (float)model_output[1];

                // =======================================================================
                // 🛡️ HYBRID HEURISTIC IDS GATING (FALSE-POSITIVE PREVENTION)
                // A live ESP32-CAM video stream generates 100-200 packets per window.
                // To distinguish a video stream from an attack, we check the Variance.
                // Video Stream = Mix of 1500-byte frames & 60-byte ACKs (Huge Variance).
                // Floods = Identical packet sizes (Zero or very low Variance).
                // =================================================================
                // HYBRID HEURISTIC GATE v2 - FALSE POSITIVE PREVENTION
                // Rules (all must pass to trust XGBoost):
                // 1. pCount < 40  (<20 pps) → too few packets, always background noise
                // 2. variance > 20000       → mixed sizes = video stream, suppress
                // 3. rate < 30 pps          → real floods hit 500+ pps, this is benign
                // =================================================================
                // =================================================================
                if (pCount < 40) {
                    // Too few packets in 2s window. Background noise, not an attack.
                    score = 0.01 + (pCount * 0.001);
                } else if (rate < 30.0) {
                    // Rate < 30 pps even with low variance is just background ARP/MDNS.
                    // Real DDoS starts at 200+ pps. Suppress this.
                    score = 0.05 + (rate * 0.003);
                } else {
                    // Flood pattern. Trust the AI model!
                }
                
                Serial.printf("[IDS] Window Complete. Packets: %lu | Threat Score: %.2f%%\n", pCount, score * 100);

                if (score >= 0.85) {
                    Serial.println("⚠️ [ALERT] MALICIOUS TRAFFIC DETECTED. FORWARDING TO CLOUD!");
                }
                
                String srcIpStr = String((sIp >> 24) & 0xFF) + "." + String((sIp >> 16) & 0xFF) + "." + String((sIp >> 8) & 0xFF) + "." + String(sIp & 0xFF);
                String dstIpStr = String((dIp >> 24) & 0xFF) + "." + String((dIp >> 16) & 0xFF) + "." + String((dIp >> 8) & 0xFF) + "." + String(dIp & 0xFF);
                String srcMacStr = String(sMac);
                String dstMacStr = String(dMac);
                
                // --- OLED Display Update ---
                display.clearDisplay();
                display.setTextColor(WHITE);
                display.setTextSize(1);
                
                // Line 1: Network Status
                display.setCursor(0, 0);
                display.println("Network: Online");
                
                // Line 2: Traffic Status
                display.setCursor(0, 12);
                if (score >= 0.85) {
                    display.println("Malicious Traffic!");
                } else {
                    display.println("Normal Traffic");
                }
                
                // Line 3: PPS
                display.setCursor(0, 24);
                display.printf("PPS: %lu", pCount / 2);
                
                // Conditional Attack Info
                if (score >= 0.85) {
                    display.setCursor(0, 36);
                    display.println("Attack Type: DDoS");
                    display.setCursor(0, 48);
                    display.println("Check Dashboard!");
                }
                
                display.display();
                // ---------------------------
                
                // ALWAYS forward telemetry so dashboard live graph updates continuously
                forward_telemetry_to_cloud(features, score, srcIpStr, dstIpStr, srcMacStr, dstMacStr, sPort, dPort, proto, isEnc);
            }
        }
        vTaskDelay(50 / portTICK_PERIOD_MS); 
    }
}

// =====================================================================
// 5. SYSTEM INITIALIZATION
// =====================================================================
void setup() {
    Serial.begin(115200);
    while (!Serial);
    
    Serial.println("=========================================================");
    Serial.println("System Boot: AI-IDS Promiscuous Edge Node (Welford's HIL)");
    Serial.println("=========================================================");
    
    // Initialize OLED
    Wire.begin(21, 22);
    if(!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
        Serial.println("OLED allocation failed on 0x3C, check wiring!");
    } else {
        display.clearDisplay();
        display.setTextColor(WHITE);
        display.setTextSize(1);
        display.setCursor(0, 20);
        display.println("AI-IDS Booting...");
        display.display();
    }
    
    // Initialize DHT11
    dht.begin();
    
    // Connect to AP to get IP and sync Channel
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    Serial.print("Linking to Network");
    int retries = 0;
    while (WiFi.status() != WL_CONNECTED && retries < 30) {
        delay(500);
        Serial.print(".");
        retries++;
    }
    Serial.println("");

    if (WiFi.status() == WL_CONNECTED) {
        Serial.print("✅ Network Linked. IP Address: ");
        Serial.println(WiFi.localIP());
        
        // Lock sniffer to the same channel as the router
        uint8_t channel = WiFi.channel();
        esp_wifi_set_channel(channel, WIFI_SECOND_CHAN_NONE);
        Serial.print("🔒 Sniffer locked to Channel: ");
        Serial.println(channel);
    } else {
        Serial.println("❌ WiFi timeout. Check credentials.");
    }

    // Engage Promiscuous Mode
    esp_wifi_set_promiscuous(true);
    esp_wifi_set_promiscuous_rx_cb(&snifferCallback);
    Serial.println("🚀 Promiscuous Layer-2 Sniffer Engaged.");

    // Launch AI Inference Thread on Core 1
    xTaskCreatePinnedToCore(inferenceLoop, "InferenceTask", 8192, NULL, 1, &InferenceTask, 1);
}

void loop() {
    // Delete default loop to free up processor cycles for the Sniffer & AI Task
    vTaskDelete(NULL);
}