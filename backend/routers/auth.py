from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.auth.user_service import create_user, authenticate_user
from backend.auth.security import create_access_token
from backend.auth.dependencies import get_current_user

router = APIRouter()


class SignupRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=200)
    email: str | None = None


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/auth/signup")
def signup(data: SignupRequest):
    try:
        user = create_user(data.username, data.password, data.email)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    token = create_access_token(user["id"], user["username"])
    return {"access_token": token, "token_type": "bearer", "user": user}


@router.post("/auth/login")
def login(data: LoginRequest):
    user = authenticate_user(data.username, data.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid username or password.")

    token = create_access_token(user["id"], user["username"])
    return {"access_token": token, "token_type": "bearer", "user": user}


@router.get("/auth/me")
def me(current_user=Depends(get_current_user)):
    return current_user
