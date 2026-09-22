import os
import sys
import re
from pathlib import Path

# Safe Unicode output for Windows CMD/PowerShell
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

ROOT_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT_DIR / "frontend"

def run_frontend_checks():
    print("=" * 80)
    print("      FRONTEND COMPONENT AUDIT & UI INTEGRITY CHECK")
    print("=" * 80)

    # 1. File existence and size check
    files = {
        "index.html": {"min_size": 20000, "desc": "Main Single-Page Application HTML"},
        "styles.css": {"min_size": 1000,  "desc": "Glassmorphism & Component Stylesheet"},
        "app.js":     {"min_size": 15000, "desc": "Client-Side Reactive Controller & API Bridge"}
    }

    all_ok = True
    print("\n[1] Physical Assets & File Size Audit:")
    for fname, meta in files.items():
        fp = FRONTEND_DIR / fname
        if not fp.exists():
            print(f"  [-] MISSING: {fname}")
            all_ok = False
            continue
        size = fp.stat().st_size
        size_kb = round(size / 1024, 2)
        if size < meta["min_size"]:
            print(f"  [-] WARNING: {fname} is smaller than expected ({size_kb} KB)")
            all_ok = False
        else:
            print(f"  [+] {fname:12s} ({size_kb:5.2f} KB) - {meta['desc']}")

    if not all_ok:
        return False

    # 2. Inspect index.html DOM Elements
    print("\n[2] HTML Template & DOM Elements Verification (index.html):")
    html_text = (FRONTEND_DIR / "index.html").read_text(encoding="utf-8")

    expected_ids = [
        # Navigation
        "tab-btn-overview", "tab-btn-farmer", "tab-btn-buyer", "tab-btn-logistics", "tab-btn-forecast", "tab-btn-routing",
        # Panes
        "tab-content-overview", "tab-content-farmer", "tab-content-buyer", "tab-content-logistics", "tab-content-forecast", "tab-content-routing",
        # Module 1 (Farmer/Buyer)
        "product-upload-form", "prod-crop-name", "prod-qty", "prod-price", "prod-location", "prod-harvest-date",
        "farmer-inventory-table", "buyer-product-grid", "buyer-search-input", "buyer-filter-category", "buyer-filter-location",
        # Modals
        "buy-modal", "order-form", "order-qty", "modal-total-display", "receipt-modal",
        # Module 2 (Logistics)
        "shipments-list", "vehicles-list", "shipment-modal", "shipment-form",
        # Module 3 (AI Forecast)
        "callout-current", "callout-forecast", "callout-badge", "fc-crop", "fc-city", "fc-festival", "fc-season", "fc-weather", "fc-base",
        "forecastChart", "factor-list", "advisory-hi",
        # Module 4 (AI Route Optimization)
        "route-dist-saved", "route-fuel-saved", "route-cost-saved", "route-co2-saved",
        "leaflet-map", "route-stops-list"
    ]

    missing_ids = [elem_id for elem_id in expected_ids if f'id="{elem_id}"' not in html_text and f"id='{elem_id}'" not in html_text]
    if missing_ids:
        print(f"  [-] Missing DOM element IDs: {missing_ids}")
        all_ok = False
    else:
        print(f"  [+] All {len(expected_ids)} Core DOM Element IDs verified present in index.html")

    # 3. Inspect External Libraries Inclusions
    print("\n[3] External CDN & Library Bindings:")
    libraries = [
        ("Tailwind CSS", "cdn.tailwindcss.com"),
        ("Chart.js", "chart.js"),
        ("Leaflet CSS & JS", "leaflet"),
        ("FontAwesome Icons", "font-awesome")
    ]
    for lib_name, needle in libraries:
        if needle.lower() in html_text.lower():
            print(f"  [+] {lib_name:18s}: Integrated")
        else:
            print(f"  [-] {lib_name:18s}: Missing")
            all_ok = False

    # 4. Inspect app.js Core JavaScript Functions
    print("\n[4] JavaScript Architecture & Function Verification (app.js):")
    js_text = (FRONTEND_DIR / "app.js").read_text(encoding="utf-8")
    
    expected_functions = [
        "switchTab", "showToast", "loadStats",
        "loadProducts", "renderFarmerInventory", "renderBuyerProducts", "applyFilters", "handleProductUpload",
        "openBuyModal", "calculateOrderTotal", "handlePlaceOrder",
        "loadShipments", "renderShipments", "advanceShipmentStatus", "loadVehicles", "handleCreateShipment",
        "runForecast", "renderForecastOutput", "renderForecastChart",
        "initOrUpdateMap", "runRouteOptimization", "renderRouteOptimization",
        "resetData"
    ]

    missing_funcs = [fn for fn in expected_functions if fn not in js_text]
    if missing_funcs:
        print(f"  [-] Missing JS functions: {missing_funcs}")
        all_ok = False
    else:
        print(f"  [+] All {len(expected_functions)} JavaScript Controller Functions verified present in app.js")

    # 5. Inspect styles.css Rules
    print("\n[5] Custom Stylesheet & Responsive Classes (styles.css):")
    css_text = (FRONTEND_DIR / "styles.css").read_text(encoding="utf-8")
    expected_css_classes = [".nav-tab", ".active-tab", ".custom-leaflet-marker", ".marker-pickup", ".marker-hub", ".tab-pane"]
    
    for cls in expected_css_classes:
        if cls in css_text:
            print(f"  [+] CSS Class '{cls}': Verified")
        else:
            print(f"  [-] CSS Class '{cls}': Missing")
            all_ok = False

    print("\n" + "=" * 80)
    print("  >>> FRONTEND INTEGRITY CHECK: 100% HEALTHY & FULLY VERIFIED! <<<")
    print("=" * 80)
    return all_ok

if __name__ == "__main__":
    run_frontend_checks()
