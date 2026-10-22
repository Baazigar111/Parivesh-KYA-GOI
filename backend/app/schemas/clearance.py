"""
clearance.py
------------
Pydantic schemas for clearance requests, DMN evaluation, and responses.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


# ── Location Schema ──────────────────────────────────────────────────────────
class PointLocation(BaseModel):
    latitude: float = Field(..., example=21.1976)
    longitude: float = Field(..., example=72.8356)


# ── Clearance Request Schema ─────────────────────────────────────────────────
class ClearanceRequest(BaseModel):
    activity_name: str = Field(..., description="Project sector/activity name (e.g. Airports, Thermal Power)")
    activity_id: Optional[int] = Field(None, description="Activity ID from /activities")
    subactivity_name: str = Field(..., description="Sub-activity name or category")
    subactivity_id: Optional[int] = Field(None, description="Sub-activity ID from /subactivities")
    capacity: str = Field("250", description="Project capacity or extent value")
    capacity_unit: Optional[str] = Field("sqmtr", description="Capacity unit")
    
    # Location
    location_mode: str = Field("Point Location", description="'Point Location' or 'Upload KML'")
    latitude: Optional[float] = Field(21.1976, description="Latitude coordinate")
    longitude: Optional[float] = Field(72.8356, description="Longitude coordinate")
    kml_content: Optional[str] = Field(None, description="Base64 encoded or raw string KML content")
    kml_filename: Optional[str] = Field("boundary.kml", description="KML file name")


# ── Clearance Items & Detailed Results ───────────────────────────────────────
class ClearanceItem(BaseModel):
    sno: str = Field("1", alias="S.No")
    approval: str = Field(..., alias="Approval")
    applicability: str = Field("No", alias="Applicability")
    remarks: str = Field("", alias="Remarks")

    class Config:
        populate_by_name = True


class AdministrativeLocation(BaseModel):
    state: str = Field("", alias="State")
    district: str = Field("", alias="District")
    village: str = Field("", alias="Village")

    class Config:
        populate_by_name = True


class ClearanceResponse(BaseModel):
    success: bool = True
    message: str = "Clearance evaluation completed successfully."
    cached: bool = False
    execution_time_seconds: float = 0.0
    
    clearances: List[ClearanceItem] = []
    toposheet: str = ""
    administrative: List[AdministrativeLocation] = []
    proximity: List[Dict[str, Any]] = []
    project: Dict[str, Any] = {}
    map_png_url: Optional[str] = None


# ── Camunda DMN Schemas ───────────────────────────────────────────────────────
class DMNVariableValue(BaseModel):
    value: Any
    type: Optional[str] = None


class DMNEvaluateRequest(BaseModel):
    decision_key: str = Field(..., example="decision_kya_clearances")
    variables: Dict[str, DMNVariableValue] = Field(
        ...,
        example={
            "envclear": {"value": True, "type": "Boolean"},
            "forclear": {"value": False, "type": "Boolean"},
            "wildlifeclear": {"value": False, "type": "Boolean"},
            "crz": {"value": False, "type": "Boolean"},
        }
    )


class DMNEvaluateResponse(BaseModel):
    decision_key: str
    result: List[Dict[str, Any]]
