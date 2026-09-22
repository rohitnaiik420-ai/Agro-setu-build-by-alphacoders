@echo off
TITLE AgroSetu AI - Test Scenarios & Component Audit Suite
color 0B
cls

echo ===============================================================================
echo       AGROSETU AI - TEST SCENARIOS & SYSTEM COMPONENT AUDIT SUITE
echo                 Problem Statement 26033 (Rohit Naik)
echo ===============================================================================
echo.

cd /d "%~dp0.."
echo [1/7] Running Canonical User Scenario 1 (Problem Statement 26033)...
python test_scenarios_and_examples\user_problem_statement_scenario.py
if errorlevel 1 goto error
echo.

echo [2/7] Running Scenario 2 (Nashik Onion Diwali Rush to Mumbai)...
python test_scenarios_and_examples\scenario_onion_festival_rush.py
if errorlevel 1 goto error
echo.

echo [3/7] Running Scenario 3 (Perishable Cold-Chain Export Sourcing)...
python test_scenarios_and_examples\scenario_cold_chain_export.py
if errorlevel 1 goto error
echo.

echo [4/7] Running Scenario 4 (7-District Mega-Corridor Route Pooling)...
python test_scenarios_and_examples\scenario_multi_district_pooling.py
if errorlevel 1 goto error
echo.

echo [5/7] Running Dedicated Database Audit (SQLite)...
python test_scenarios_and_examples\check_database.py
if errorlevel 1 goto error
echo.

echo [6/7] Running Dedicated Frontend UI Audit (HTML/CSS/JS)...
python test_scenarios_and_examples\check_frontend.py
if errorlevel 1 goto error
echo.

echo [7/7] Running Dedicated Backend Audit (FastAPI REST APIs)...
python test_scenarios_and_examples\check_backend.py
if errorlevel 1 goto error
echo.

color 0A
echo ===============================================================================
echo   CONGRATULATIONS! ALL 4 SCENARIOS AND ALL 3 COMPONENT CHECKS PASSED!
echo   Backend, Frontend, and Database are 100%% OPERATIONAL with ZERO ERRORS.
echo ===============================================================================
pause
exit /b 0

:error
color 0C
echo.
echo ===============================================================================
echo   [ERROR] One or more tests failed. Please review the output above.
echo ===============================================================================
pause
exit /b 1
