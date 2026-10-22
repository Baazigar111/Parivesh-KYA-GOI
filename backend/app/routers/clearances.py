"""
clearances.py
-------------
Router for clearance evaluation and Camunda DMN decision execution.
Supports both /api/v1/clearances and /api/clearances for universal compatibility.
"""

import logging
from fastapi import APIRouter, HTTPException
from ..schemas.clearance import (
    ClearanceRequest,
    ClearanceResponse,
    DMNEvaluateRequest,
    DMNEvaluateResponse,
)
from ..services.parivesh_service import execute_clearance_evaluation
from ..services.dmn_service import evaluate_camunda_dmn
from ..cache import cache

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Clearances & DMN"])


@router.post("/api/v1/clearances", response_model=ClearanceResponse, summary="Evaluate Project Clearances")
@router.post("/api/clearances", response_model=ClearanceResponse, summary="Evaluate Project Clearances (Direct)")
@router.post("/api/v1/clearances/", include_in_schema=False)
@router.post("/api/clearances/", include_in_schema=False)
def evaluate_project_clearances(request: ClearanceRequest):
    """
    Evaluates tentative environmental, forest, wildlife, and CRZ clearances.
    
    1. Checks Redis/Upstash cache for identical query coordinates & capacity.
    2. Runs headless evaluation with zero-click CAPTCHA resolution and spatial analysis.
    3. Intercepts Camunda DMN decision evaluation for full legal remarks.
    4. Caches result with a 1-hour TTL.
    """
    try:
        response = execute_clearance_evaluation(request)
        if not response.success:
            raise HTTPException(status_code=500, detail=response.message)
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error evaluating clearances: %s", e)
        raise HTTPException(status_code=500, detail=f"Clearance evaluation failed: {str(e)}")


@router.post("/api/v1/evaluate-dmn", response_model=DMNEvaluateResponse, summary="Direct Camunda DMN Evaluate")
@router.post("/api/evaluate-dmn", response_model=DMNEvaluateResponse, summary="Direct Camunda DMN Evaluate (Direct)")
@router.post("/api/v1/evaluate-dmn/", include_in_schema=False)
@router.post("/api/evaluate-dmn/", include_in_schema=False)
def evaluate_dmn_directly(request: DMNEvaluateRequest):
    """
    Directly evaluates a Camunda DMN decision table matching:
    POST /engine-rest/decision-definition/key/{decisionKey}/evaluate
    """
    try:
        raw_vars = {k: v.model_dump() for k, v in request.variables.items()}
        result = evaluate_camunda_dmn(request.decision_key, raw_vars)
        return DMNEvaluateResponse(
            decision_key=request.decision_key,
            result=result
        )
    except Exception as e:
        logger.exception("DMN evaluation error: %s", e)
        raise HTTPException(status_code=500, detail=f"DMN evaluation error: {str(e)}")


@router.post("/api/v1/cache/clear", summary="Clear Redis Cache")
@router.post("/api/cache/clear", summary="Clear Redis Cache (Direct)")
def clear_application_cache():
    """Administrative utility to clear Redis/in-memory cache."""
    try:
        cache.clear() if hasattr(cache, "clear") else None
        return {"status": "Cache cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
