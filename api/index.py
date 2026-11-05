import os
import sys
from pathlib import Path

# Add project root to sys.path so backend and other modules can always be imported cleanly
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Expose FastAPI application instance for Vercel Serverless Functions
from backend.main import app

__all__ = ["app"]
