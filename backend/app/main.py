"""
main.py
-------
FastAPI Application Entry Point for PARIVESH 2.0 KYA Backend Service.
Decoupled, high-performance architecture built for AWS ECS, Google Cloud Run, or VPS.
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

# ── CORS Middleware ───────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For Next.js on Vercel and local dev
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
def root_redirect():
    return {
        "service": settings.APP_NAME,
        "status": "online",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "cache": cache.status()
    }


@app.get("/api/v1/health", tags=["Health"])
def health_check():
    """Returns system status and cache health."""
    return {
        "status": "healthy",
        "cache_driver": cache.client_type,
        "cache_connected": True,
        "version": settings.APP_VERSION
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
