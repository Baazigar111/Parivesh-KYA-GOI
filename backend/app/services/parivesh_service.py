"""
parivesh_service.py
-------------------
Core evaluation service bridging FastAPI endpoints with the Playwright browser engine,
Camunda DMN evaluation, and Redis/Upstash caching layer.
"""

import sys
import os
import time
import base64
import hashlib
import logging
from typing import Dict, Any, Optional

# Ensure project root is available to load existing parivesh_engine
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ..config import settings
from ..cache import cache
from ..schemas.clearance import (
    ClearanceRequest,
    ClearanceResponse,
    ClearanceItem,
    AdministrativeLocation,
)

logger = logging.getLogger(__name__)


def _generate_cache_key(req: ClearanceRequest) -> str:
    """Creates a deterministic hash of clearance query parameters."""
    lat_str = f"{req.latitude:.4f}" if req.latitude is not None else ""
    lon_str = f"{req.longitude:.4f}" if req.longitude is not None else ""
    raw = f"{req.activity_name}|{req.subactivity_name}|{req.capacity}|{req.location_mode}|{lat_str}|{lon_str}"
    if req.location_mode == "Upload KML" and req.kml_content:
        raw += f"|{hashlib.md5(req.kml_content.encode('utf-8')).hexdigest()}"
    return f"kya:eval:{hashlib.sha256(raw.encode('utf-8')).hexdigest()}"


class FastAPILoggerStatus:
    """Status callback logger for headless evaluation steps."""
    def __init__(self):
        self.logs = []

    def info(self, msg):
        logger.info(msg)
        self.logs.append(msg)

    def warning(self, msg):
        logger.warning(msg)
        self.logs.append(f"WARN: {msg}")

    def error(self, msg):
        logger.error(msg)
        self.logs.append(f"ERROR: {msg}")

    def success(self, msg):
        logger.info(msg)
        self.logs.append(f"SUCCESS: {msg}")


def execute_clearance_evaluation(req: ClearanceRequest) -> ClearanceResponse:
    """
    Executes or fetches cached clearance report.
    """
    start_time = time.time()
    cache_key = _generate_cache_key(req)

    # 1. Check Redis / Upstash Cache
    cached_report = cache.get(cache_key)
    if cached_report:
        logger.info("Serving clearance report from cache: %s", cache_key)
        resp_obj = ClearanceResponse(**cached_report)
        resp_obj.cached = True
        resp_obj.execution_time_seconds = round(time.time() - start_time, 2)
        return resp_obj

    # 2. Prepare parameters for Playwright Engine
    kml_bytes = None
    kml_name = req.kml_filename or "boundary.kml"
    if req.location_mode == "Upload KML" and req.kml_content:
        try:
            clean_kml = req.kml_content.strip()
            if clean_kml.startswith("<"):
                kml_bytes = clean_kml.encode("utf-8")
            else:
                try:
                    kml_bytes = base64.b64decode(clean_kml)
                except Exception:
                    kml_bytes = clean_kml.encode("utf-8")
        except Exception as e:
            logger.warning("Error parsing KML content: %s", e)
            kml_bytes = req.kml_content.encode("utf-8")

    from parivesh_engine import run_full_automated_lookup
    from .activities_service import resolve_statutory_unit

    threshold_meta = resolve_statutory_unit(
        subactivity_id=req.subactivity_id,
        subactivity_name=req.subactivity_name,
        activity_id=req.activity_id
    )
    resolved_unit = threshold_meta.get("unit") or req.capacity_unit or "sqmtr"
    resolved_param = threshold_meta.get("param") or "Project Capacity/Extent"
    req.capacity_unit = resolved_unit

    status_tracker = FastAPILoggerStatus()
    raw_results = run_full_automated_lookup(
        activity_name=req.activity_name,
        subactivity_name=req.subactivity_name,
        capacity=req.capacity,
        location_mode=req.location_mode,
        lat=req.latitude or 21.1976,
        lon=req.longitude or 72.8356,
        kml_bytes=kml_bytes,
        kml_name=kml_name,
        manual_captcha="",
        status_callback=status_tracker,
        session_state={},
    )

    if not raw_results:
        log_summary = " | ".join(status_tracker.logs[-3:]) if status_tracker.logs else "Execution halted unexpectedly."
        return ClearanceResponse(
            success=False,
            message=f"PARIVESH portal failed to return clearance data ({log_summary}).",
            execution_time_seconds=round(time.time() - start_time, 2)
        )

    # Convert clearances
    clearance_items = []
    for c in raw_results.get("clearances", []):
        clearance_items.append(
            ClearanceItem(
                sno=str(c.get("S.No", len(clearance_items) + 1)),
                approval=c.get("Approval", "Clearance"),
                applicability=c.get("Applicability", "No"),
                remarks=c.get("Remarks", "")
            )
        )

    # Convert admin locations
    admin_items = []
    for a in raw_results.get("administrative", []):
        admin_items.append(
            AdministrativeLocation(
                state=a.get("State", ""),
                district=a.get("District", ""),
                village=a.get("Village", "")
            )
        )

    # Ensure project data includes resolved statutory parameters
    project_data = dict(raw_results.get("project", {}))
    if not project_data:
        project_data = {
            "Project / Activity": req.activity_name,
            "Sub Activity": req.subactivity_name,
            "Project Capacity / Extent": f"{req.capacity} {resolved_unit}".strip()
        }
    project_data["Statutory Unit"] = resolved_unit
    project_data["Statutory Parameter"] = resolved_param

    response = ClearanceResponse(
        success=True,
        message="Clearance evaluation completed successfully.",
        cached=False,
        execution_time_seconds=round(time.time() - start_time, 2),
        clearances=clearance_items,
        toposheet=raw_results.get("toposheet", ""),
        administrative=admin_items,
        proximity=raw_results.get("proximity", []),
        project=project_data,
        map_png_url="/debug/parivesh_map_view.png" if raw_results.get("map_png") else None
    )

    # 3. Store in Redis/Upstash Cache
    try:
        cache.set(cache_key, response.model_dump(), ex=settings.CACHE_TTL_CLEARANCES)
        logger.info("Saved clearance report to cache with 1h TTL")
    except Exception as e:
        logger.warning("Failed to cache clearance response: %s", e)

    return response
