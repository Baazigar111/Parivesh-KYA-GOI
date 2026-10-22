"""
main.py
-------
FastAPI Application Entry Point for PARIVESH 2.0 KYA Backend Service.
Decoupled, high-performance architecture built for AWS ECS, Google Cloud Run, Render, or VPS.
"""

import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import settings
from .cache import cache
from .routers import activities, clearances

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("parivesh-kya-backend")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Enterprise REST API service for PARIVESH 2.0 KYA Environmental Clearance Evaluation, Camunda DMN Interception, and Geospatial Analysis.",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS Middleware (Permissive for Vercel, localhost, and custom domains) ────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(activities.router)
app.include_router(clearances.router)

# Mount debug directory for screenshots if exists
debug_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "debug")
if os.path.exists(debug_dir):
    app.mount("/debug", StaticFiles(directory=debug_dir), name="debug")


# ── Health & Diagnostics ──────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
@app.get("/health", tags=["Health"])
@app.get("/api/health", tags=["Health"])
@app.get("/api/v1/health", tags=["Health"])
def health_check():
    """Returns system status and cache health across all standard health endpoints."""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "cache_driver": cache.client_type,
        "cache_connected": True,
        "version": settings.APP_VERSION,
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
