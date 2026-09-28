"""
FastAPI dependencies for reading the current user from a Bearer token.

Two variants:
  - get_current_user: raises 401 if there's no valid token. Used for
    endpoints that must be authenticated (e.g. /auth/me).
  - get_optional_user: returns the user dict if a valid token is
    present, otherwise None. Used to make data user-scoped WHEN auth
    is in use, without breaking the app for anyone running it as a
    single-user desktop tool with no login at all (the project's
    existing default mode).
"""

from typing import Optional

from fastapi import Header, HTTPException

from backend.auth.security import decode_access_token
from backend.auth.user_service import get_user_by_id


def _extract_user(authorization: Optional[str]):
    if not authorization or not authorization.startswith("Bearer "):
        return None

    token = authorization.removeprefix("Bearer ").strip()
    payload = decode_access_token(token)

    if payload is None:
        return None

    user_id = payload.get("sub")
    if user_id is None:
        return None

    return get_user_by_id(int(user_id))


def get_current_user(authorization: Optional[str] = Header(default=None)):
    user = _extract_user(authorization)
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated.")
    return user


def get_optional_user(authorization: Optional[str] = Header(default=None)):
    return _extract_user(authorization)
