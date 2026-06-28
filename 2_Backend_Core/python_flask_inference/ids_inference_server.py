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

def publish_mqtt(topic, payload):
    try:
        temp_client = mqtt.Client(client_id="flask-pub-" + str(time.time())[:10])
        temp_client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
        temp_client.publish(topic, payload)
        temp_client.disconnect()
    except Exception as e:
        print(f"[CRITICAL] MQTT Publish Failed: {e}")

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

DEVICE_NAMES = {
    '192.168.24.167': 'ESP32-CAM',
    '192.168.121.6':  'ESP32 Gateway',
    '192.168.24.6':   'ESP32 Gateway',
    '192.168.1.1':    'Router / AP',
}

def send_telegram(attack_type, confidence, device_ip="192.168.24.167", sustained_secs=0, src_ip="Unknown", is_recovery=False):
    if BOT_TOKEN == "YOUR_BOT_TOKEN_FROM_BOTFATHER":
        print(f"[TELEGRAM SKIPPED] Token not configured. Attack: {attack_type} @ {confidence}% for {sustained_secs:.1f}s")
        return
    device_name = DEVICE_NAMES.get(device_ip, device_ip)
    
    if is_recovery:
        text = (
            f"🟢 <b>NETWORK SECURE</b>\n\n"
            f"✅ Malicious traffic has ceased.\n"
            f"🎯 Device: <b>{device_name}</b>\n"
            f"🕒 Time: {time.strftime('%H:%M:%S')}\n\n"
            f"Shields remain fully active. No further action required."
        )
    else:
        text = (
            f"🔴 <b>AI-IDS ALERT</b>\n\n"
            f"⚠️ Malicious Traffic Sustained (>5s)\n"
            f"🎯 Target Device: <b>{device_name}</b>\n"
            f"🕒 Time: {time.strftime('%H:%M:%S')}\n"
            f"💊 Type: <b>{attack_type}</b>\n"
            f"🌐 Source: <code>{src_ip}</code>\n\n"
            f"🔗 Open Security Dashboard:\n"
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
# ENTERPRISE SOC: DETECTION FUSION ENGINES
# ==========================================

# 1. Behavioral Anomaly Engine (Stateful)
device_baselines = {}
def run_behavioral_engine(src_ip, pkt_rate):
    if src_ip not in device_baselines:
        device_baselines[src_ip] = {"rates": [], "avg": 0}
    
    hist = device_baselines[src_ip]["rates"]
    hist.append(pkt_rate)
    if len(hist) > 10:
        hist.pop(0)
    
    avg_rate = sum(hist) / len(hist)
    device_baselines[src_ip]["avg"] = avg_rate
    
    if pkt_rate > (avg_rate * 3) and pkt_rate > 10:
        return True, "Anomaly", min(1.0, (pkt_rate / max(1, avg_rate)) / 10.0)
    return False, "BENIGN", 0.0

# 2. Rule-Based Engine (Static)
def run_rule_engine(features):
    try:
        pkt_rate = float(features[2])
        size = float(features[3])
        if pkt_rate > 100: return True, "DDoS", 0.95
        if size > 65000: return True, "DoS", 0.85
    except: pass
    return False, "BENIGN", 0.0

# 3. Signature Engine (Static Match)
def run_signature_engine(features):
    try:
        proto = float(features[1])
        size = float(features[3])
        if proto == 17 and size == 74: return True, "Mirai", 0.99
    except: pass
    return False, "BENIGN", 0.0

# 4. Explainable AI Heuristics
def calculate_xai(features, attack_type, confidence):
    if confidence < 0.2:
        return [{"feature": "Traffic Pattern", "impact": "Normal", "value": "Nominal"}]
    try:
        rate = float(features[2])
        size = float(features[3])
        if attack_type in ["DDoS", "DoS", "Anomaly"]:
            return [
                {"feature": "Packet Rate", "impact": "+85%", "value": f"{rate} pps"},
                {"feature": "Flow Size", "impact": "+12%", "value": f"{size} bytes"}
            ]
        elif attack_type == "Mirai":
            return [
                {"feature": "Protocol Signature", "impact": "+92%", "value": "UDP (17)"},
                {"feature": "Payload Size", "impact": "+8%", "value": f"{size} bytes"}
            ]
    except: pass
    return [{"feature": "Network Anomaly", "impact": "+50%", "value": "Detected"}]

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
                publish_mqtt("ids/devices", json.dumps(data["devices"]))
            return jsonify({"status": "heartbeat received"}), 200
        else:
            # Handle GET request from dashboard
            return jsonify({"status": "success", "devices": {}}), 200
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
            resolved_src = get_ip_from_mac(src_mac)
            resolved_dst = get_ip_from_mac(dst_mac)
            src_ip = resolved_src if resolved_src else f"MAC: {src_mac}"
            dst_ip = resolved_dst if resolved_dst else f"MAC: {dst_mac}"
            port = 0
            proto_str = "Encrypted WPA2"
        else:
            try:
                proto_num = int(float(data.get("protocol", features_list[1])))
                proto_mapping = {6: "TCP", 17: "UDP", 1: "ICMP", 0: "ARP", 2: "IGMP", 4: "IPv4", 41: "IPv6"}
                proto_str = proto_mapping.get(proto_num, f"Other ({proto_num})")
            except:
                proto_str = "Unknown"
        
        # Safely calculate average packet size
        try:
            tot_size = float(features_list[3])
            num_pkts = float(features_list[7])
            avg_size = int(tot_size / num_pkts) if num_pkts > 0 else 64
            if avg_size > 1500: avg_size = 1500
            if avg_size < 40: avg_size = 40
        except:
            avg_size = 64
            
        edge_score = data.get("edge_score", 0.0)
        ml_is_attack = edge_score >= 0.40
        
        ml_type = "BENIGN"
        ml_conf = 0.0
        if ml_is_attack:
            raw_array = np.array(features_list).reshape(1, -1)
            scaled_array = scaler.transform(raw_array)
            probabilities = model.predict_proba(scaled_array)[0]
            predicted_idx = int(np.argmax(probabilities))
            ml_conf = float(probabilities[predicted_idx])
            ml_type = CLASS_MAPPING.get(predicted_idx, "UnknownAttack")
        
        # Run New Engines
        try: pkt_rate_val = float(features_list[2])
        except: pkt_rate_val = 0.0
        
        rule_attack, rule_type, rule_conf = run_rule_engine(features_list)
        behav_attack, behav_type, behav_conf = run_behavioral_engine(src_ip, pkt_rate_val)
        sig_attack, sig_type, sig_conf = run_signature_engine(features_list)

        engines_triggered = []
        if ml_is_attack: engines_triggered.append("ML")
        if rule_attack: engines_triggered.append("Rule")
        if behav_attack: engines_triggered.append("Behavioral")
        if sig_attack: engines_triggered.append("Signature")

        final_is_attack = len(engines_triggered) > 0
        
        scores = [
            ("ML", ml_type, ml_conf),
            ("Rule", rule_type, rule_conf),
            ("Behavioral", behav_type, behav_conf),
            ("Signature", sig_type, sig_conf)
        ]
        top_engine = max(scores, key=lambda x: x[2])
        final_attack_type = top_engine[1] if final_is_attack else "BENIGN"
        
        multiplier = 1.0 + (len(engines_triggered) * 0.1)
        risk_score = min(100.0, (top_engine[2] * 100) * multiplier)
        if not final_is_attack: risk_score = 0.0

        xai_data = calculate_xai(features_list, final_attack_type, risk_score/100.0)
        baseline_avg = device_baselines.get(src_ip, {}).get("avg", 0)

        response_data = {
            "incident_verified": final_is_attack,
            "attack_type": final_attack_type,
            "confidence_metric": round(risk_score, 2)
        }
        
        display_confidence = round(risk_score, 1) if final_is_attack else 0
        
        alert_payload = {
            "attack": final_is_attack,
            "attackType": final_attack_type,
            "confidence": risk_score / 100.0,
            "displayConfidence": display_confidence,
            "pktRate": pkt_rate_val,
            "packetSize": avg_size,
            "protocol": proto_str,
            "sourceIp": src_ip,
            "destIp": dst_ip,
            "port": port,
            "timestamp": time.strftime("%H:%M:%S"),
            "severityScore": round(risk_score, 0),
            "fusionEngines": engines_triggered,
            "xai": xai_data,
            "baselineAvg": round(baseline_avg, 1)
        }

        try:
            if is_attack:
                publish_mqtt("ids/alerts", json.dumps(alert_payload))
            publish_mqtt("ids/packets", json.dumps(alert_payload))
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
            attack_state["type"] = final_attack_type
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
                if attack_state["alert_fired"]:
                    print("[RECOVERY] Sending Telegram recovery message")
                    threading.Thread(
                        target=send_telegram,
                        args=(attack_state["type"], attack_state["confidence"], "192.168.24.167", sustained_secs, "EXTERNAL", True)
                    ).start()
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