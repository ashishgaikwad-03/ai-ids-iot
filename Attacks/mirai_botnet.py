import socket
import time
import random

def mirai_udp_plain(target_ip, duration=30):
    """
    Mirai-udpplain signature from CIC-IoT 2023 dataset:
    - Protocol: UDP (not TCP!)
    - Packet size: exactly 74 bytes (Mirai's signature payload)
    - Rate: LOW (20-40 pps) - Mirai is stealthy, not a high-rate flood
    - Destination: random high ports (Mirai scans random ports)
    """
    print(f"[Mirai] Mirai-udpplain simulation against {target_ip}")
    print("[INFO] Sending 74-byte UDP packets at low rate (CIC-IoT 2023 signature)")
    print("[INFO] This matches the Mirai botnet C2 communication pattern")

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Mirai udpplain: EXACTLY 74 bytes of payload (this is the signature the model knows)
    # 74 bytes total = UDP header (8) + IP header (20) + 46 bytes data
    payload = b'\x00' * 46  # 46 bytes data = 74 total on wire

    end_time = time.time() + duration
    packets_sent = 0

    try:
        while time.time() < end_time:
            # Mirai scans random destination ports
            dst_port = random.randint(1024, 65535)
            sock.sendto(payload, (target_ip, dst_port))
            packets_sent += 1
            if packets_sent % 50 == 0:
                print(f"   -> Sent {packets_sent} Mirai probe packets")
            # Low rate = 25-35 pps (Mirai is stealthy)
            time.sleep(0.03 + random.uniform(0, 0.01))
    except KeyboardInterrupt:
        print("\n[STOPPED] Mirai simulation stopped.")

    sock.close()
    print(f"[DONE] Sent {packets_sent} Mirai-udpplain packets. Check dashboard for Mirai alert!")

if __name__ == "__main__":
    ip = input("Enter Target ESP32-CAM IP (Default: 192.168.24.167): ").strip() or "192.168.24.167"
    dur = input("Enter Duration in seconds (Default: 30): ").strip()
    dur = int(dur) if dur.isdigit() else 30
    mirai_udp_plain(ip, dur)
