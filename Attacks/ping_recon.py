import socket
import threading
import time
import subprocess
import os

def ping_scan(target_ip, duration=10):
    print(f"🔍 [Reconnaissance] Initiating Active ICMP & Port Scan against ({target_ip})")
    print("⚠️  This will flood the target with ICMP Pings and SYN requests to simulate Nmap.")
    
    end_time = time.time() + duration
    
    def icmp_flood():
        # Use system ping to flood ICMP packets
        while True:
            # -n 1 for Windows, -c 1 for Linux
            param = '-n' if os.name == 'nt' else '-c'
            subprocess.run(["ping", param, "1", target_ip], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
    def port_scan():
        # Scan random ports aggressively
        while True:
            port = 80 # Usually focus on port 80 to hit the web server
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.1)
                s.connect((target_ip, port))
                s.close()
            except:
                pass
            time.sleep(0.05)

    # Launch ICMP flood
    t_icmp = threading.Thread(target=icmp_flood)
    t_icmp.daemon = True
    t_icmp.start()
    
    # Launch aggressive port scanning
    for _ in range(5):
        t_port = threading.Thread(target=port_scan)
        t_port.daemon = True
        t_port.start()
        
    try:
        while True:
            time.sleep(1)
            print(f"Scanning target {target_ip}...")
    except KeyboardInterrupt:
        pass
        
    print("✅ Reconnaissance Complete.")
    print("👀 Check your AI Dashboard - it should flag Active Scanning / Recon!")

if __name__ == "__main__":
    ip = input("Enter Target IP (Default: 192.168.24.167): ")
    if not ip.strip():
        ip = "192.168.24.167"
        
    dur = input("Enter Duration in seconds (Default: 10): ")
    dur = int(dur) if dur.strip().isdigit() else 10
    
    ping_scan(ip, dur)
