@echo off
TITLE AgroSetu AI Dashboard Launcher - Problem Statement 26033
color 0A
cls

echo ===============================================================================
echo            AGROSETU AI - AGRO-LOGISTICS AND MARKETPLACE SYSTEM
echo                       Problem Statement 26033
echo                         Solved by Rohit Naik
echo ===============================================================================
echo.

:: 1. Intelligent Python Detection
set "PY_EXE="

python --version >nul 2>&1
if not errorlevel 1 (
    set "PY_EXE=python"
    goto found_python
)

py -3 --version >nul 2>&1
if not errorlevel 1 (
    set "PY_EXE=py -3"
    goto found_python
)

if exist "C:\Users\ADMIN\anaconda3\python.exe" (
    set "PY_EXE=C:\Users\ADMIN\anaconda3\python.exe"
    goto found_python
)

if exist "C:\Users\ADMIN\AppData\Local\Programs\Python\Python313\python.exe" (
    set "PY_EXE=C:\Users\ADMIN\AppData\Local\Programs\Python\Python313\python.exe"
    goto found_python
)

echo [ERROR] Python not detected in PATH!
echo Please ensure Python 3.10+ is installed.
pause
exit /b 1

:found_python
echo [OK] Python Engine Detected: %PY_EXE%
echo.

:: 2. Set directory to script folder
cd /d "%~dp0"

:: 3. Delegate to auto-healing start.py
%PY_EXE% start.py

if errorlevel 1 (
    echo.
    echo [!] Process exited. Press any key to close.
    pause
)
