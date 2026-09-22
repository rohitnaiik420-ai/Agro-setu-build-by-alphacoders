# Test Scenarios & Component Verification Suite
### Problem Statement 26033 | Solved by Rohit Naik

This special folder contains comprehensive test scenarios, real-world agro-industry examples, and dedicated diagnostic tools to check the **Backend**, **Frontend**, and **Database**.

---

## 📁 Folder Contents & Structure

| File | Description |
|------|-------------|
| **`user_problem_statement_scenario.py`** | **Exact Canonical User Scenario from Problem Statement 26033**:<br>• Part 1: Farmer upload & Buyer order with simulated payment<br>• Part 2: Logistics pipeline (Farmer, Nashik ➔ Collection Center ➔ Pune Buyer)<br>• Part 3: AI Demand Forecasting (Pune Tomato: 1,000 kg ➔ 1,500 kg, +50%)<br>• Part 4: AI Route Optimization (5 Farmers: Nashik, Sangamner, Ahmednagar, Pune, Satara) |
| **`scenario_onion_festival_rush.py`** | **Scenario 2 (Onion Festival Surge)**: Nashik & Lasalgaon Red Onion wholesale supply to Mumbai Vashi APMC during Diwali with heavy rain weather disruption and 10T Lorry dispatch. |
| **`scenario_cold_chain_export.py`** | **Scenario 3 (Cold-Chain Logistics)**: Ahmednagar Bhagwa Pomegranates & Satara Strawberries high-value perishable transport using refrigerated container vans (+2°C to +4°C). |
| **`scenario_multi_district_pooling.py`** | **Scenario 4 (Mega-Corridor Pooling)**: 7-district multi-stop agro route solver (Nashik ➔ Sangamner ➔ Shrirampur ➔ Ahmednagar ➔ Pune ➔ Satara ➔ Kolhapur ➔ Mumbai JNPT export hub). |
| **`check_backend.py`** | Dedicated backend diagnostic script auditing all 20+ FastAPI REST endpoints, status codes, query filters, and response payloads. |
| **`check_database.py`** | Dedicated database diagnostic script auditing SQLite file integrity (`PRAGMA integrity_check`), table schemas, foreign keys, row counts, and ACID transactions (commit/rollback). |
| **`check_frontend.py`** | Dedicated frontend diagnostic script auditing HTML DOM element IDs, Chart.js canvas binding, Leaflet map container, JavaScript controller functions, and CSS stylesheets. |
| **`sample_payloads.json`** | Ready-to-use JSON request and response payloads for manual testing with Postman, curl, or Thunder Client. |
| **`run_all_tests.bat`** | 1-Click Windows batch script to run the entire suite and print a colored executive report. |

---

## 🚀 How to Run the Tests

### Option 1: One-Click Runner (Windows Batch)
Simply double-click:
```cmd
test_scenarios_and_examples\run_all_tests.bat
```

### Option 2: Run Individual Scenarios via Python
```powershell
# 1. Run the canonical user problem statement scenario:
python test_scenarios_and_examples\user_problem_statement_scenario.py

# 2. Run the Onion festival rush scenario:
python test_scenarios_and_examples\scenario_onion_festival_rush.py

# 3. Run the cold-chain export scenario:
python test_scenarios_and_examples\scenario_cold_chain_export.py

# 4. Run the 7-district mega pooling corridor scenario:
python test_scenarios_and_examples\scenario_multi_district_pooling.py

# 5. Run dedicated database health check:
python test_scenarios_and_examples\check_database.py

# 6. Run dedicated frontend UI audit:
python test_scenarios_and_examples\check_frontend.py

# 7. Run dedicated backend API check:
python test_scenarios_and_examples\check_backend.py
```
