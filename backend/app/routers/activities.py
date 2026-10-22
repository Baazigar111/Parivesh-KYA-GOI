"""
activities.py
-------------
Router for PARIVESH 2.0 master activity and subactivity dropdown endpoints.
"""

from typing import List, Dict, Any
from fastapi import APIRouter, Query, HTTPException
from ..services.activities_service import get_master_activities, get_subactivities_by_id

router = APIRouter(prefix="/api/v1", tags=["Master Data"])


@router.get("/activities", response_model=List[Dict[str, Any]], summary="Get Master Activities / Sectors")
def list_activities():
    """
    Returns the list of available PARIVESH 2.0 project activities.
    Cached via Redis/Upstash for fast 24-hour response times.
    """
    activities = get_master_activities()
    if not activities:
        raise HTTPException(status_code=503, detail="Unable to retrieve activities from cache or NIC portal")
    return activities


@router.get("/subactivities", response_model=List[Dict[str, Any]], summary="Get Sub-Activities for Activity ID")
def list_subactivities(activity_id: int = Query(..., description="ID of the parent activity")):
    """
    Returns the sub-activities corresponding to an activity ID.
    Cached individually per activity ID.
    """
    subactivities = get_subactivities_by_id(activity_id)
    return subactivities
