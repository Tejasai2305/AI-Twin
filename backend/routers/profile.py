from fastapi import APIRouter, Depends, HTTPException

from backend.auth.dependencies import get_optional_user
from backend.services.profile_service import build_profile

router = APIRouter()


@router.get("/profile")
def profile(current_user=Depends(get_optional_user)):
    try:
        user_id = current_user["id"] if current_user else None
        return build_profile(user_id=user_id)
    except Exception as e:
        print("Profile build error:", e)
        raise HTTPException(status_code=500, detail="Unable to build profile.")
