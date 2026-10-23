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
    local_path = settings.ACTIVITIES_JSON_PATH
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


def get_threshold_units_catalog() -> Dict[str, Any]:
    """
    Retrieves the statutory threshold units dictionary (mapped by subactivity and activity).
    """
    cache_key = "kya:master:threshold_units"
    cached_data = cache.get(cache_key)
    if cached_data is not None:
        return cached_data

    local_path = settings.THRESHOLD_UNITS_JSON_PATH
    if not os.path.exists(local_path):
        local_path = "parivesh_threshold_units.json"

    catalog = {}
    if os.path.exists(local_path):
        try:
            with open(local_path, "r", encoding="utf-8") as f:
                catalog = json.load(f)
                if catalog:
                    cache.set(cache_key, catalog, ex=settings.CACHE_TTL_THRESHOLDS)
                    return catalog
        except Exception as e:
            logger.warning("Failed to load threshold_units.json: %s", e)

    return catalog


def resolve_statutory_unit(
    subactivity_id: int = None,
    subactivity_name: str = None,
    activity_id: int = None
) -> Dict[str, str]:
    """
    Resolves the exact statutory unit (e.g. 'Km', 'sqmtr', 'Ha') and parameter name
    (e.g. 'Length of air strip', 'Built up Area') for a given sub-activity or activity.
    """
    catalog = get_threshold_units_catalog()
    by_sub = catalog.get("by_subactivity", {})
    by_act = catalog.get("by_activity", {})

    # 1. Match by subactivity ID directly
    if subactivity_id is not None and str(subactivity_id) in by_sub:
        matched = by_sub[str(subactivity_id)]
        if matched and len(matched) > 0:
            return {"unit": matched[0].get("unit", "sqmtr"), "param": matched[0].get("param", "Project Capacity/Extent")}

    # 2. Match by subactivity name lookup in local subactivities catalog
    if subactivity_name and activity_id:
        clean_name = " ".join(subactivity_name.strip().lower().split())
        sub_list = get_subactivities_by_id(activity_id)
        for s in sub_list:
            s_name = " ".join((s.get("name") or s.get("sub_activity_name") or "").strip().lower().split())
            if s_name == clean_name and s.get("id"):
                matched = by_sub.get(str(s["id"]))
                if matched and len(matched) > 0:
                    return {"unit": matched[0].get("unit", "sqmtr"), "param": matched[0].get("param", "Project Capacity/Extent")}

    # 3. Match by activity ID
    if activity_id is not None and str(activity_id) in by_act:
        matched = by_act[str(activity_id)]
        if matched and len(matched) > 0:
            return {"unit": matched[0].get("unit", "sqmtr"), "param": matched[0].get("param", "Project Capacity/Extent")}

    return {"unit": "sqmtr", "param": "Project Capacity/Extent"}


def get_subactivities_by_id(activity_id: int) -> List[Dict[str, Any]]:
    """
    Retrieves sub-activities for a specific activity ID.
    Enriches each sub-activity with its official statutory unit and parameter name.
    Caches results per activity ID.
    """
    cache_key = f"kya:master:subactivities:{activity_id}"
    cached_data = cache.get(cache_key)
    if cached_data is not None:
        logger.info("Serving sub-activities for ID %s from cache", activity_id)
        return cached_data

    sub_list = []

    # 1. Check local seed catalog 'parivesh_subactivities.json'
    local_sub_path = settings.SUBACTIVITIES_JSON_PATH
    if not os.path.exists(local_sub_path):
        local_sub_path = "parivesh_subactivities.json"

    if os.path.exists(local_sub_path):
        try:
            with open(local_sub_path, "r", encoding="utf-8") as f:
                catalog = json.load(f)
                if str(activity_id) in catalog and catalog[str(activity_id)]:
                    sub_list = catalog[str(activity_id)]
        except Exception as e:
            logger.warning("Failed to load local parivesh_subactivities.json: %s", e)

    # 2. Live NIC API fallback if local catalog not found
    if not sub_list:
        url = f"{settings.PARIVESH_API_BASE}/getSubactivity?id={activity_id}"
        try:
            res = requests.get(url, headers=HEADERS, timeout=8)
            if res.status_code == 200:
                data = res.json()
                if isinstance(data, list):
                    sub_list = data
                elif isinstance(data, dict):
                    sub_list = data.get("data", data.get("result", []))
        except Exception as e:
            logger.warning("Could not query sub-activities for activity ID %s: %s", activity_id, e)

    # 3. Enrich sub-activities with statutory threshold units
    enriched = []
    threshold_catalog = get_threshold_units_catalog().get("by_subactivity", {})
    for item in sub_list:
        copy_item = dict(item)
        sub_id_str = str(copy_item.get("id", ""))
        if sub_id_str in threshold_catalog and threshold_catalog[sub_id_str]:
            copy_item["unit"] = threshold_catalog[sub_id_str][0].get("unit", "sqmtr")
            copy_item["param"] = threshold_catalog[sub_id_str][0].get("param", "Project Capacity/Extent")
        else:
            copy_item["unit"] = "sqmtr"
            copy_item["param"] = "Project Capacity/Extent"
        enriched.append(copy_item)

    if enriched:
        cache.set(cache_key, enriched, ex=settings.CACHE_TTL_SUBACTIVITIES)
        return enriched

    return []

