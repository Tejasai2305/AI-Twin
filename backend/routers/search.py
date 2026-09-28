from fastapi import APIRouter, Depends, HTTPException

from backend.auth.dependencies import get_optional_user
from backend.services.global_search_service import global_search

router = APIRouter()


@router.get("/search")
def search(q: str = "", current_user=Depends(get_optional_user)):
    try:
        user_id = current_user["id"] if current_user else None
        return global_search(q, user_id=user_id)
    except Exception as e:
        print("Global search error:", e)
        raise HTTPException(status_code=500, detail="Search failed.")
