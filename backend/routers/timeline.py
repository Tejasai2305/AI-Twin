from fastapi import APIRouter, Depends, HTTPException

from backend.auth.dependencies import get_optional_user
from backend.services.timeline_service import (
    get_timeline,
    get_timeline_years,
    get_timeline_categories,
)

router = APIRouter()


def _uid(current_user):
    return current_user["id"] if current_user else None


@router.get("/timeline")
def timeline(
    year: int | None = None,
    category: str | None = None,
    limit: int = 200,
    current_user=Depends(get_optional_user),
):
    try:
        return get_timeline(year=year, category=category, limit=limit, user_id=_uid(current_user))
    except Exception as e:
        print("Timeline error:", e)
        raise HTTPException(status_code=500, detail="Unable to build timeline.")


@router.get("/timeline/years")
def timeline_years(current_user=Depends(get_optional_user)):
    try:
        return get_timeline_years(user_id=_uid(current_user))
    except Exception as e:
        print("Timeline years error:", e)
        raise HTTPException(status_code=500, detail="Unable to list timeline years.")


@router.get("/timeline/categories")
def timeline_categories(current_user=Depends(get_optional_user)):
    try:
        return get_timeline_categories(user_id=_uid(current_user))
    except Exception as e:
        print("Timeline categories error:", e)
        raise HTTPException(status_code=500, detail="Unable to list timeline categories.")
