"""
activities_service.py
---------------------
Service for fetching, caching, and serving PARIVESH 2.0 master activity and subactivity datasets.
"""

import os
import json
import logging
import requests
from typing import List, Dict, Any
from ..config import settings
from ..cache import cache

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://parivesh.nic.in/",
}

def get_master_activities() -> List[Dict[str, Any]]:
    """
    Retrieves the list of all master activities.
    Checks Redis/Upstash cache first, then local fallback JSON, then live NIC API.
    """
    cache_key = "kya:master:activities"
    cached_data = cache.get(cache_key)
    if cached_data:
        logger.info("Serving master activities from cache (%s)", cache.client_type)
        return cached_data

    # 1. Local JSON fallback
    local_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "parivesh_activities.json")
    if not os.path.exists(local_path):
        local_path = "parivesh_activities.json"

    if os.path.exists(local_path):
        try:
            with open(local_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data:
                    cache.set(cache_key, data, ex=settings.CACHE_TTL_ACTIVITIES)
                    return data
        except Exception as e:
            logger.warning("Failed to load local parivesh_activities.json: %s", e)

    # 2. Live API query
    try:
        url = f"{settings.PARIVESH_API_BASE}/getactivities"
        res = requests.get(url, headers=HEADERS, timeout=8)
        if res.status_code == 200:
            data = res.json()
            if isinstance(data, list) and data:
                cache.set(cache_key, data, ex=settings.CACHE_TTL_ACTIVITIES)
                return data
    except Exception as e:
        logger.error("Error fetching activities from NIC API: %s", e)

    return []


def get_subactivities_by_id(activity_id: int) -> List[Dict[str, Any]]:
    """
    Retrieves sub-activities for a specific activity ID.
    Caches results per activity ID.
    """
    cache_key = f"kya:master:subactivities:{activity_id}"
    cached_data = cache.get(cache_key)
    if cached_data is not None:
        logger.info("Serving sub-activities for ID %s from cache", activity_id)
        return cached_data

    url = f"{settings.PARIVESH_API_BASE}/getSubactivity?id={activity_id}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=8)
        if res.status_code == 200:
            data = res.json()
            sub_list = []
            if isinstance(data, list):
                sub_list = data
            elif isinstance(data, dict):
                sub_list = data.get("data", data.get("result", []))
            
            cache.set(cache_key, sub_list, ex=settings.CACHE_TTL_SUBACTIVITIES)
            return sub_list
    except Exception as e:
        logger.warning("Could not query sub-activities for activity ID %s: %s", activity_id, e)

    return []
