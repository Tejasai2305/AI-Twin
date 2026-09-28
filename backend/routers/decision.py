from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.services.decision_service import compare_options

router = APIRouter()


class DecisionRequest(BaseModel):
    options: List[str] = Field(..., min_length=2, max_length=8)
    criteria: List[str] = Field(..., min_length=1, max_length=8)
    weights: Optional[Dict[str, float]] = None


@router.post("/decision/compare")
def compare(request: DecisionRequest):
    try:
        return compare_options(request.options, request.criteria, request.weights)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print("Decision support error:", e)
        raise HTTPException(status_code=500, detail="Unable to compare options.")
