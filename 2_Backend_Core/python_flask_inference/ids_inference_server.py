import os
import time
import pickle
import numpy as np
import json
import threading
import requests
import paho.mqtt.client as mqtt
import subprocess
import re

# =====================================================================
# ARP RESOLUTION (For WPA2 Encrypted Layer 2 Traffic)
# =====================================================================
def get_ip_from_mac(mac):
    if not mac or mac == "00:00:00:00:00:00":
        return None
    try:
        # Windows arp -a format uses hyphens
        mac_win = mac.replace(':', '-').lower()
        output = subprocess.check_output(['arp', '-a']).decode('utf-8', errors='ignore')
        for line in output.split('\n'):
            if mac_win in line.lower():
                parts = line.split()
                if len(parts) >= 2:
                    return parts[0] # Return the IP address
    except Exception as e:
        print(f"ARP lookup failed: {e}")
    return None

from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app) # Allows Vercel frontend to call this API if needed

# ==========================================
# CLOUD INTEGRATION SETTINGS
# ==========================================
# 1. HiveMQ MQTT (for real-time dashboard updates)
MQTT_BROKER = "broker.emqx.io"
MQTT_PORT   = 1883 # Public unencrypted port
MQTT_USER   = ""
MQTT_PASS   = ""

# 2. Telegram Bot (for instant push notifications)
BOT_TOKEN   = "8697442024:AAFnMcIqebrFuDg-k8NCEN6FxNITV_VbZls"
CHAT_ID     = "5120288258"

mqtt_client = mqtt.Client(client_id="flask-ids-backend-" + str(time.time()))

# ==========================================
# SUSTAINED ATTACK TRACKER
# Fires Telegram when attack lasts 5+ seconds
# ==========================================
attack_state = {
    "active": False,
    "start_time": None,
    "last_seen": None,
    "type": None,
    "confidence": 0,
    "alert_fired": False,   # prevents spam: only 1 alert per sustained event
    "gap_threshold": 8.0,   # seconds gap before attack is considered "over"
    "sustain_threshold": 5.0  # seconds before CRITICAL Telegram fires
}

def connect_mqtt():
    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
        mqtt_client.loop_start()
        print("[SUCCESS] Connected to Public HiveMQ Broker.")
    except Exception as e:
        print(f"[WARNING] MQTT Connection failed: {e}")

connect_mqtt()

DEVICE_NAMES = {
    '192.168.24.167': 'ESP32-CAM',
    '192.168.121.6':  'ESP32 Gateway',
    '192.168.24.6':   'ESP32 Gateway',
    '192.168.1.1':    'Router / AP',
}

def send_telegram(attack_type, confidence, device_ip="192.168.24.167", sustained_secs=0, src_ip="Unknown"):
    if BOT_TOKEN == "YOUR_BOT_TOKEN_FROM_BOTFATHER":
        print(f"[TELEGRAM SKIPPED] Token not configured. Attack: {attack_type} @ {confidence}% for {sustained_secs:.1f}s")
        return
    device_name = DEVICE_NAMES.get(device_ip, device_ip)
    text = (
        f"\U0001f534 <b>AI-IDS ALERT</b>\n\n"
        f"\u26a0\ufe0f Malicious Traffic Detected\n"
        f"\U0001f3af Target Device: <b>{device_name}</b>\n"
        f"\U0001f550 Time: {time.strftime('%H:%M:%S')}\n"
        f"\U0001f48a Type: <b>{attack_type}</b>\n"
        f"\U0001f310 Source: <code>{src_ip}</code>\n\n"
        f"\U0001f517 Open Security Dashboard:\n"
        f"https://ai-iot-ids.vercel.app/"
    )
    try:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"},
            timeout=5
        )
        print(f"[TELEGRAM SENT] {attack_type} @ {device_name} sustained {sustained_secs:.1f}s")
    except Exception as e:
        print(f"Telegram failed: {e}")

# ==========================================
# INFERENCE ENGINE
# ==========================================
scaler = None
model = None

CLASS_MAPPING = {
    0: "DDoS",
    1: "DoS",
    2: "Mirai",
    3: "Spoofing",
    4: "Recon"
}

