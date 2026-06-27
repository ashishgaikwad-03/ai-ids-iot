import socket
import time
import random

def spoofing_simulation(duration=15):
    print(f"🎭 [Spoofing] Simulating MAC/IP/DNS Spoofing anomalies on the local subnet")
    print("⚠️  Broadcasting malformed UDP packets to simulate spoofed DHCP/DNS traffic...")
    
    end_time = time.time() + duration
    
    # Broadcast address to simulate Layer 2 / Layer 3 spoofing floods
    target_ip = "255.255.255.255" 
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    
    try:
        while True:
            # Simulate DNS (53), DHCP (67/68), and NetBIOS (137) spoofing
            for port in [53, 67, 68, 137]:
                # Send tiny, rapid malformed packets typical of spoofing injections
                payload = random.randbytes(42) 
                for _ in range(20):
                    sock.sendto(payload, (target_ip, port))
            time.sleep(0.01)
            print("Broadcasting spoofed packets...", end="\r")
    except KeyboardInterrupt:
        pass
        
    sock.close()
    print("\n✅ Spoofing Simulation Complete.")

if __name__ == "__main__":
    dur = input("Enter Duration (Default: 15): ")
    dur = int(dur) if dur.strip().isdigit() else 15
    spoofing_simulation(dur)
