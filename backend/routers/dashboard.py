from fastapi import APIRouter, Depends, HTTPException

from backend.auth.dependencies import get_optional_user
from backend.services.dashboard_service import build_dashboard

router = APIRouter()


@router.get("/dashboard")
def dashboard(current_user=Depends(get_optional_user)):
    try:
        user_id = current_user["id"] if current_user else None
        return build_dashboard(user_id=user_id)
    except Exception as e:
        print("Dashboard build error:", e)
        raise HTTPException(status_code=500, detail="Unable to build dashboard.")
