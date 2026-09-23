import os
import sys
import time
import socket
import json
import webbrowser
import threading
import subprocess
from pathlib import Path

# Safe terminal encoding
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
    """Returns the local network IPv4 address for mobile device access."""
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
    """Checks if a TCP port is currently listening."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.4)
        return s.connect_ex(('127.0.0.1', port)) == 0

def check_existing_agrosetu_server(port: int) -> bool:
    """Checks if the running service on this port is AgroSetu."""
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

def free_port_if_stale_python(port: int) -> bool:
    """
    If port is held by an unresponsive Python or stale instance, kill it
    to ensure port 8000 is always cleanly available for AgroSetu.
    """
    try:
        cmd = f'netstat -ano | findstr :{port}'
        output = subprocess.check_output(cmd, shell=True, text=True, errors='ignore')
        current_pid = os.getpid()
        killed = False
        for line in output.strip().splitlines():
            if "LISTENING" in line.upper():
                parts = line.split()
                if len(parts) >= 5:
                    pid = int(parts[-1])
                    if pid > 0 and pid != current_pid:
                        print(f"[*] Releasing busy port {port} (PID: {pid})...")
                        subprocess.run(f"taskkill /F /PID {pid}", shell=True, capture_output=True)
                        time.sleep(0.8)
                        killed = True
        return killed
    except Exception:
        return False

def find_best_port() -> int:
    """
    Prefers port 8000. If 8000 is free or is already healthy AgroSetu, use 8000.
    If occupied by an unknown stale process, attempts to clear it.
    Falls back to 8005 or 8080 if 8000 cannot be used.
    """
    # 1. If 8000 already has our healthy AgroSetu server
    if is_port_in_use(8000) and check_existing_agrosetu_server(8000):
        return 8000

    # 2. If 8000 is occupied by something else, try to free it
    if is_port_in_use(8000):
        free_port_if_stale_python(8000)
        time.sleep(0.5)

    if not is_port_in_use(8000):
        return 8000

    # 3. Check fallback ports
    for p in [8005, 8080, 8001]:
        if not is_port_in_use(p) or check_existing_agrosetu_server(p):
            return p

    return 8000

def launch_browser(url: str):
    time.sleep(1.2)
    print(f"\n[+] Opening browser automatically: {url}")
    webbrowser.open(url)

def handle_already_running_dashboard(local_url: str, mobile_url: str, port: int):
    """
    Interactive control menu when server is already running in background.
    Prevents the terminal window from flashing and closing!
    """
    print("\n" + "=" * 80)
    print("      [OK] AGROSETU AI IS ALREADY RUNNING & HEALTHY!")
    print("=" * 80)
    print(f"  * Local PC URL      : {local_url}")
    print(f"  * Mobile Phone URL  : {mobile_url}  (Any phone on your Wi-Fi)")
    print(f"  * API Documentation : {local_url}/docs")
    print("=" * 80)
    print("\n[+] Opening dashboard in your browser...")
    webbrowser.open(local_url)

    print("\nControls (Control Menu):")
    print("  [Enter] -> Re-open dashboard in browser")
    print("  [r]     -> Restart AgroSetu server")
    print("  [t]     -> Run system diagnostic tests")
    print("  [q]     -> Close this launcher window\n")

    while True:
        try:
            choice = input("Select an option [Enter/r/t/q]: ").strip().lower()
            if choice == 'r':
                print("[*] Stopping existing server...")
                free_port_if_stale_python(port)
                time.sleep(1)
                print("[*] Restarting AgroSetu now...\n")
                main()
                break
            elif choice == 't':
                diag_script = ROOT_DIR / "backend" / "test_system.py"
                if diag_script.exists():
                    subprocess.run([sys.executable, str(diag_script)])
                else:
                    print("Diagnostics script not found.")
            elif choice == 'q':
                print("Launcher closed. (AgroSetu server remains active in background).")
                break
            else:
                webbrowser.open(local_url)
        except (KeyboardInterrupt, EOFError):
            print("\nExiting launcher.")
            break

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

    # 3. If AgroSetu is ALREADY running on this port, show interactive menu
    if is_port_in_use(target_port) and check_existing_agrosetu_server(target_port):
        handle_already_running_dashboard(local_url, mobile_url, target_port)
        return

    # 4. Starting fresh server
    print(f"\n[+] Selected Port     : {target_port}")
    print(f"[+] Local PC URL      : {local_url}")
    print(f"[+] Mobile Device URL : {mobile_url} (Same Wi-Fi / Hotspot)")
    print(f"[+] API Documentation : {local_url}/docs")

    # Schedule browser opening
    threading.Thread(target=launch_browser, args=(local_url,), daemon=True).start()

    import uvicorn
    print(f"\n[*] Starting Uvicorn Server bound to 0.0.0.0:{target_port} ...")
    print("[*] Sabhi farmers apne mobile phone se bhi jud sakte hain!")
    print("[*] Press Ctrl+C in this window at any time to stop the server.\n")

    try:
        uvicorn.run("main:app", host="0.0.0.0", port=target_port, reload=False, app_dir=str(BACKEND_DIR))
    except KeyboardInterrupt:
        print("\n[*] AgroSetu server stopped by user.")
    except OSError as e:
        if "10048" in str(e):
            alt_port = 8005 if target_port != 8005 else 8080
            print(f"\n[!] Port {target_port} was busy. Retrying automatically on port {alt_port}...")
            webbrowser.open(f"http://127.0.0.1:{alt_port}")
            uvicorn.run("main:app", host="0.0.0.0", port=alt_port, reload=False, app_dir=str(BACKEND_DIR))
        else:
            print(f"\n[!] Server error: {e}")
    except Exception as e:
        print(f"\n[!] Unexpected error: {e}")
    finally:
        print("\n" + "=" * 80)
        print("  AgroSetu session ended.")
        print("=" * 80)
        try:
            input("\nPress Enter to close this window...")
        except (EOFError, KeyboardInterrupt):
            pass

if __name__ == "__main__":
    main()
