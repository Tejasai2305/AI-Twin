import os

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.auth.user_service import create_user, authenticate_user
from backend.auth.security import create_access_token
from backend.auth.dependencies import get_current_user
from backend.auth.password_reset_service import (
    create_password_reset_token,
    reset_password,
)
from backend.services.email_service import send_password_reset_email

router = APIRouter()


class SignupRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=200)
    email: str | None = None


class LoginRequest(BaseModel):
    username: str
    password: str


class ForgotPasswordRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=254)


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., min_length=20)
    new_password: str = Field(..., min_length=8, max_length=200)


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


@router.post("/auth/forgot-password")
def forgot_password(data: ForgotPasswordRequest):
    email = data.email.strip().lower()
    token = create_password_reset_token(email)

    if token:
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173").rstrip("/")
        reset_url = f"{frontend_url}/reset-password?token={token}"

        try:
            send_password_reset_email(email, reset_url)
        except Exception as e:
            print(f"[password-reset] email delivery failed: {e}")

    return {
        "message": "If an account with that email exists, a password reset link has been sent."
    }


@router.post("/auth/reset-password")
def reset_password_endpoint(data: ResetPasswordRequest):
    try:
        success = reset_password(data.token, data.new_password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not success:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired password reset link.",
        )

    return {"message": "Password reset successfully. You can now log in."}


@router.get("/auth/me")
def me(current_user=Depends(get_current_user)):
    return current_user
