import os
import sys
from pathlib import Path

# Add project root to sys.path so backend and other modules can always be imported cleanly
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Expose the FastAPI application instance for Vercel and ASGI servers
from backend.main import app

__all__ = ["app"]

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
