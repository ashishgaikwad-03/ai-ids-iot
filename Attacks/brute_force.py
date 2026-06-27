import socket
import time

def brute_force_simulation(target_ip, duration=15):
    print(f"🔐 [Brute Force] Simulating Dictionary Brute Force against {target_ip}")
    print("⚠️  Making sequential, rapid login attempts on FTP (21) and SSH (22)...")
    
    end_time = time.time() + duration
    
    # Brute force attacks have a very steady, rhythmic packet rate
    try:
        while True:
            for port in [21, 22]:
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(0.2)
                    s.connect((target_ip, port))
                    s.send(b"USER admin\r\nPASS password\r\n")
                    s.close()
                except:
                    pass
            # Steady rhythm (approx 10 attempts per second)
            time.sleep(0.1) 
            print("Trying password...", end="\r")
    except KeyboardInterrupt:
        pass
        
    print("\n✅ Brute Force Simulation Complete.")

if __name__ == "__main__":
    ip = input("Enter Target IP (Default: 192.168.24.167): ")
    if not ip.strip(): ip = "192.168.24.167"
    dur = input("Enter Duration (Default: 15): ")
    dur = int(dur) if dur.strip().isdigit() else 15
    brute_force_simulation(ip, dur)
