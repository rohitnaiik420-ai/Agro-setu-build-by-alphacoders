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

def is_port_in_use(port: int) -> bool:
    """Checks if a local TCP port is already open."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(('127.0.0.1', port)) == 0

def check_existing_agrosetu_server(port: int) -> bool:
    """Checks if the existing process on the port is ACTUALLY AgroSetu (PS 26033)."""
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
    Finds the best port for AgroSetu:
    1. If an existing AgroSetu instance is already running on any port, return that port.
    2. Otherwise, check 8000. If 8000 is free, return 8000.
    3. If 8000 is taken by another application (like AutoDataScientist), return first free port (8005, 8080, 8001...).
    """
    candidate_ports = [8000, 8005, 8080, 8001, 8002]
    
    # First, check if AgroSetu is ALREADY running on any of these ports
    for p in candidate_ports:
        if is_port_in_use(p) and check_existing_agrosetu_server(p):
            return p

    # If not already running, pick the first completely free port
    for p in candidate_ports:
        if not is_port_in_use(p):
            return p

    return 8005

def launch_browser(url: str):
    time.sleep(1.8)
    print(f"\n[+] Opening web browser at: {url} ...")
    webbrowser.open(url)

def main():
    print("=" * 75)
    print("      AGROSETU AI - AGRO-LOGISTICS & MARKETPLACE SYSTEM")
    print("             Problem Statement 26033 | Rohit Naik")
    print("=" * 75)

    # 1. Database Initialization
    try:
        if not DB_PATH.exists() or DB_PATH.stat().st_size == 0:
            print("[*] Initializing permanent SQLite database & demo data...")
            seed_all()
        else:
            print(f"[OK] Database Connected: {DB_PATH.name} ({round(DB_PATH.stat().st_size/1024, 1)} KB)")
    except Exception as e:
        print(f"[!] Warning during DB check: {e}")

    # 2. Find Best Port without collisions
    target_port = find_best_port()
    dashboard_url = f"http://127.0.0.1:{target_port}"

    # If AgroSetu is already running on this port, simply open browser!
    if is_port_in_use(target_port) and check_existing_agrosetu_server(target_port):
        print(f"\n[OK] AgroSetu server is ALREADY active and healthy on {dashboard_url}!")
        print(f"[+] Opening browser now...")
        webbrowser.open(dashboard_url)
        print("\n" + "=" * 75)
        print(f"  DASHBOARD URL: {dashboard_url}")
        print(f"  Interactive Swagger Docs: {dashboard_url}/docs")
        print("  (Server is active in the background. Enjoy your dashboard!)")
        print("=" * 75)
        input("\nPress Enter to exit this launcher window...")
        return

    print(f"\n[+] Selected Clean Port: {target_port}")
    print(f"[+] Dashboard URL: {dashboard_url}")

    # 3. Schedule Browser Open
    threading.Thread(target=launch_browser, args=(dashboard_url,), daemon=True).start()

    # 4. Start Uvicorn Server with Safe Error Handling
    import uvicorn
    print(f"[*] Starting FastAPI Server on {dashboard_url} ...")
    print("[*] Press Ctrl+C anytime to stop the server.\n")

    try:
        uvicorn.run("main:app", host="127.0.0.1", port=target_port, reload=False, app_dir=str(BACKEND_DIR))
    except OSError as e:
        if "10048" in str(e):
            alt_port = 8005 if target_port != 8005 else 8080
            print(f"\n[!] Port {target_port} was locked. Retrying on alternate port {alt_port}...")
            alt_url = f"http://127.0.0.1:{alt_port}"
            webbrowser.open(alt_url)
            uvicorn.run("main:app", host="127.0.0.1", port=alt_port, reload=False, app_dir=str(BACKEND_DIR))
        else:
            raise e

if __name__ == "__main__":
    main()
