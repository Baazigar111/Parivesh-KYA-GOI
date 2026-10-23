"""
config.py
---------
Configuration management for PARIVESH KYA FastAPI Backend.
Loads environment variables with intelligent defaults for local development
and containerized cloud execution (AWS ECS, Google Cloud Run, VPS).
"""

import os
from pathlib import Path
from typing import List

class Settings:
    # Project Root Directory
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent

    # Service Information
    APP_NAME: str = "PARIVESH 2.0 KYA Backend API"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() in ("true", "1")
    PORT: int = int(os.getenv("PORT", "8000"))
    HOST: str = os.getenv("HOST", "0.0.0.0")

    # CORS settings (Allows Next.js frontend on Vercel, localhost, etc.)
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "https://*.vercel.app",
        "*"
    ]

    # Caching Layer (Redis / Upstash)
    REDIS_URL: str = os.getenv("REDIS_URL", "")
    UPSTASH_REDIS_REST_URL: str = os.getenv("UPSTASH_REDIS_REST_URL", "")
    UPSTASH_REDIS_REST_TOKEN: str = os.getenv("UPSTASH_REDIS_REST_TOKEN", "")

    # Cache TTLs (in seconds)
    CACHE_TTL_ACTIVITIES: int = int(os.getenv("CACHE_TTL_ACTIVITIES", "86400"))      # 24 Hours
    CACHE_TTL_SUBACTIVITIES: int = int(os.getenv("CACHE_TTL_SUBACTIVITIES", "86400"))  # 24 Hours
    CACHE_TTL_THRESHOLDS: int = int(os.getenv("CACHE_TTL_THRESHOLDS", "86400"))        # 24 Hours
    CACHE_TTL_CLEARANCES: int = int(os.getenv("CACHE_TTL_CLEARANCES", "3600"))        # 1 Hour

    # PARIVESH Government Endpoints
    PARIVESH_API_BASE: str = os.getenv("PARIVESH_API_BASE", "https://parivesh.nic.in/parivesh_api/kya")
    PARIVESH_KYA_PORTAL: str = os.getenv("PARIVESH_KYA_PORTAL", "https://parivesh.nic.in/kya/#/")

    # Official Government Master Dataset Paths
    ACTIVITIES_JSON_PATH: str = os.getenv(
        "ACTIVITIES_JSON_PATH",
        str(BASE_DIR / "parivesh_activities.json")
    )
    SUBACTIVITIES_JSON_PATH: str = os.getenv(
        "SUBACTIVITIES_JSON_PATH",
        str(BASE_DIR / "parivesh_subactivities.json")
    )
    THRESHOLD_UNITS_JSON_PATH: str = os.getenv(
        "THRESHOLD_UNITS_JSON_PATH",
        str(BASE_DIR / "parivesh_threshold_units.json")
    )

settings = Settings()

