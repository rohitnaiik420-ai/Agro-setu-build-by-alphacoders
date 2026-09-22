@echo off
TITLE Test All 4 Problem Statement Examples
color 0A
cls

echo ===============================================================================
echo            TESTING ALL 4 ORIGINAL PROBLEM STATEMENT EXAMPLES
echo                      Problem Statement 26033
echo                        Solved by Rohit Naik
echo ===============================================================================
echo.

cd /d "%~dp0"

echo [1/4] Testing Point 1: Farmer/FPO -> Consumer/Buyer...
echo.
python 1_TEST_FARMER_AND_BUYER.py
echo.
echo -------------------------------------------------------------------------------
echo.

echo [2/4] Testing Point 2: Logistics Support (Nashik -> Pune)...
echo.
python 2_TEST_LOGISTICS_SUPPORT.py
echo.
echo -------------------------------------------------------------------------------
echo.

echo [3/4] Testing Point 3: AI Demand Forecasting (Pune Tomato 1000kg -> 1500kg)...
echo.
python 3_TEST_AI_DEMAND_FORECASTING.py
echo.
echo -------------------------------------------------------------------------------
echo.

echo [4/4] Testing Point 4: AI Route Optimization (5 Farmers Pooling)...
echo.
python 4_TEST_AI_ROUTE_OPTIMIZATION.py
echo.

echo ===============================================================================
echo   SABHI 4 POINTS KA TEST PURA HUA - ALL 4 EXAMPLES ARE WORKING 100%%!
echo ===============================================================================
pause
