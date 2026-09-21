import os
import sys
import time
import webbrowser
import threading
from pathlib import Path

# Add backend directory to sys.path
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR / "backend"))

from database import init_db, DB_PATH
from seed_data import seed_all

def open_browser():
    time.sleep(1.5)
    print("\n[+] Opening web browser at: http://127.0.0.1:8000 ...")
    webbrowser.open("http://127.0.0.1:8000")

def main():
    print("=" * 70)
    print("      AGROSETU AI - AGRO-LOGISTICS & MARKETPLACE SYSTEM")
    print("              Problem Statement 26033")
    print("                Solved by Rohit Naik")
    print("=" * 70)

    # 1. Initialize & Seed DB if empty
    if not DB_PATH.exists():
        print("[*] Initializing permanent SQLite database and example scenarios...")
        seed_all()
    else:
        print(f"[*] Found existing database: {DB_PATH}")

    # 2. Launch browser in a background thread
    threading.Thread(target=open_browser, daemon=True).start()

    # 3. Start Uvicorn web server
    import uvicorn
    print("[*] Starting FastAPI web server on http://127.0.0.1:8000")
    print("[*] Press Ctrl+C in this terminal to safely stop the server.\n")
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=False)

if __name__ == "__main__":
    main()
