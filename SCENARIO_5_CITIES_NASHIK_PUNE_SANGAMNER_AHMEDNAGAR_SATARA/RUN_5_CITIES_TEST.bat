@echo off
TITLE 5-Cities Agro Corridor Test - Satara, Pune, Sangamner, Ahmednagar, Nashik
color 0B
cls

:menu
cls
echo ===============================================================================
echo      5-CITIES AGRO LOGISTICS CORRIDOR - SEPARATE TEST SCENARIO
echo          Satara, Pune, Sangamner, Ahmednagar, Nashik
echo                Problem Statement 26033 (Rohit Naik)
echo ===============================================================================
echo.
echo  Aap kya test karna chahte hain? (Select an option):
echo.
echo  [1] Run Full 5-City Route Optimization & Savings Audit (Pura Test)
echo  [2] Test City 1: NASHIK       (Farmer A - Tomato & Grapes)
echo  [3] Test City 2: SANGAMNER    (Farmer B - Chillies & Onions)
echo  [4] Test City 3: AHMEDNAGAR   (Farmer C - Pomegranates & Wheat)
echo  [5] Test City 4: PUNE         (Farmer D - Capsicum & Greens)
echo  [6] Test City 5: SATARA       (Farmer E - Ginger & Strawberries)
echo  [7] Exit (Band karein)
echo.
echo ===============================================================================
set /p choice="Enter your choice (1-7): "

if "%choice%"=="1" goto full_test
if "%choice%"=="2" goto test_nashik
if "%choice%"=="3" goto test_sangamner
if "%choice%"=="4" goto test_ahmednagar
if "%choice%"=="5" goto test_pune
if "%choice%"=="6" goto test_satara
if "%choice%"=="7" goto exit

echo.
echo [!] Invalid choice. Please enter 1 to 7.
pause
goto menu

:full_test
cls
color 0A
python "%~dp0TEST_5_CITIES_CORRIDOR.py"
echo.
echo Press any key to return to menu...
pause >nul
color 0B
goto menu

:test_nashik
cls
color 0E
python "%~dp0TEST_5_CITIES_CORRIDOR.py" --city Nashik
echo.
echo Press any key to return to menu...
pause >nul
color 0B
goto menu

:test_sangamner
cls
color 0E
python "%~dp0TEST_5_CITIES_CORRIDOR.py" --city Sangamner
echo.
echo Press any key to return to menu...
pause >nul
color 0B
goto menu

:test_ahmednagar
cls
color 0E
python "%~dp0TEST_5_CITIES_CORRIDOR.py" --city Ahmednagar
echo.
echo Press any key to return to menu...
pause >nul
color 0B
goto menu

:test_pune
cls
color 0E
python "%~dp0TEST_5_CITIES_CORRIDOR.py" --city Pune
echo.
echo Press any key to return to menu...
pause >nul
color 0B
goto menu

:test_satara
cls
color 0E
python "%~dp0TEST_5_CITIES_CORRIDOR.py" --city Satara
echo.
echo Press any key to return to menu...
pause >nul
color 0B
goto menu

:exit
exit /b 0
