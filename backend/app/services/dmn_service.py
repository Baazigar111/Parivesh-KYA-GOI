"""
dmn_service.py
--------------
Camunda DMN Evaluator Service for PARIVESH 2.0 KYA.
Handles POST /engine-rest/decision-definition/key/{key}/evaluate specifications.
"""

import os
import logging
import requests
from typing import Dict, Any, List
from ..schemas.clearance import ClearanceItem

logger = logging.getLogger(__name__)

CAMUNDA_REST_BASE = os.getenv("CAMUNDA_REST_BASE", "")

def evaluate_camunda_dmn(decision_key: str, variables: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Evaluates a DMN table via Camunda REST API if CAMUNDA_REST_BASE is provided.
    Falls back to the internal PARIVESH DMN rule matrix.
    """
    if CAMUNDA_REST_BASE:
        url = f"{CAMUNDA_REST_BASE.rstrip('/')}/engine-rest/decision-definition/key/{decision_key}/evaluate"
        try:
            payload = {"variables": variables}
            res = requests.post(url, json=payload, timeout=10)
            if res.status_code == 200:
                data = res.json()
                if isinstance(data, list):
                    return data
        except Exception as e:
            logger.error("Remote Camunda DMN evaluation failed: %s", e)

    # Internal DMN Rule Engine
    return _evaluate_internal_dmn(variables)


def _evaluate_internal_dmn(variables: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Direct evaluation of PARIVESH 4-pillar environmental decision tables.
    """
    def get_val(var_name, default=False):
        v = variables.get(var_name, {})
        if isinstance(v, dict):
            return v.get("value", default)
        return v if v is not None else default

    envclear = get_val("envclear", False)
    forclear = get_val("forclear", False)
    wildlifeclear = get_val("wildlifeclear", False)
    crz = get_val("crz", False)

    remark_ec = "The proposed project/activity is covered under Category B/A of the Schedule to the EIA Notification, 2006 (as amended) and requires Prior Environmental Clearance." if envclear else "The proposed activity or capacity does not attract the provisions of EIA Notification 2006."
    remark_fc = "The proposed project involves diversion of forest land and requires prior Forest Clearance under Section 2 of the Van (Sanrakshan Evam Samvardhan) Adhiniyam, 1980." if forclear else "The project boundary is not falling in any notified Forest Land as per state forest spatial layer."
    remark_wl = "The project area falls within a Protected Area (National Park / Sanctuary) or its notified Eco-Sensitive Zone (ESZ), requiring prior National Board for Wildlife (NBWL) clearance." if wildlifeclear else "The project boundary does not fall within 10 km of any notified National Park or Wildlife Sanctuary."
    remark_crz = "The project area intersects Coastal Regulation Zone (CRZ-I/II/III/IV) and requires prior clearance from the respective State Coastal Zone Management Authority (SCZMA)." if crz else "The project location does not fall within Coastal Regulation Zone boundaries."

    return [{
        "remark_ec": {"value": remark_ec, "type": "String"},
        "remark_fc": {"value": remark_fc, "type": "String"},
        "remark_wl": {"value": remark_wl, "type": "String"},
        "remark_crz": {"value": remark_crz, "type": "String"}
    }]


def format_dmn_to_clearances(dmn_result: Dict[str, Any], variables: Dict[str, Any]) -> List[ClearanceItem]:
    """
    Converts DMN decision evaluation dictionary to executive clearance items.
    """
    def get_bool(key):
        v = variables.get(key, {})
        return v.get("value", False) if isinstance(v, dict) else bool(v)

    def determine_app(flag, remark):
        rem_lower = str(remark).lower()
        if flag:
            return "Yes"
        if "not falling" in rem_lower or "not covered" in rem_lower or "does not attract" in rem_lower:
            return "No"
        if "falling in" in rem_lower or "covered under" in rem_lower or "requires prior" in rem_lower:
            return "Yes"
        return "No"

    ec_rem = dmn_result.get("remark_ec", {}).get("value", "")
    fc_rem = dmn_result.get("remark_fc", {}).get("value", "")
    wl_rem = dmn_result.get("remark_wl", {}).get("value", "")
    crz_rem = dmn_result.get("remark_crz", {}).get("value", "")

    return [
        ClearanceItem(
            sno="1",
            approval="Environmental clearance",
            applicability=determine_app(get_bool("envclear"), ec_rem),
            remarks=ec_rem
        ),
        ClearanceItem(
            sno="2",
            approval="Forest Clearance",
            applicability=determine_app(get_bool("forclear"), fc_rem),
            remarks=fc_rem
        ),
        ClearanceItem(
            sno="3",
            approval="Wildlife Clearance",
            applicability=determine_app(get_bool("wildlifeclear"), wl_rem),
            remarks=wl_rem
        ),
        ClearanceItem(
            sno="4",
            approval="Coastal Regulation Clearance",
            applicability=determine_app(get_bool("crz"), crz_rem),
            remarks=crz_rem
        ),
    ]
