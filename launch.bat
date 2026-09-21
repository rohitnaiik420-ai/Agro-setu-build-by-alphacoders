@echo off
TITLE AgroSetu AI - Problem Statement 26033 (Rohit Naik)
color 0A
cls

echo =====================================================================
echo           AGROSETU AI - AGRO-LOGISTICS & MARKETPLACE SYSTEM
echo                    Problem Statement 26033
echo                      Solved by Rohit Naik
echo =====================================================================
echo.
echo [1/4] Checking Python Environment...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in your PATH.
    echo Please install Python 3.10+ and add it to PATH.
    pause
    exit /b 1
)
echo       Python detected successfully!
echo.

echo [2/4] Verifying Dependencies...
pip install -r "%~dp0requirements.txt" --quiet
echo       Core libraries (FastAPI, Uvicorn, Pydantic) verified.
echo.

echo [3/4] Checking SQLite Database & Example Data...
if not exist "%~dp0data\agri_system.db" (
    echo       Initializing database and populating demo examples...
    python "%~dp0backend\seed_data.py"
) else (
    echo       Permanent database found: data\agri_system.db
)
echo.

echo [4/4] Starting Server & Opening Dashboard...
echo       Local URL: http://127.0.0.1:8000
echo.
start "" "http://127.0.0.1:8000"

python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
pause
