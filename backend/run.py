"""
run.py
------
Local runner for FastAPI backend service.
"""

import sys
import os
import uvicorn

# Add root directory to PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

if __name__ == "__main__":
    from backend.app.config import settings
    print(f"🌿 Starting {settings.APP_NAME} on http://localhost:{settings.PORT}")
    print(f"📖 Interactive Swagger Docs: http://localhost:{settings.PORT}/docs")
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=settings.PORT, reload=True)
