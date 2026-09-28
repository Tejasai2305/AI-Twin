from fastapi import APIRouter, Depends, HTTPException

from backend.auth.dependencies import get_optional_user
from backend.services.insights_service import generate_insights

router = APIRouter()


@router.get("/insights")
def insights(current_user=Depends(get_optional_user)):
    try:
        user_id = current_user["id"] if current_user else None
        return generate_insights(user_id=user_id)
    except Exception as e:
        print("Insights generation error:", e)
        raise HTTPException(status_code=500, detail="Unable to generate insights.")
