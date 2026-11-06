import os
import sys
from pathlib import Path

# Mark environment as Vercel serverless so backend adjusts static file serving
os.environ.setdefault("VERCEL", "1")

# Add project root to sys.path so backend modules import cleanly
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Patch FRONTEND_DIR in backend.main so StaticFiles mount is skipped on Vercel
# (Vercel serves frontend/** as static assets directly via routes in vercel.json)
import importlib
import types

# Import and expose the FastAPI application instance
from backend.main import app

# Remove the broken StaticFiles mount if it was registered
# (StaticFiles("/") at index -1 or last mount causes 500 on Vercel read-only fs)
routes_to_remove = []
for route in app.routes:
    if hasattr(route, 'name') and route.name == 'frontend':
        routes_to_remove.append(route)
for r in routes_to_remove:
    app.routes.remove(r)

__all__ = ["app"]
