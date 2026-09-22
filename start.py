import os
import sys
import time
import socket
import json
import webbrowser
import threading
from pathlib import Path

# Safe Unicode output for Windows terminal
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from database import init_db, DB_PATH
from seed_data import seed_all

def get_local_ip() -> str:
    """Returns the local network IPv4 address of this machine for mobile device access."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.5)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"

def is_port_in_use(port: int) -> bool:
    """Checks if a local TCP port is already open."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.4)
        return s.connect_ex(('127.0.0.1', port)) == 0

def check_existing_agrosetu_server(port: int) -> bool:
    """Checks if the process on this port is ACTUALLY our AgroSetu platform."""
    import urllib.request
    try:
        url = f"http://127.0.0.1:{port}/api/health"
        with urllib.request.urlopen(url, timeout=1.5) as res:
            if res.status == 200:
                content = res.read().decode('utf-8', errors='ignore')
                if "Problem Statement 26033" in content or "Agro" in content:
                    return True
    except Exception:
        pass
    return False

def find_best_port() -> int:
    """
    Finds the cleanest available port for AgroSetu:
    1. If AgroSetu is already running, return that port immediately.
    2. Otherwise, check 8000, 8005, 8080, 8001.
    """
    candidate_ports = [8000, 8005, 8080, 8001, 8002]
    
    # Check if AgroSetu is ALREADY alive
    for p in candidate_ports:
        if is_port_in_use(p) and check_existing_agrosetu_server(p):
            return p

    # Pick first free port
    for p in candidate_ports:
        if not is_port_in_use(p):
            return p

    return 8000

def launch_browser(url: str):
    time.sleep(1.5)
    print(f"\n[+] Opening browser automatically: {url}")
    webbrowser.open(url)

def main():
    print("=" * 80)
    print("      AGROSETU AI - AGRO-LOGISTICS AND MARKETPLACE SYSTEM")
    print("               Problem Statement 26033 | Rohit Naik")
    print("              (Universal Platform for ALL Farmers in India)")
    print("=" * 80)

    # 1. Database Initialization
    try:
        if not DB_PATH.exists() or DB_PATH.stat().st_size == 0:
            print("[*] Initializing permanent SQLite database & nationwide seed data...")
            seed_all()
        else:
            print(f"[OK] Permanent Database Connected: {DB_PATH.name} ({round(DB_PATH.stat().st_size/1024, 1)} KB)")
    except Exception as e:
        print(f"[!] Warning during DB check: {e}")

    # 2. Identify Host & Port
    local_ip = get_local_ip()
    target_port = find_best_port()
    local_url = f"http://127.0.0.1:{target_port}"
    mobile_url = f"http://{local_ip}:{target_port}"

    # If AgroSetu is ALREADY running on this port, simply open the browser and exit cleanly!
    if is_port_in_use(target_port) and check_existing_agrosetu_server(target_port):
        print(f"\n[OK] AgroSetu platform is ALREADY active and healthy!")
        print(f"  * Local PC URL  : {local_url}")
        print(f"  * Mobile Phone  : {mobile_url} (Any phone on your Wi-Fi)")
        print(f"[+] Opening browser now...")
        webbrowser.open(local_url)
        print("\n" + "=" * 80)
        print(f"  DASHBOARD IS READY!")
        print(f"  PC Browser    : {local_url}")
        print(f"  Mobile Device : {mobile_url}")
        print("  (Server is already active. Enjoy using your dashboard!)")
        print("=" * 80)
        time.sleep(2)
        return

    print(f"\n[+] Selected Clean Port: {target_port}")
    print(f"[+] Local PC URL       : {local_url}")
    print(f"[+] Mobile Device URL  : {mobile_url} (Same Wi-Fi / Hotspot)")

    # 3. Schedule Browser Open
    threading.Thread(target=launch_browser, args=(local_url,), daemon=True).start()

    # 4. Start Uvicorn Server bound to 0.0.0.0 (Accessible to all farmers on local network)
    import uvicorn
    print(f"\n[*] Starting Server bound to 0.0.0.0:{target_port} ...")
    print("[*] Sabhi farmers apne phone se bhi jud sakte hain!")
    print("[*] Press Ctrl+C in this terminal to stop the server.\n")

    try:
        uvicorn.run("main:app", host="0.0.0.0", port=target_port, reload=False, app_dir=str(BACKEND_DIR))
    except OSError as e:
        if "10048" in str(e):
            alt_port = 8005 if target_port != 8005 else 8080
            print(f"\n[!] Port {target_port} was busy. Retrying on port {alt_port}...")
            webbrowser.open(f"http://127.0.0.1:{alt_port}")
            uvicorn.run("main:app", host="0.0.0.0", port=alt_port, reload=False, app_dir=str(BACKEND_DIR))
        else:
            raise e

if __name__ == "__main__":
    main()