# The model was trained on 16 features where rst_count (index 10) was duplicated at index 11.
# ESP32 sends 15 correct features. We patch the array here before inference.
def pad_features_to_16(f15):
    """Insert duplicate rst_count at index 11 to match training data shape."""
    f16 = list(f15)
    f16.insert(11, f16[10])  # duplicate rst_count
    return f16

def load_binaries():
    global scaler, model
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        scaler_path = os.path.join(base_dir, "scaler_multi.pkl")
        model_path = os.path.join(base_dir, "model_multi.pkl")

        with open(scaler_path, "rb") as f:
            scaler = pickle.load(f)
        with open(model_path, "rb") as f:
            model = pickle.load(f)
        print("[SUCCESS] Stage 2 Multi-class engine models uploaded to Flask memory.")
    except Exception as e:
        print(f"[CRITICAL] Binary loader sequence failed: {e}")

load_binaries()

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "engine": "Flask Multi-Class Node"}), 200

@app.route("/api/esp32/devices", methods=["GET", "POST"])
def device_heartbeat():
    try:
        if request.method == "POST":
            data = request.get_json()
            if data and "devices" in data:
                mqtt_client.publish("ids/devices", json.dumps(data["devices"]))
            return jsonify({"status": "heartbeat received"}), 200
        else:
            # Handle GET request from dashboard
            mock_devices = {
                'esp32-gw':  { 'name': 'ESP32 Gateway', 'ip': '192.168.121.6', 'status': 'ONLINE' },
                'esp32-cam': { 'name': 'ESP32-CAM',     'ip': '192.168.24.167', 'status': 'ONLINE' },
                'dht11':     { 'name': 'DHT11 Sensor',  'ip': '192.168.121.6', 'status': 'ONLINE' }
            }
            return jsonify({"status": "success", "devices": mock_devices}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/v2/analyze", methods=["POST"])
def analyze():
    if scaler is None or model is None:
        return jsonify({"error": "Classification models are offline."}), 503
        
    data = request.get_json()
    if not data or "features" not in data:
        return jsonify({"error": "Missing 'features' index payload array."}), 400
        
    features_list = data["features"]
    if len(features_list) == 15:
        # ESP32 sends 15 features — pad to 16 to match model training shape
        features_list = pad_features_to_16(features_list)
    elif len(features_list) != 16:
        return jsonify({"error": f"Array dimensional mismatch. Expected 15 or 16, got {len(features_list)}"}), 400

    try:
        edge_score = data.get("edge_score", 0.0)
        is_attack = edge_score >= 0.40
        
        predicted_idx = -1
        confidence = 0.0
        attack_type = "BENIGN"
        telemetry_matrix = {}

        if is_attack:
            raw_array = np.array(features_list).reshape(1, -1)
            scaled_array = scaler.transform(raw_array)
            probabilities = model.predict_proba(scaled_array)[0]
            predicted_idx = int(np.argmax(probabilities))
            confidence = float(probabilities[predicted_idx])
            attack_type = CLASS_MAPPING.get(predicted_idx, "UnknownAttack")
            telemetry_matrix = {CLASS_MAPPING[i]: round(float(prob) * 100, 2) for i, prob in enumerate(probabilities)}
        else:
            confidence = 1.0 - edge_score

        response_data = {
            "incident_verified": is_attack,
            "attack_type": attack_type,
            "confidence_metric": round(confidence * 100, 2)
        }
        
        # -------------------------------------------------------------
        # WPA2 DECRYPTION LOGIC (Layer-2 Promiscuous Handling)
        # -------------------------------------------------------------
        encrypted = data.get("encrypted", True)
        src_mac = data.get("src_mac", "")
        dst_mac = data.get("dst_mac", "")
        
        src_ip = data.get("src_ip", "External Network")
        dst_ip = data.get("dst_ip", "192.168.121.x (IoT Subnet)")
        port = int(data.get("dst_port", 0))
        
        if encrypted:
            # Traffic is WPA2 encrypted. We cannot read IP/Port from ciphertext.
            # Use the unencrypted Layer-2 MAC addresses and resolve via ARP table!
            resolved_src = get_ip_from_mac(src_mac)
            resolved_dst = get_ip_from_mac(dst_mac)
            
            src_ip = resolved_src if resolved_src else f"MAC: {src_mac}"
            dst_ip = resolved_dst if resolved_dst else f"MAC: {dst_mac}"
            
            port = 0
            proto_str = "Encrypted WPA2"
        else:
            # Determine protocol string for unencrypted traffic
            try:
                proto_num = int(float(data.get("protocol", features_list[1])))
                proto_mapping = {6: "TCP", 17: "UDP", 1: "ICMP", 0: "ARP", 2: "IGMP", 4: "IPv4", 41: "IPv6"}
                proto_str = proto_mapping.get(proto_num, f"Other ({proto_num})")
            except:
                proto_str = "Unknown"
        
        # Safely calculate average packet size to ensure it's never massive
        try:
            tot_size = float(features_list[3])
            num_pkts = float(features_list[7])
            avg_size = int(tot_size / num_pkts) if num_pkts > 0 else 64
            if avg_size > 1500: avg_size = 1500 # Cap at standard MTU
            if avg_size < 40: avg_size = 40     # Min size
        except:
            avg_size = 64
        # Use edge_score as confidence display — this is what ESP32 computed (e.g. 99.11%)
        # XGBoost model confidence is used only for attack TYPE classification
        display_confidence = round(edge_score * 100, 1)
        severity_score = display_confidence if is_attack else 0
        alert_payload = {
            "attack": is_attack,
            "attackType": attack_type,
            "confidence": edge_score,       # raw 0-1 for internal use
            "displayConfidence": display_confidence,  # 99.11% from ESP32 edge score
            "pktRate": float(features_list[2]),
            "packetSize": avg_size,
            "protocol": proto_str,
            "sourceIp": src_ip,
            "destIp": dst_ip,
            "port": port,
            "timestamp": time.strftime("%H:%M:%S"),
            "severityScore": severity_score
        }

        try:
            if is_attack:
                mqtt_client.publish("ids/alerts", json.dumps(alert_payload))
            mqtt_client.publish("ids/packets", json.dumps(alert_payload))
        except Exception as e:
            print(f"Failed to publish to MQTT: {e}")

        # -- Sustained Attack Tracker (Telegram fires after 5s) --
        if is_attack:
            now = time.time()
            if not attack_state["active"]:
                attack_state["active"] = True
                attack_state["start_time"] = now
                attack_state["alert_fired"] = False
                attack_state["type"] = attack_type
                attack_state["confidence"] = display_confidence
                print(f"[ATTACK START] {attack_type} @ {display_confidence}%")
            attack_state["last_seen"] = now
            attack_state["type"] = attack_type
            attack_state["confidence"] = display_confidence

        return jsonify(response_data), 200

    except Exception as e:
        return jsonify({"error": f"Pipeline processing error: {str(e)}"}), 500

def monitor_attack_state():
    while True:
        time.sleep(1)
        if attack_state["active"] and attack_state["start_time"] is not None and attack_state["last_seen"] is not None:
            now = time.time()
            sustained_secs = now - attack_state["start_time"]
            
            if sustained_secs >= attack_state["sustain_threshold"] and not attack_state["alert_fired"]:
                attack_state["alert_fired"] = True
                print(f"[CRITICAL] Attack sustained {sustained_secs:.1f}s -> Firing Telegram!")
                threading.Thread(
                    target=send_telegram,
                    args=(attack_state["type"], attack_state["confidence"], "192.168.24.167", sustained_secs, "EXTERNAL")
                ).start()
                
            gap = now - attack_state["last_seen"]
            if gap > attack_state["gap_threshold"]:
                print(f"[ATTACK END] {attack_state['type']} ended after gap {gap:.1f}s")
                attack_state["active"] = False
                attack_state["start_time"] = None
                attack_state["alert_fired"] = False

# start thread before app.run
threading.Thread(target=monitor_attack_state, daemon=True).start()

# ==========================================
# SIMULATION LAB API
# ==========================================
SIM_RUNNING = False
SIM_PROCESS = None

@app.route("/api/simulation/start", methods=["POST"])
def sim_start():
    global SIM_RUNNING
    SIM_RUNNING = True
    return jsonify({"running": True})

@app.route("/api/simulation/stop", methods=["POST"])
def sim_stop():
    global SIM_RUNNING, SIM_PROCESS
    SIM_RUNNING = False
    if SIM_PROCESS:
        try:
            SIM_PROCESS.kill()
        except:
            pass
        SIM_PROCESS = None
    return jsonify({"running": False})

@app.route("/api/inject", methods=["POST"])
def sim_inject():
    global SIM_PROCESS
    attack_type = request.args.get("type", "")
    script_map = {
        "DDoS_UDP": "ddos_udp_flood.py",
        "DoS_TCP": "dos_tcp_flood.py",
        "Mirai": "mirai_botnet.py",
        "Spoofing": "spoofing_sim.py",
        "Recon_Ping": "ping_recon.py",
        "BruteForce": "brute_force.py",
        "Web_Attack": "web_attack.py"
    }
    
    script_file = script_map.get(attack_type)
    if script_file:
        script_path = os.path.join("C:\\PROJECT\\AI-IDS-IoT-Network\\Attacks", script_file)
        if os.path.exists(script_path):
            try:
                # Fire and forget with default inputs (newlines) and UTF-8 to prevent emoji crash
                env = os.environ.copy()
                env["PYTHONIOENCODING"] = "utf-8"
                SIM_PROCESS = subprocess.Popen(
                    ["python", script_path],
                    stdin=subprocess.PIPE,
                    env=env
                )
                SIM_PROCESS.stdin.write(b'\n\n')
                SIM_PROCESS.stdin.flush()
                return jsonify({"status": "injected", "script": script_file})
            except Exception as e:
                return jsonify({"error": str(e)}), 500
    
    return jsonify({"status": "ignored", "reason": "script not found"}), 404

# ==========================================
# FILE ANALYSIS API
# ==========================================
import pandas as pd

@app.route("/api/analyze", methods=["POST"])
def analyze_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Empty filename"}), 400
        
    try:
        df = pd.read_csv(file)
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if not numeric_cols:
            return jsonify({"error": "No numeric columns found in CSV"}), 400
            
        features = df[numeric_cols[:15]].values.tolist()
        
        results = []
        attacks = 0
        top_threat = {}
        
        for row in features[:200]: # limit to 200 rows for real-time response
            if len(row) < 15:
                row = row + [0] * (15 - len(row))
            f15 = np.array(row[:15], dtype=float)
            f16 = pad_features_to_16(f15)
            f16_scaled = scaler.transform(f16.reshape(1, -1))
            probs = model.predict_proba(f16_scaled)[0]
            
            predicted_idx = int(np.argmax(probs))
            confidence = float(np.max(probs))
            
            attack_type = "BENIGN"
            is_attack = False
            
            if predicted_idx in CLASS_MAPPING:
                attack_type = CLASS_MAPPING[predicted_idx]
                is_attack = (attack_type != "BENIGN" and predicted_idx != 5) # Assuming 5 might be benign, wait CLASS_MAPPING has no Benign. 0-4 are attacks.
                if is_attack:
                    attacks += 1
                    top_threat[attack_type] = top_threat.get(attack_type, 0) + 1
            else:
                attack_type = "BENIGN"
                
            results.append({
                "attackType": attack_type,
                "attack": is_attack,
                "confidence": confidence,
                "timestamp": "Batch Analysis",
                "sourceIp": "PCAP/CSV",
                "destIp": "IoT Device",
                "protocol": "ANY",
                "packetSize": int(row[0]) if len(row) > 0 else 0
            })
            
        dominant_threat = max(top_threat, key=top_threat.get) if top_threat else "None"
        
        return jsonify({
            "results": results,
            "summary": {
                "total": len(results),
                "attacks": attacks,
                "attackRate": f"{round((attacks/max(1, len(results)))*100, 1)}%",
                "topThreat": dominant_threat
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)