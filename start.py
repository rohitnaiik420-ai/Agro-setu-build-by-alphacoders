import os
import sys
import time
import socket
import subprocess
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

def check_existing_agrosetu_server(port: int = 8000) -> bool:
    """Checks if the existing process on the port is actually AgroSetu responding to /api/health."""
    import urllib.request
    try:
        url = f"http://127.0.0.1:{port}/api/health"
        with urllib.request.urlopen(url, timeout=1.5) as res:
            if res.status == 200:
                return True
    except Exception:
        pass
    return False

def free_port_windows(port: int = 8000):
    """Attempts to kill any stale process holding the port on Windows."""
    try:
        cmd = f'netstat -ano | findstr :{port}'
        output = subprocess.check_output(cmd, shell=True, text=True)
        for line in output.strip().splitlines():
            parts = line.split()
            if len(parts) >= 5 and 'LISTENING' in line.upper():
                pid = parts[-1]
                if pid and pid != str(os.getpid()):
                    print(f"[*] Releasing stale port {port} (Terminating PID: {pid})...")
                    subprocess.run(f'taskkill /F /PID {pid}', shell=True, capture_output=True)
                    time.sleep(1)
    except Exception:
        pass

def find_available_port(start_port: int = 8000) -> int:
    """Finds the first available port among 8000, 8001, 8002, 8080."""
    candidate_ports = [start_port, 8001, 8002, 8080, 8888]
    for p in candidate_ports:
        if not is_port_in_use(p):
            return p
    return start_port

def launch_browser(url: str):
    time.sleep(1.8)
    print(f"\n[+] Automatically opening browser: {url}")
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

    # 2. Port Check & Conflict Resolution
    target_port = 8000
    if is_port_in_use(target_port):
        if check_existing_agrosetu_server(target_port):
            dashboard_url = f"http://127.0.0.1:{target_port}"
            print(f"\n[OK] AgroSetu server is ALREADY active and healthy on {dashboard_url}!")
            print(f"[+] Opening browser now...")
            webbrowser.open(dashboard_url)
            print("\n" + "=" * 75)
            print(f"  DASHBOARD URL: {dashboard_url}")
            print("  Interactive Swagger Docs: http://127.0.0.1:8000/docs")
            print("  (Server is already running in the background. Enjoy your dashboard!)")
            print("=" * 75)
            input("\nPress Enter to exit this launcher window...")
            return

        # Not responding to health check, try to free the port
        print(f"[*] Port {target_port} is busy with a stale process. Attempting to free port...")
        free_port_windows(target_port)
        time.sleep(1)

        if is_port_in_use(target_port):
            target_port = find_available_port(8001)
            print(f"[!] Port 8000 remained locked. Switching seamlessly to port {target_port}...")

    dashboard_url = f"http://127.0.0.1:{target_port}"
    print(f"\n[+] Target Server URL: {dashboard_url}")

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
            print(f"\n[!] Port {target_port} had a bind collision. Retrying on alternate port...")
            alt_port = find_available_port(target_port + 1)
            webbrowser.open(f"http://127.0.0.1:{alt_port}")
            uvicorn.run("main:app", host="127.0.0.1", port=alt_port, reload=False, app_dir=str(BACKEND_DIR))
        else:
            raise e

if __name__ == "__main__":
    main()
