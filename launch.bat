@echo off
TITLE AgroSetu AI Dashboard Launcher - Problem Statement 26033
color 0A
cls

echo ===============================================================================
echo            AGROSETU AI - AGRO-LOGISTICS AND MARKETPLACE SYSTEM
echo                       Problem Statement 26033
echo                         Solved by Rohit Naik
echo              (Universal Platform for ALL Farmers Across India)
echo ===============================================================================
echo.

:: 1. Intelligent Multi-Path Python Detection
set "PY_CMD="

if exist "C:\Users\ADMIN\anaconda3\python.exe" (
    "C:\Users\ADMIN\anaconda3\python.exe" -c "import sys" >nul 2>&1
    if not errorlevel 1 (
        set "PY_CMD=C:\Users\ADMIN\anaconda3\python.exe"
        goto found_python
    )
)

python -c "import sys" >nul 2>&1
if not errorlevel 1 (
    set "PY_CMD=python"
    goto found_python
)

py -3 -c "import sys" >nul 2>&1
if not errorlevel 1 (
    set "PY_CMD=py -3"
    goto found_python
)

if exist "C:\Users\ADMIN\AppData\Local\Programs\Python\Python313\python.exe" (
    "C:\Users\ADMIN\AppData\Local\Programs\Python\Python313\python.exe" -c "import sys" >nul 2>&1
    if not errorlevel 1 (
        set "PY_CMD=C:\Users\ADMIN\AppData\Local\Programs\Python\Python313\python.exe"
        goto found_python
    )
)

echo [ERROR] Python environment not detected!
echo Please make sure Python 3.10+ or Anaconda is installed on this PC.
echo.
pause
exit /b 1

:found_python
echo [OK] Python Engine : %PY_CMD%

:: 2. Project Directory Resolution
set "PROJ_DIR="

if exist "%~dp0start.py" (
    set "PROJ_DIR=%~dp0"
    goto found_proj
)

if exist "%~dp0problem statement 26033 solve by rohit naik\start.py" (
    set "PROJ_DIR=%~dp0problem statement 26033 solve by rohit naik\"
    goto found_proj
)

if exist "C:\Users\ADMIN\Desktop\problem statement 26033 solve by rohit naik\start.py" (
    set "PROJ_DIR=C:\Users\ADMIN\Desktop\problem statement 26033 solve by rohit naik\"
    goto found_proj
)

if exist "%USERPROFILE%\Desktop\problem statement 26033 solve by rohit naik\start.py" (
    set "PROJ_DIR=%USERPROFILE%\Desktop\problem statement 26033 solve by rohit naik\"
    goto found_proj
)

for /d %%D in ("%USERPROFILE%\Desktop\*26033*") do (
    if exist "%%D\start.py" (
        set "PROJ_DIR=%%D\"
        goto found_proj
    )
)

:found_proj
if "%PROJ_DIR%"=="" (
    echo [ERROR] Could not locate the AgroSetu project folder!
    echo Please make sure 'problem statement 26033 solve by rohit naik' exists on your Desktop.
    echo.
    pause
    exit /b 1
)

echo [OK] Project Path  : %PROJ_DIR%
echo.
echo [*] Launching AgroSetu Dashboard...
echo.

cd /d "%PROJ_DIR%"

if "%PY_CMD%"=="python" (
    python start.py
) else if "%PY_CMD%"=="py -3" (
    py -3 start.py
) else (
    "%PY_CMD%" start.py
)

if errorlevel 1 (
    echo.
    echo ===============================================================================
    echo [!] Server process stopped with error code %errorlevel%.
    echo ===============================================================================
    pause
)
