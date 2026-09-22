@echo off
TITLE AgroSetu AI Dashboard Launcher - Problem Statement 26033
color 0A
cls

echo ===============================================================================
echo            AGROSETU AI - AGRO-LOGISTICS & MARKETPLACE SYSTEM
echo                       Problem Statement 26033
echo                         Solved by Rohit Naik
echo ===============================================================================
echo.

:: 1. Verify Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in your system PATH!
    echo Please install Python 3.10+ and add it to PATH.
    echo.
    pause
    exit /b 1
)

:: 2. Set directory to script folder
cd /d "%~dp0"

:: 3. Delegate to auto-healing start.py
python start.py

if errorlevel 1 (
    echo.
    echo [!] Server exited. Press any key to close.
    pause
)
