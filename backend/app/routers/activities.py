"""
activities.py
-------------
Router for PARIVESH 2.0 master activity and subactivity dropdown endpoints.
Supports both /api/v1/ and /api/ paths.
"""

from typing import List, Dict, Any
from fastapi import APIRouter, Query, HTTPException
from ..services.activities_service import get_master_activities, get_subactivities_by_id

router = APIRouter(tags=["Master Data"])


@router.get("/api/v1/activities", response_model=List[Dict[str, Any]], summary="Get Master Activities / Sectors")
@router.get("/api/activities", response_model=List[Dict[str, Any]], summary="Get Master Activities / Sectors (Direct)")
@router.get("/api/v1/activities/", include_in_schema=False)
@router.get("/api/activities/", include_in_schema=False)
def list_activities():
    """
    Returns the list of available PARIVESH 2.0 project activities.
    Cached via Redis/Upstash for fast response times.
    """
    activities = get_master_activities()
    if not activities:
        raise HTTPException(status_code=503, detail="Unable to retrieve activities from cache or NIC portal")
    return activities


@router.get("/api/v1/subactivities", response_model=List[Dict[str, Any]], summary="Get Sub-Activities for Activity ID")
@router.get("/api/subactivities", response_model=List[Dict[str, Any]], summary="Get Sub-Activities for Activity ID (Direct)")
@router.get("/api/v1/subactivities/", include_in_schema=False)
@router.get("/api/subactivities/", include_in_schema=False)
def list_subactivities(activity_id: int = Query(..., description="ID of the parent activity")):
    """
    Returns the sub-activities corresponding to an activity ID.
    Cached individually per activity ID.
    """
    subactivities = get_subactivities_by_id(activity_id)
    return subactivities
